// Package chi_test contains functional tests for the chi HTTP router.
// These tests are organized into three groups:
//   - Spec Requirements: one test per testable specification section
//   - Fitness Scenarios: one test per QUALITY.md scenario (1:1 mapping)
//   - Boundaries and Edge Cases: one test per defensive pattern from Step 5
//
// Import pattern: external test package following Go conventions for tests
// outside the package root directory.
//
// Run with: go test -v ./quality/
// Or from quality/ directory: go test -v .
package chi_test

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	chi "github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

// ============================================================
// SPEC REQUIREMENTS
// One test per testable specification section from chi.go/README.
// ============================================================

// [Req: formal — chi.go Router interface]
// NewRouter returns a Mux implementing the Router interface.
func TestSpec_NewRouterImplementsRouterInterface(t *testing.T) {
	r := chi.NewRouter()
	if r == nil {
		t.Fatal("NewRouter() returned nil")
	}
	var _ chi.Router = r // compile-time assertion
}

// [Req: formal — chi.go: GET routing]
// r.Get(pattern, handlerFn) registers a handler that responds only to GET.
func TestSpec_GetRouteMatchesGet(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/ping", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(200)
		w.Write([]byte("pong"))
	})

	req := httptest.NewRequest("GET", "/ping", nil)
	rr := httptest.NewRecorder()
	r.ServeHTTP(rr, req)

	if rr.Code != 200 {
		t.Errorf("expected 200, got %d", rr.Code)
	}
	if rr.Body.String() != "pong" {
		t.Errorf("expected 'pong', got %q", rr.Body.String())
	}
}

// [Req: formal — chi.go: method routing]
// A GET route must not match POST requests — returns 405.
func TestSpec_GetRouteDoesNotMatchPost(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/ping", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(200)
	})

	req := httptest.NewRequest("POST", "/ping", nil)
	rr := httptest.NewRecorder()
	r.ServeHTTP(rr, req)

	if rr.Code != 405 {
		t.Errorf("expected 405, got %d", rr.Code)
	}
}

// [Req: formal — chi.go: URL parameters {name}]
// Simple named placeholder {name} matches any sequence of characters up to next /.
func TestSpec_URLParamSimpleNamedPlaceholder(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/user/{name}", func(w http.ResponseWriter, r *http.Request) {
		name := chi.URLParam(r, "name")
		w.Write([]byte(name))
	})

	req := httptest.NewRequest("GET", "/user/jsmith", nil)
	rr := httptest.NewRecorder()
	r.ServeHTTP(rr, req)

	if rr.Body.String() != "jsmith" {
		t.Errorf("expected 'jsmith', got %q", rr.Body.String())
	}
	// Must not match /user/jsmith/info (next segment present)
	req2 := httptest.NewRequest("GET", "/user/jsmith/info", nil)
	rr2 := httptest.NewRecorder()
	r.ServeHTTP(rr2, req2)
	if rr2.Code != 404 {
		t.Errorf("expected 404 for /user/jsmith/info, got %d", rr2.Code)
	}
}

// [Req: formal — chi.go: URL parameters with regexp {id:[0-9]+}]
// Regexp placeholder matches only strings conforming to the regexp.
func TestSpec_URLParamRegexpPlaceholder(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/article/{id:[0-9]+}", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte(chi.URLParam(r, "id")))
	})

	// Should match digits
	req := httptest.NewRequest("GET", "/article/42", nil)
	rr := httptest.NewRecorder()
	r.ServeHTTP(rr, req)
	if rr.Code != 200 || rr.Body.String() != "42" {
		t.Errorf("expected 200 with '42', got %d %q", rr.Code, rr.Body.String())
	}

	// Should not match non-digits
	req2 := httptest.NewRequest("GET", "/article/abc", nil)
	rr2 := httptest.NewRecorder()
	r.ServeHTTP(rr2, req2)
	if rr2.Code != 404 {
		t.Errorf("expected 404 for non-digit id, got %d", rr2.Code)
	}
}

// [Req: formal — chi.go: wildcard * matches rest of URL including /]
// /page/* matches /page/intro/latest (catches / characters).
func TestSpec_CatchAllWildcard(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/page/*", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("ok"))
	})

	for _, path := range []string{"/page/intro", "/page/intro/latest", "/page/a/b/c"} {
		req := httptest.NewRequest("GET", path, nil)
		rr := httptest.NewRecorder()
		r.ServeHTTP(rr, req)
		if rr.Code != 200 {
			t.Errorf("path %q: expected 200, got %d", path, rr.Code)
		}
	}
}

// [Req: formal — chi.go: Use() adds middleware to stack]
// Middleware registered with Use() runs for every matching route.
func TestSpec_UseAppliesMiddleware(t *testing.T) {
	var executed bool
	mw := func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			executed = true
			next.ServeHTTP(w, r)
		})
	}

	r := chi.NewRouter()
	r.Use(mw)
	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(200)
	})

	req := httptest.NewRequest("GET", "/", nil)
	rr := httptest.NewRecorder()
	r.ServeHTTP(rr, req)

	if !executed {
		t.Error("middleware was not executed")
	}
}

// [Req: formal — chi.go: With() adds inline middleware for a specific endpoint]
// Middleware added via With() applies only to that endpoint.
func TestSpec_WithAppliesInlineMiddleware(t *testing.T) {
	var inlineExecuted bool
	inlineMw := func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			inlineExecuted = true
			next.ServeHTTP(w, r)
		})
	}

	r := chi.NewRouter()
	r.With(inlineMw).Get("/protected", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(200)
	})
	r.Get("/open", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(200)
	})

	// inline middleware fires on /protected
	inlineExecuted = false
	r.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest("GET", "/protected", nil))
	if !inlineExecuted {
		t.Error("inline middleware not executed for /protected")
	}

	// inline middleware does NOT fire on /open
	inlineExecuted = false
	r.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest("GET", "/open", nil))
	if inlineExecuted {
		t.Error("inline middleware unexpectedly executed for /open")
	}
}

// [Req: formal — chi.go: Group() creates inline sub-router with fresh middleware stack]
func TestSpec_GroupMiddlewareIsolation(t *testing.T) {
	var groupMwExecuted bool
	groupMw := func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			groupMwExecuted = true
			next.ServeHTTP(w, r)
		})
	}

	r := chi.NewRouter()
	r.Group(func(sub chi.Router) {
		sub.Use(groupMw)
		sub.Get("/admin", func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(200) })
	})
	r.Get("/public", func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(200) })

	// Group middleware fires for /admin
	groupMwExecuted = false
	r.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest("GET", "/admin", nil))
	if !groupMwExecuted {
		t.Error("group middleware not executed for /admin")
	}

	// Group middleware does NOT fire for /public
	groupMwExecuted = false
	r.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest("GET", "/public", nil))
	if groupMwExecuted {
		t.Error("group middleware unexpectedly executed for /public")
	}
}

// [Req: formal — chi.go: NotFound sets custom 404 handler]
func TestSpec_CustomNotFoundHandler(t *testing.T) {
	r := chi.NewRouter()
	r.NotFound(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(404)
		w.Write([]byte("custom 404"))
	})
	r.Get("/exists", func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(200) })

	rr := httptest.NewRecorder()
	r.ServeHTTP(rr, httptest.NewRequest("GET", "/missing", nil))

	if rr.Code != 404 {
		t.Errorf("expected 404, got %d", rr.Code)
	}
	if rr.Body.String() != "custom 404" {
		t.Errorf("expected 'custom 404', got %q", rr.Body.String())
	}
}

// [Req: formal — chi.go: MethodNotAllowed sets custom 405 handler]
func TestSpec_CustomMethodNotAllowedHandler(t *testing.T) {
	r := chi.NewRouter()
	r.MethodNotAllowed(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(405)
		w.Write([]byte("custom 405"))
	})
	r.Get("/thing", func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(200) })

	rr := httptest.NewRecorder()
	r.ServeHTTP(rr, httptest.NewRequest("DELETE", "/thing", nil))

	if rr.Code != 405 {
		t.Errorf("expected 405, got %d", rr.Code)
	}
	if rr.Body.String() != "custom 405" {
		t.Errorf("expected 'custom 405', got %q", rr.Body.String())
	}
}

// [Req: formal — chi.go: Match() searches routing tree without executing handler]
func TestSpec_MatchWithoutExecuting(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/items/{id}", func(w http.ResponseWriter, r *http.Request) {})

	rctx := chi.NewRouteContext()
	if !r.Match(rctx, "GET", "/items/99") {
		t.Error("Match returned false for registered route")
	}

	rctx2 := chi.NewRouteContext()
	if r.Match(rctx2, "GET", "/nonexistent") {
		t.Error("Match returned true for unregistered route")
	}
}

// [Req: formal — chi.go: Route() mounts sub-router at pattern]
func TestSpec_RouteSubrouter(t *testing.T) {
	r := chi.NewRouter()
	r.Route("/api", func(sub chi.Router) {
		sub.Get("/users", func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("users"))
		})
	})

	rr := httptest.NewRecorder()
	r.ServeHTTP(rr, httptest.NewRequest("GET", "/api/users", nil))
	if rr.Code != 200 || rr.Body.String() != "users" {
		t.Errorf("expected 200 'users', got %d %q", rr.Code, rr.Body.String())
	}
}

// [Req: formal — chain.go: Chain builds middleware chain in correct order (outermost first)]
func TestSpec_ChainMiddlewareOrder(t *testing.T) {
	order := []string{}
	mw1 := func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			order = append(order, "mw1-before")
			next.ServeHTTP(w, r)
			order = append(order, "mw1-after")
		})
	}
	mw2 := func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			order = append(order, "mw2-before")
			next.ServeHTTP(w, r)
			order = append(order, "mw2-after")
		})
	}
	endpoint := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		order = append(order, "endpoint")
	})

	h := chi.Chain(mw1, mw2).Handler(endpoint)
	h.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest("GET", "/", nil))

	want := []string{"mw1-before", "mw2-before", "endpoint", "mw2-after", "mw1-after"}
	if len(order) != len(want) {
		t.Fatalf("expected %v, got %v", want, order)
	}
	for i, v := range want {
		if order[i] != v {
			t.Errorf("order[%d]: expected %q, got %q", i, v, order[i])
		}
	}
}

// [Req: formal — chi.go: Handle() matches all HTTP methods]
func TestSpec_HandleMatchesAllMethods(t *testing.T) {
	r := chi.NewRouter()
	r.Handle("/any", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(200)
	}))

	for _, method := range []string{"GET", "POST", "PUT", "DELETE", "PATCH"} {
		rr := httptest.NewRecorder()
		r.ServeHTTP(rr, httptest.NewRequest(method, "/any", nil))
		if rr.Code != 200 {
			t.Errorf("method %s: expected 200, got %d", method, rr.Code)
		}
	}
}

// ============================================================
// FITNESS SCENARIOS
// One test per QUALITY.md scenario (1:1 mapping).
// ============================================================

// [Req: inferred — from mux.go Use() guard at line 101]
// Scenario 1: Middleware Registered After Routes Causes Silent Panic
func TestScenario1_MiddlewareAfterRoutesPanics(t *testing.T) {
	// Use() before routes: must not panic
	func() {
		defer func() {
			if r := recover(); r != nil {
				t.Errorf("Use() before routes panicked unexpectedly: %v", r)
			}
		}()
		r := chi.NewRouter()
		r.Use(func(next http.Handler) http.Handler { return next })
		r.Get("/", func(w http.ResponseWriter, r *http.Request) {})
	}()

	// Use() after routes: must panic with specific message
	panicked := false
	func() {
		defer func() {
			if r := recover(); r != nil {
				msg := ""
				if s, ok := r.(string); ok {
					msg = s
				}
				if !strings.Contains(msg, "middlewares must be defined before routes") {
					t.Errorf("panic message unexpected: %q", msg)
				}
				panicked = true
			}
		}()
		r := chi.NewRouter()
		r.Get("/", func(w http.ResponseWriter, r *http.Request) {})
		r.Use(func(next http.Handler) http.Handler { return next }) // should panic
	}()
	if !panicked {
		t.Error("expected panic when Use() called after routes, but no panic occurred")
	}
}

// [Req: inferred — from mux.go ServeHTTP pool.Get/Reset/Put at lines 81–91]
// Scenario 2: sync.Pool RouteContext Reuse Corruption
// Tests exported fields only (unexported fields tested via the router indirectly).
func TestScenario2_RouteContextReset(t *testing.T) {
	x := chi.NewRouteContext()

	// Populate exported fields
	x.RoutePath = "/some/path"
	x.RouteMethod = "POST"
	x.RoutePatterns = []string{"/a", "/b"}
	x.URLParams.Add("key1", "val1")
	x.URLParams.Add("key2", "val2")

	x.Reset()

	if x.RoutePath != "" {
		t.Errorf("RoutePath not reset: %q", x.RoutePath)
	}
	if x.RouteMethod != "" {
		t.Errorf("RouteMethod not reset: %q", x.RouteMethod)
	}
	if len(x.RoutePatterns) != 0 {
		t.Errorf("RoutePatterns not reset: %v", x.RoutePatterns)
	}
	if len(x.URLParams.Keys) != 0 {
		t.Errorf("URLParams.Keys not reset: %v", x.URLParams.Keys)
	}
	if len(x.URLParams.Values) != 0 {
		t.Errorf("URLParams.Values not reset: %v", x.URLParams.Values)
	}
}

// [Req: inferred — from mux.go handle() guard at line 417]
// Scenario 3: Routing Pattern Must Begin With Slash
func TestScenario3_InvalidPatternPanic(t *testing.T) {
	for _, badPattern := range []string{"no-slash", "users/{id}", "api/v1"} {
		panicked := false
		func(pattern string) {
			defer func() {
				if r := recover(); r != nil {
					panicked = true
				}
			}()
			router := chi.NewRouter()
			router.Get(pattern, func(w http.ResponseWriter, r *http.Request) {})
		}(badPattern)
		if !panicked {
			t.Errorf("expected panic for pattern %q, but no panic occurred", badPattern)
		}
	}
}

// [Req: inferred — from mux.go Mount() nextRoutePath at lines 309–313]
// Scenario 4: Sub-Router Mount Path Stripping
func TestScenario4_MountPathStripping(t *testing.T) {
	sub := chi.NewRouter()
	sub.Get("/users/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		w.Write([]byte(id))
	})

	r := chi.NewRouter()
	r.Mount("/api", sub)

	rr := httptest.NewRecorder()
	r.ServeHTTP(rr, httptest.NewRequest("GET", "/api/users/42", nil))

	if rr.Code != 200 {
		t.Errorf("expected 200, got %d", rr.Code)
	}
	if rr.Body.String() != "42" {
		t.Errorf("expected '42', got %q", rr.Body.String())
	}
}

// [Req: inferred — from middleware/realip.go net.ParseIP guard at line 52]
// Scenario 5: RealIP Middleware IP Validation Bypass
func TestScenario5_RealIPValidation(t *testing.T) {
	originalAddr := "1.2.3.4:5678"

	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte(r.RemoteAddr))
	})
	wrapped := middleware.RealIP(handler)

	for _, hdr := range []struct {
		name  string
		value string
	}{
		{"X-Forwarded-For", "attacker@example.com"},
		{"X-Forwarded-For", "not-an-ip"},
		{"X-Real-IP", "256.256.256.256"},
		{"X-Real-IP", ";;;"},
		{"True-Client-IP", "192.168.1.0/24"}, // CIDR, not bare IP
	} {
		req := httptest.NewRequest("GET", "/", nil)
		req.RemoteAddr = originalAddr
		req.Header.Set(hdr.name, hdr.value)
		rr := httptest.NewRecorder()
		wrapped.ServeHTTP(rr, req)

		if rr.Body.String() != originalAddr {
			t.Errorf("header %s=%q: RemoteAddr was modified to %q (expected unchanged %q)",
				hdr.name, hdr.value, rr.Body.String(), originalAddr)
		}
	}
}

// [Req: inferred — from middleware/recoverer.go ErrAbortHandler special case at line 27]
// Scenario 6: Recoverer Must Re-Panic on ErrAbortHandler
func TestScenario6_RecovererRepanicOnErrAbortHandler(t *testing.T) {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		panic(http.ErrAbortHandler)
	})
	wrapped := middleware.Recoverer(handler)

	panicked := false
	var panicVal interface{}
	func() {
		defer func() {
			if r := recover(); r != nil {
				panicked = true
				panicVal = r
			}
		}()
		wrapped.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest("GET", "/", nil))
	}()

	if !panicked {
		t.Error("expected ErrAbortHandler to propagate through Recoverer, but no panic occurred")
	}
	if panicVal != http.ErrAbortHandler {
		t.Errorf("expected http.ErrAbortHandler, got %v", panicVal)
	}
}

// [Req: inferred — from middleware/timeout.go ctx.Err() guard at line 38]
// Scenario 7: Timeout Middleware Writes 504 Only on DeadlineExceeded
func TestScenario7_TimeoutOnly504OnDeadline(t *testing.T) {
	// Handler that takes longer than timeout
	slowHandler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		select {
		case <-r.Context().Done():
			return
		case <-time.After(500 * time.Millisecond):
			w.Write([]byte("done"))
		}
	})

	wrapped := middleware.Timeout(10 * time.Millisecond)(slowHandler)

	req := httptest.NewRequest("GET", "/", nil)
	rr := httptest.NewRecorder()
	wrapped.ServeHTTP(rr, req)

	// Should be 504 because context deadline was exceeded
	if rr.Code != 504 {
		t.Errorf("expected 504 for timed-out request, got %d", rr.Code)
	}
}

// [Req: inferred — from middleware/throttle.go panic guards at lines 45, 49]
// Scenario 8: Throttle Rejects Invalid Configuration at Startup
func TestScenario8_ThrottleInvalidConfig(t *testing.T) {
	// Limit < 1 must panic
	func() {
		defer func() {
			if r := recover(); r == nil {
				t.Error("expected panic for Throttle(0), got none")
			}
		}()
		middleware.Throttle(0)
	}()

	// Limit = -5 must panic
	func() {
		defer func() {
			if r := recover(); r == nil {
				t.Error("expected panic for Throttle(-5), got none")
			}
		}()
		middleware.Throttle(-5)
	}()

	// BacklogLimit < 0 must panic
	func() {
		defer func() {
			if r := recover(); r == nil {
				t.Error("expected panic for ThrottleBacklog(1, -1, ...), got none")
			}
		}()
		middleware.ThrottleBacklog(1, -1, time.Second)
	}()

	// Valid config must not panic
	func() {
		defer func() {
			if r := recover(); r != nil {
				t.Errorf("unexpected panic for valid ThrottleBacklog: %v", r)
			}
		}()
		middleware.ThrottleBacklog(2, 5, time.Second)
	}()
}

// [Req: inferred — from context.go URLParam backward search at line 101]
// Scenario 9: URLParam Returns Last Value for Duplicate Keys
func TestScenario9_URLParamLastValueWins(t *testing.T) {
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("id", "first")
	rctx.URLParams.Add("id", "second")

	val := rctx.URLParam("id")
	if val != "second" {
		t.Errorf("expected 'second' (last value wins), got %q", val)
	}
}

// [Req: inferred — from mux.go Mount() findPattern guard at lines 296–297]
// Scenario 10: Mount Panics on Duplicate Pattern
func TestScenario10_MountDuplicatePanic(t *testing.T) {
	panicked := false
	func() {
		defer func() {
			if r := recover(); r != nil {
				panicked = true
			}
		}()
		r := chi.NewRouter()
		sub1 := chi.NewRouter()
		sub2 := chi.NewRouter()
		r.Mount("/api", sub1)
		r.Mount("/api", sub2) // should panic
	}()
	if !panicked {
		t.Error("expected panic when mounting duplicate pattern, but no panic occurred")
	}
}

// ============================================================
// BOUNDARIES AND EDGE CASES
// One test per defensive pattern from Step 5.
// ============================================================

// [Req: inferred — from mux.go ServeHTTP nil handler check at line 65]
// Mux with no routes registered must serve 404 (not panic).
func TestBoundary_EmptyMuxServes404(t *testing.T) {
	r := chi.NewMux()
	rr := httptest.NewRecorder()
	r.ServeHTTP(rr, httptest.NewRequest("GET", "/anything", nil))
	if rr.Code != 404 {
		t.Errorf("expected 404 for empty mux, got %d", rr.Code)
	}
}

// [Req: inferred — from mux.go handle() pattern[0] != '/' check at line 417]
// Empty pattern must also panic.
func TestBoundary_EmptyPatternPanics(t *testing.T) {
	panicked := false
	func() {
		defer func() {
			if r := recover(); r != nil {
				panicked = true
			}
		}()
		r := chi.NewRouter()
		r.Get("", func(w http.ResponseWriter, r *http.Request) {})
	}()
	if !panicked {
		t.Error("expected panic for empty pattern")
	}
}

// [Req: inferred — from mux.go Mount() nil handler check at line 289]
// Mount with nil handler must panic.
func TestBoundary_MountNilHandlerPanics(t *testing.T) {
	panicked := false
	func() {
		defer func() {
			if r := recover(); r != nil {
				panicked = true
			}
		}()
		r := chi.NewRouter()
		r.Mount("/api", nil)
	}()
	if !panicked {
		t.Error("expected panic when mounting nil handler")
	}
}

// [Req: inferred — from mux.go Method() unsupported method check at line 128]
// Registering an unsupported HTTP method must panic.
func TestBoundary_UnsupportedMethodPanics(t *testing.T) {
	panicked := false
	func() {
		defer func() {
			if r := recover(); r != nil {
				panicked = true
			}
		}()
		r := chi.NewRouter()
		r.Method("INVALID_METHOD", "/", func(w http.ResponseWriter, r *http.Request) {})
	}()
	if !panicked {
		t.Error("expected panic for unsupported HTTP method")
	}
}

// [Req: inferred — from context.go RoutePattern() nil guard at line 123]
// RoutePattern on nil context must return "" not panic.
func TestBoundary_RoutePatternOnNilContext(t *testing.T) {
	var x *chi.Context
	result := x.RoutePattern()
	if result != "" {
		t.Errorf("expected '' from nil context RoutePattern(), got %q", result)
	}
}

// [Req: inferred — from context.go replaceWildcards iterative replacement at line 139]
// Consecutive wildcards in RoutePatterns must be collapsed correctly.
func TestBoundary_RoutePatternConsecutiveWildcards(t *testing.T) {
	x := chi.NewRouteContext()
	x.RoutePatterns = []string{"/api/", "*/", "*/", "users"}
	result := x.RoutePattern()
	if strings.Contains(result, "/*/") {
		t.Errorf("wildcard not fully replaced in RoutePattern: %q", result)
	}
}

// [Req: inferred — from middleware/realip.go valid IP passthrough]
// RealIP must set RemoteAddr when a valid IP is provided.
func TestBoundary_RealIPSetsValidIP(t *testing.T) {
	var gotAddr string
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotAddr = r.RemoteAddr
	})
	wrapped := middleware.RealIP(handler)

	req := httptest.NewRequest("GET", "/", nil)
	req.RemoteAddr = "1.2.3.4:9999"
	req.Header.Set("X-Real-IP", "203.0.113.1")
	wrapped.ServeHTTP(httptest.NewRecorder(), req)

	if !strings.HasPrefix(gotAddr, "203.0.113.1") {
		t.Errorf("expected RemoteAddr to start with '203.0.113.1', got %q", gotAddr)
	}
}

// [Req: inferred — from middleware/realip.go X-Forwarded-For first entry]
// RealIP must take only the first IP from a comma-separated X-Forwarded-For.
func TestBoundary_RealIPXForwardedForFirstEntry(t *testing.T) {
	var gotAddr string
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotAddr = r.RemoteAddr
	})
	wrapped := middleware.RealIP(handler)

	req := httptest.NewRequest("GET", "/", nil)
	req.RemoteAddr = "1.2.3.4:9999"
	req.Header.Set("X-Forwarded-For", "10.0.0.1, 10.0.0.2, 10.0.0.3")
	wrapped.ServeHTTP(httptest.NewRecorder(), req)

	if !strings.HasPrefix(gotAddr, "10.0.0.1") {
		t.Errorf("expected first IP '10.0.0.1', got %q", gotAddr)
	}
}

// [Req: inferred — from recoverer.go WebSocket upgrade check at line 39]
// Recoverer must not write status on WebSocket upgrade connections.
func TestBoundary_RecovererNoStatusOnWebSocketUpgrade(t *testing.T) {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		panic("test panic during upgrade")
	})
	wrapped := middleware.Recoverer(handler)

	req := httptest.NewRequest("GET", "/ws", nil)
	req.Header.Set("Connection", "Upgrade")
	rr := httptest.NewRecorder()
	wrapped.ServeHTTP(rr, req)

	// Code should remain 200 (default, no WriteHeader called by Recoverer)
	if rr.Code != 200 {
		t.Errorf("expected no status written for Upgrade connection, got %d", rr.Code)
	}
}

// [Req: inferred — from middleware/throttle.go capacity exceeded path]
// When throttle limit is exceeded, must return configured status code.
func TestBoundary_ThrottleCapacityExceeded(t *testing.T) {
	block := make(chan struct{})
	slow := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		<-block
		w.WriteHeader(200)
	})
	wrapped := middleware.Throttle(1)(slow)

	// First request: holds the slot
	go wrapped.ServeHTTP(httptest.NewRecorder(), httptest.NewRequest("GET", "/", nil))
	time.Sleep(10 * time.Millisecond) // give first request time to acquire slot

	// Second request: should be rejected
	rr := httptest.NewRecorder()
	wrapped.ServeHTTP(rr, httptest.NewRequest("GET", "/", nil))
	close(block)

	if rr.Code != http.StatusTooManyRequests {
		t.Errorf("expected 429 when throttle exceeded, got %d", rr.Code)
	}
}

// [Req: inferred — from middleware/content_type.go empty body bypass at line 28]
// AllowContentType must skip check when request body is empty (ContentLength == 0).
func TestBoundary_ContentTypeSkipForEmptyBody(t *testing.T) {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(200)
	})
	wrapped := middleware.AllowContentType("application/json")(handler)

	// Request with wrong content-type but empty body: must pass through
	req := httptest.NewRequest("POST", "/", nil)
	req.Header.Set("Content-Type", "text/plain")
	rr := httptest.NewRecorder()
	wrapped.ServeHTTP(rr, req)

	if rr.Code != 200 {
		t.Errorf("expected 200 for empty body with wrong content-type, got %d", rr.Code)
	}
}

// [Req: inferred — from middleware/content_type.go 415 on wrong type]
// AllowContentType must return 415 for non-empty body with disallowed type.
func TestBoundary_ContentTypeRejectsWrongType(t *testing.T) {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(200)
	})
	wrapped := middleware.AllowContentType("application/json")(handler)

	req := httptest.NewRequest("POST", "/", strings.NewReader("data"))
	req.Header.Set("Content-Type", "text/plain")
	rr := httptest.NewRecorder()
	wrapped.ServeHTTP(rr, req)

	if rr.Code != 415 {
		t.Errorf("expected 415 for non-empty body with wrong content-type, got %d", rr.Code)
	}
}

// [Req: inferred — from middleware/request_id.go hostname fallback at line 48]
// RequestID must generate a valid non-empty ID.
func TestBoundary_RequestIDAlwaysGenerated(t *testing.T) {
	var gotID string
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotID = middleware.GetReqID(r.Context())
	})
	wrapped := middleware.RequestID(handler)

	req := httptest.NewRequest("GET", "/", nil)
	wrapped.ServeHTTP(httptest.NewRecorder(), req)

	if gotID == "" {
		t.Error("expected non-empty request ID")
	}
}

// [Req: inferred — from middleware/request_id.go pass-through existing ID at line 71]
// RequestID must use the incoming X-Request-Id header if present.
func TestBoundary_RequestIDPassThroughExisting(t *testing.T) {
	var gotID string
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotID = middleware.GetReqID(r.Context())
	})
	wrapped := middleware.RequestID(handler)

	req := httptest.NewRequest("GET", "/", nil)
	req.Header.Set("X-Request-Id", "existing-id-123")
	wrapped.ServeHTTP(httptest.NewRecorder(), req)

	if gotID != "existing-id-123" {
		t.Errorf("expected 'existing-id-123', got %q", gotID)
	}
}

// [Req: inferred — from tree.go regexp.Compile error handling at line 257]
// Invalid regexp pattern in route must panic with message identifying the pattern.
func TestBoundary_InvalidRegexpPatternPanics(t *testing.T) {
	panicked := false
	func() {
		defer func() {
			if r := recover(); r != nil {
				panicked = true
			}
		}()
		router := chi.NewRouter()
		router.Get("/item/{id:[invalid}", func(w http.ResponseWriter, r *http.Request) {})
	}()
	if !panicked {
		t.Error("expected panic for invalid regexp route pattern")
	}
}

// [Req: inferred — from mux.go Route() nil function check]
// Route() with nil function must panic.
func TestBoundary_RouteNilFunctionPanics(t *testing.T) {
	panicked := false
	func() {
		defer func() {
			if r := recover(); r != nil {
				panicked = true
			}
		}()
		r := chi.NewRouter()
		r.Route("/api", nil)
	}()
	if !panicked {
		t.Error("expected panic for Route() with nil function")
	}
}

// [Req: inferred — from tree.go RegisterMethod silent noop for empty method at line 62]
// RegisterMethod with empty string must be a noop (no panic, no side effects).
func TestBoundary_RegisterMethodEmptyStringNoop(t *testing.T) {
	defer func() {
		if r := recover(); r != nil {
			t.Errorf("RegisterMethod('') panicked: %v", r)
		}
	}()
	chi.RegisterMethod("")
}

// [Req: inferred — from middleware/compress.go unsupported wildcard pattern at lines 70–78]
// NewCompressor with an unsupported wildcard (not ending in /*) must panic.
func TestBoundary_CompressorInvalidWildcardPanics(t *testing.T) {
	panicked := false
	func() {
		defer func() {
			if r := recover(); r != nil {
				panicked = true
			}
		}()
		middleware.NewCompressor(5, "text/*plain") // wildcard not at end
	}()
	if !panicked {
		t.Error("expected panic for invalid wildcard content-type in Compressor")
	}
}

// [Req: inferred — from middleware/compress.go valid wildcard pattern text/*]
// NewCompressor must accept valid wildcard patterns like "text/*".
func TestBoundary_CompressorValidWildcardAccepted(t *testing.T) {
	defer func() {
		if r := recover(); r != nil {
			t.Errorf("NewCompressor panicked for valid wildcard: %v", r)
		}
	}()
	middleware.NewCompressor(5, "text/*")
}

// [Req: inferred — from middleware/route_headers.go empty router bypass at line 80]
// RouteHeaders with no routes configured must pass request through unmodified.
func TestBoundary_RouteHeadersEmptyPassthrough(t *testing.T) {
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(200)
	})
	wrapped := middleware.RouteHeaders().Handler(handler)

	req := httptest.NewRequest("GET", "/", nil)
	rr := httptest.NewRecorder()
	wrapped.ServeHTTP(rr, req)

	if rr.Code != 200 {
		t.Errorf("expected 200 for empty RouteHeaders, got %d", rr.Code)
	}
}

// [Req: inferred — from context.go URLParam "" for missing key]
// URLParam returns "" for a key not in the param stack.
func TestBoundary_URLParamMissingKeyReturnsEmpty(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/test", func(w http.ResponseWriter, r *http.Request) {
		val := chi.URLParam(r, "nonexistent")
		if val != "" {
			w.WriteHeader(500)
			w.Write([]byte("unexpected: " + val))
			return
		}
		w.WriteHeader(200)
	})

	rr := httptest.NewRecorder()
	r.ServeHTTP(rr, httptest.NewRequest("GET", "/test", nil))
	if rr.Code != 200 {
		t.Errorf("expected 200, got %d: %s", rr.Code, rr.Body.String())
	}
}

// [Req: inferred — from mux.go notFoundHandler propagation in Mount at lines 302–308]
// Custom NotFound handler registered on parent must propagate to mounted sub-router.
func TestBoundary_NotFoundHandlerPropagatesOnMount(t *testing.T) {
	sub := chi.NewRouter()
	sub.Get("/known", func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(200) })

	parent := chi.NewRouter()
	parent.NotFound(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(404)
		w.Write([]byte("parent-404"))
	})
	parent.Mount("/sub", sub)

	rr := httptest.NewRecorder()
	parent.ServeHTTP(rr, httptest.NewRequest("GET", "/sub/unknown", nil))

	if rr.Code != 404 || rr.Body.String() != "parent-404" {
		t.Errorf("expected parent-404, got %d %q", rr.Code, rr.Body.String())
	}
}
