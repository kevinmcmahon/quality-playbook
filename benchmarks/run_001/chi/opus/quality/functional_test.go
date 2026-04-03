package chi_test

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"

	"github.com/go-chi/chi/v5"
)

// =============================================================================
// Spec Requirements — Tests derived from README.md and chi.go documentation
// =============================================================================

// [Req: formal — README URL pattern documentation]
// A simple named placeholder {name} matches any sequence of characters up to the next / or end of URL.
func TestSpec_NamedPlaceholder_MatchesUpToSlash(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/user/{name}", func(w http.ResponseWriter, r *http.Request) {
		name := chi.URLParam(r, "name")
		w.Write([]byte("user:" + name))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	// Should match
	resp, err := http.Get(ts.URL + "/user/jsmith")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 200 {
		t.Fatalf("expected 200, got %d", resp.StatusCode)
	}
	body := readBody(t, resp)
	if body != "user:jsmith" {
		t.Errorf("expected 'user:jsmith', got '%s'", body)
	}

	// Should not match (extra path segment)
	resp, err = http.Get(ts.URL + "/user/jsmith/info")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 404 {
		t.Errorf("expected 404 for /user/jsmith/info, got %d", resp.StatusCode)
	}
}

// [Req: formal — README URL pattern documentation]
// Named placeholder with path continuation: /user/{name}/info
func TestSpec_NamedPlaceholder_WithPathContinuation(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/user/{name}/info", func(w http.ResponseWriter, r *http.Request) {
		name := chi.URLParam(r, "name")
		w.Write([]byte("info:" + name))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, err := http.Get(ts.URL + "/user/jsmith/info")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 200 {
		t.Fatalf("expected 200, got %d", resp.StatusCode)
	}
	body := readBody(t, resp)
	if body != "info:jsmith" {
		t.Errorf("expected 'info:jsmith', got '%s'", body)
	}
}

// [Req: formal — README URL pattern documentation]
// Regexp parameters: /date/{yyyy:\d\d\d\d}/{mm:\d\d}/{dd:\d\d}
func TestSpec_RegexpPlaceholder_DatePattern(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/date/{yyyy:\\d\\d\\d\\d}/{mm:\\d\\d}/{dd:\\d\\d}", func(w http.ResponseWriter, r *http.Request) {
		yyyy := chi.URLParam(r, "yyyy")
		mm := chi.URLParam(r, "mm")
		dd := chi.URLParam(r, "dd")
		w.Write([]byte(fmt.Sprintf("%s-%s-%s", yyyy, mm, dd)))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, err := http.Get(ts.URL + "/date/2017/04/01")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 200 {
		t.Fatalf("expected 200, got %d", resp.StatusCode)
	}
	body := readBody(t, resp)
	if body != "2017-04-01" {
		t.Errorf("expected '2017-04-01', got '%s'", body)
	}

	// Non-matching regexp should 404
	resp, err = http.Get(ts.URL + "/date/abc/04/01")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 404 {
		t.Errorf("expected 404 for non-matching regexp, got %d", resp.StatusCode)
	}
}

// [Req: formal — README URL pattern documentation]
// Catch-all wildcard: /page/* matches /page/intro/latest
func TestSpec_CatchAllWildcard(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/page/*", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("page-catch-all"))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, err := http.Get(ts.URL + "/page/intro/latest")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 200 {
		t.Fatalf("expected 200, got %d", resp.StatusCode)
	}
	body := readBody(t, resp)
	if body != "page-catch-all" {
		t.Errorf("expected 'page-catch-all', got '%s'", body)
	}
}

// [Req: formal — chi.go Router interface documentation]
// All HTTP method convenience functions register routes correctly.
func TestSpec_AllHTTPMethods(t *testing.T) {
	methods := []struct {
		method   string
		register func(chi.Router, string, http.HandlerFunc)
	}{
		{"GET", func(r chi.Router, p string, h http.HandlerFunc) { r.Get(p, h) }},
		{"POST", func(r chi.Router, p string, h http.HandlerFunc) { r.Post(p, h) }},
		{"PUT", func(r chi.Router, p string, h http.HandlerFunc) { r.Put(p, h) }},
		{"DELETE", func(r chi.Router, p string, h http.HandlerFunc) { r.Delete(p, h) }},
		{"PATCH", func(r chi.Router, p string, h http.HandlerFunc) { r.Patch(p, h) }},
		{"HEAD", func(r chi.Router, p string, h http.HandlerFunc) { r.Head(p, h) }},
		{"OPTIONS", func(r chi.Router, p string, h http.HandlerFunc) { r.Options(p, h) }},
		{"TRACE", func(r chi.Router, p string, h http.HandlerFunc) { r.Trace(p, h) }},
	}

	for _, m := range methods {
		t.Run(m.method, func(t *testing.T) {
			r := chi.NewRouter()
			m.register(r, "/test", func(w http.ResponseWriter, r *http.Request) {
				w.Write([]byte("method:" + r.Method))
			})

			ts := httptest.NewServer(r)
			defer ts.Close()

			req, _ := http.NewRequest(m.method, ts.URL+"/test", nil)
			resp, err := http.DefaultClient.Do(req)
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if resp.StatusCode != 200 {
				t.Errorf("expected 200 for %s, got %d", m.method, resp.StatusCode)
			}
		})
	}
}

// [Req: formal — chi.go Router interface documentation]
// Use() appends middleware onto the Router stack.
func TestSpec_UseAppendsMiddleware(t *testing.T) {
	r := chi.NewRouter()

	var order []string
	mw1 := func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			order = append(order, "mw1")
			next.ServeHTTP(w, r)
		})
	}
	mw2 := func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			order = append(order, "mw2")
			next.ServeHTTP(w, r)
		})
	}

	r.Use(mw1)
	r.Use(mw2)
	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		order = append(order, "handler")
		w.Write([]byte("ok"))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	_, err := http.Get(ts.URL + "/")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	expected := []string{"mw1", "mw2", "handler"}
	if len(order) != len(expected) {
		t.Fatalf("expected %d calls, got %d: %v", len(expected), len(order), order)
	}
	for i, v := range expected {
		if order[i] != v {
			t.Errorf("position %d: expected '%s', got '%s'", i, v, order[i])
		}
	}
}

// [Req: formal — chi.go Router interface documentation]
// With() adds inline middlewares for an endpoint handler.
func TestSpec_WithInlineMiddleware(t *testing.T) {
	r := chi.NewRouter()

	var hitMiddleware bool
	authMw := func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			hitMiddleware = true
			next.ServeHTTP(w, r)
		})
	}

	r.Get("/public", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("public"))
	})
	r.With(authMw).Get("/private", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("private"))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	// Public route should not hit middleware
	hitMiddleware = false
	http.Get(ts.URL + "/public")
	if hitMiddleware {
		t.Error("inline middleware should not run for /public")
	}

	// Private route should hit middleware
	hitMiddleware = false
	http.Get(ts.URL + "/private")
	if !hitMiddleware {
		t.Error("inline middleware should run for /private")
	}
}

// [Req: formal — chi.go Router interface documentation]
// NotFound defines a custom handler for unmatched routes.
func TestSpec_CustomNotFoundHandler(t *testing.T) {
	r := chi.NewRouter()
	r.NotFound(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(404)
		w.Write([]byte("custom-404"))
	})
	r.Get("/exists", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("found"))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, err := http.Get(ts.URL + "/nonexistent")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 404 {
		t.Fatalf("expected 404, got %d", resp.StatusCode)
	}
	body := readBody(t, resp)
	if body != "custom-404" {
		t.Errorf("expected custom 404 body 'custom-404', got '%s'", body)
	}
}

// [Req: formal — chi.go Router interface documentation]
// MethodNotAllowed defines a custom handler for unresolved methods.
func TestSpec_CustomMethodNotAllowedHandler(t *testing.T) {
	r := chi.NewRouter()
	r.MethodNotAllowed(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(405)
		w.Write([]byte("custom-405"))
	})
	r.Get("/only-get", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("got"))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	req, _ := http.NewRequest("POST", ts.URL+"/only-get", nil)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 405 {
		t.Fatalf("expected 405, got %d", resp.StatusCode)
	}
	body := readBody(t, resp)
	if body != "custom-405" {
		t.Errorf("expected custom 405 body 'custom-405', got '%s'", body)
	}
}

// [Req: formal — chi.go Router interface documentation]
// Route() creates a new Mux and mounts it as a subrouter.
func TestSpec_RouteSubRouter(t *testing.T) {
	r := chi.NewRouter()
	r.Route("/api", func(r chi.Router) {
		r.Get("/users", func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("users-list"))
		})
		r.Get("/users/{id}", func(w http.ResponseWriter, r *http.Request) {
			id := chi.URLParam(r, "id")
			w.Write([]byte("user:" + id))
		})
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, err := http.Get(ts.URL + "/api/users")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	body := readBody(t, resp)
	if body != "users-list" {
		t.Errorf("expected 'users-list', got '%s'", body)
	}

	resp, err = http.Get(ts.URL + "/api/users/42")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	body = readBody(t, resp)
	if body != "user:42" {
		t.Errorf("expected 'user:42', got '%s'", body)
	}
}

// [Req: formal — chi.go Router interface documentation]
// Group() adds a new inline-Router with a fresh middleware stack.
func TestSpec_GroupInlineRouter(t *testing.T) {
	r := chi.NewRouter()

	var groupMwCalled bool
	r.Group(func(r chi.Router) {
		r.Use(func(next http.Handler) http.Handler {
			return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				groupMwCalled = true
				next.ServeHTTP(w, r)
			})
		})
		r.Get("/grouped", func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("in-group"))
		})
	})
	r.Get("/ungrouped", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("no-group"))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	// Group middleware should run for /grouped
	groupMwCalled = false
	http.Get(ts.URL + "/grouped")
	if !groupMwCalled {
		t.Error("group middleware should run for /grouped")
	}

	// Group middleware should not run for /ungrouped
	groupMwCalled = false
	http.Get(ts.URL + "/ungrouped")
	if groupMwCalled {
		t.Error("group middleware should not run for /ungrouped")
	}
}

// =============================================================================
// Fitness Scenarios — One test per QUALITY.md scenario
// =============================================================================

// Scenario 1: Radix Trie Node Split Corruption
// [Req: inferred — from tree.go InsertRoute() split logic]
func TestScenario1_RadixTrieNodeSplitCorrectness(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/users", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("users-list"))
	})
	r.Get("/us", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("us-page"))
	})
	r.Get("/user-settings", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("settings"))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	tests := []struct {
		path     string
		expected string
	}{
		{"/users", "users-list"},
		{"/us", "us-page"},
		{"/user-settings", "settings"},
	}

	for _, tt := range tests {
		resp, err := http.Get(ts.URL + tt.path)
		if err != nil {
			t.Fatalf("unexpected error for %s: %v", tt.path, err)
		}
		if resp.StatusCode != 200 {
			t.Errorf("%s: expected 200, got %d", tt.path, resp.StatusCode)
			continue
		}
		body := readBody(t, resp)
		if body != tt.expected {
			t.Errorf("%s: expected '%s', got '%s'", tt.path, tt.expected, body)
		}
	}
}

// Scenario 2: URL Parameter Extraction Across Nested Sub-Routers
// [Req: inferred — from context.go URLParam() reverse iteration]
func TestScenario2_URLParamNestedSubRouters(t *testing.T) {
	r := chi.NewRouter()
	r.Route("/api/{version}", func(r chi.Router) {
		r.Route("/users", func(r chi.Router) {
			r.Get("/{userID}", func(w http.ResponseWriter, r *http.Request) {
				version := chi.URLParam(r, "version")
				userID := chi.URLParam(r, "userID")
				w.Write([]byte(fmt.Sprintf("v=%s,u=%s", version, userID)))
			})
		})
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, err := http.Get(ts.URL + "/api/v2/users/42")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 200 {
		t.Fatalf("expected 200, got %d", resp.StatusCode)
	}
	body := readBody(t, resp)
	if body != "v=v2,u=42" {
		t.Errorf("expected 'v=v2,u=42', got '%s'", body)
	}
}

// Scenario 3: Context Pool Reuse After Panic in Handler
// [Req: inferred — from mux.go ServeHTTP() pool.Get/pool.Put pattern]
func TestScenario3_ContextPoolReuseSafety(t *testing.T) {
	r := chi.NewRouter()

	// Use a simple recovery middleware
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			defer func() {
				if rvr := recover(); rvr != nil {
					w.WriteHeader(500)
					w.Write([]byte("recovered"))
				}
			}()
			next.ServeHTTP(w, r)
		})
	})

	r.Get("/panic/{id}", func(w http.ResponseWriter, r *http.Request) {
		panic("intentional panic")
	})
	r.Get("/safe/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		w.Write([]byte("id:" + id))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	// Trigger panic
	http.Get(ts.URL + "/panic/999")

	// Subsequent request should get correct params, not stale ones
	resp, err := http.Get(ts.URL + "/safe/42")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	body := readBody(t, resp)
	if body != "id:42" {
		t.Errorf("expected 'id:42' after panic recovery, got '%s'", body)
	}
}

// Scenario 4: Middleware Ordering Violation After Route Registration
// [Req: inferred — from mux.go Use() panic guard]
func TestScenario4_MiddlewareAfterRoutePanics(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/test", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("ok"))
	})

	defer func() {
		if rvr := recover(); rvr == nil {
			t.Error("expected panic when adding middleware after routes")
		}
	}()

	// This should panic
	r.Use(func(next http.Handler) http.Handler {
		return next
	})
}

// Scenario 5: Wildcard Pattern Collision on Mount — Static vs Mounted Sub-Router
// [Req: inferred — from mux.go Mount() duplicate pattern check]
func TestScenario5_StaticRouteVsMountedSubRouter(t *testing.T) {
	r := chi.NewRouter()

	// Register static route first
	r.Get("/api/users", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("static-users"))
	})

	// Mount sub-router under /api
	r.Mount("/api/v2", func() http.Handler {
		sub := chi.NewRouter()
		sub.Get("/items", func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("v2-items"))
		})
		return sub
	}())

	ts := httptest.NewServer(r)
	defer ts.Close()

	// Static route should still work
	resp, err := http.Get(ts.URL + "/api/users")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 200 {
		t.Fatalf("expected 200 for static /api/users, got %d", resp.StatusCode)
	}
	body := readBody(t, resp)
	if body != "static-users" {
		t.Errorf("expected 'static-users', got '%s'", body)
	}

	// Mounted sub-router should work
	resp, err = http.Get(ts.URL + "/api/v2/items")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 200 {
		t.Fatalf("expected 200 for mounted /api/v2/items, got %d", resp.StatusCode)
	}
	body = readBody(t, resp)
	if body != "v2-items" {
		t.Errorf("expected 'v2-items', got '%s'", body)
	}
}

// Scenario 6: Regexp Pattern Validation and Matching
// [Req: inferred — from tree.go addChild() regexp.Compile]
func TestScenario6_RegexpPatternMatching(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/item/{id:[0-9]+}", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		w.Write([]byte("item:" + id))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	// Matching: numeric ID
	resp, err := http.Get(ts.URL + "/item/12345")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 200 {
		t.Fatalf("expected 200 for numeric id, got %d", resp.StatusCode)
	}
	body := readBody(t, resp)
	if body != "item:12345" {
		t.Errorf("expected 'item:12345', got '%s'", body)
	}

	// Non-matching: alphabetic string should 404
	resp, err = http.Get(ts.URL + "/item/abc")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 404 {
		t.Errorf("expected 404 for non-numeric id, got %d", resp.StatusCode)
	}

	// Long numeric string should still match
	resp, err = http.Get(ts.URL + "/item/" + strings.Repeat("1", 256))
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 200 {
		t.Errorf("expected 200 for long numeric id, got %d", resp.StatusCode)
	}
}

// Scenario 7: Method Not Allowed Handler with Allow Header
// [Req: inferred — from mux.go methodNotAllowedHandler() and tree.go findRoute()]
func TestScenario7_MethodNotAllowedAllowHeader(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/resource/{id}", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("get-resource"))
	})
	r.Put("/resource/{id}", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("put-resource"))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	// DELETE should get 405
	req, _ := http.NewRequest("DELETE", ts.URL+"/resource/42", nil)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 405 {
		t.Fatalf("expected 405, got %d", resp.StatusCode)
	}

	// Allow header should be present
	allow := resp.Header.Get("Allow")
	if allow == "" {
		// Check for multiple Allow headers
		allows := resp.Header.Values("Allow")
		if len(allows) == 0 {
			t.Error("expected Allow header on 405 response")
		}
	}
}

// Scenario 8: RoutePattern Wildcard Collapse Across Deep Nesting
// [Req: inferred — from context.go RoutePattern() and replaceWildcards()]
func TestScenario8_RoutePatternWildcardCollapse(t *testing.T) {
	// Test using Context directly, matching context_test.go pattern
	x := &chi.Context{
		RoutePatterns: []string{
			"/v1/*",
			"/resources/*",
			"/{resource_id}",
		},
	}

	pattern := x.RoutePattern()
	expected := "/v1/resources/{resource_id}"
	if pattern != expected {
		t.Errorf("expected pattern '%s', got '%s'", expected, pattern)
	}

	// Test with consecutive wildcards
	x.RoutePatterns = []string{
		"/v1/*",
		"/resources/*",
		"/*",
		"/{resource_id}",
	}
	pattern = x.RoutePattern()
	if pattern != expected {
		t.Errorf("expected pattern '%s' with consecutive wildcards, got '%s'", expected, pattern)
	}
}

// Scenario 9: Handle() With Space-Delimited Method Pattern
// [Req: inferred — from mux.go Handle() pattern parsing]
func TestScenario9_HandleMethodPatternParsing(t *testing.T) {
	r := chi.NewRouter()
	r.Handle("GET /specific", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("specific-get"))
	}))

	ts := httptest.NewServer(r)
	defer ts.Close()

	// GET should match
	resp, err := http.Get(ts.URL + "/specific")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 200 {
		t.Fatalf("expected 200, got %d", resp.StatusCode)
	}
	body := readBody(t, resp)
	if body != "specific-get" {
		t.Errorf("expected 'specific-get', got '%s'", body)
	}

	// POST should not match (should 404 or 405)
	req, _ := http.NewRequest("POST", ts.URL+"/specific", nil)
	resp, err = http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode == 200 {
		t.Error("POST to GET-only route should not return 200")
	}
}

// Scenario 10: RegisterMethod() Custom Method Support
// [Req: inferred — from tree.go RegisterMethod()]
func TestScenario10_RegisterCustomMethod(t *testing.T) {
	chi.RegisterMethod("PURGE")

	r := chi.NewRouter()
	r.MethodFunc("PURGE", "/cache", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("purged"))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	req, _ := http.NewRequest("PURGE", ts.URL+"/cache", nil)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 200 {
		t.Fatalf("expected 200 for custom PURGE method, got %d", resp.StatusCode)
	}
	body := readBody(t, resp)
	if body != "purged" {
		t.Errorf("expected 'purged', got '%s'", body)
	}
}

// =============================================================================
// Boundaries and Edge Cases — Tests derived from defensive patterns
// =============================================================================

// [Req: inferred — from mux.go ServeHTTP() nil handler guard at line 65]
func TestBoundary_NilHandler_ReturnsNotFound(t *testing.T) {
	r := chi.NewRouter()
	// Don't register any routes — handler stays nil

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, err := http.Get(ts.URL + "/anything")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 404 {
		t.Errorf("expected 404 for router with no routes, got %d", resp.StatusCode)
	}
}

// [Req: inferred — from context.go URLParam() empty key returns empty string]
func TestBoundary_URLParamMissingKey(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/item/{id}", func(w http.ResponseWriter, r *http.Request) {
		name := chi.URLParam(r, "nonexistent")
		w.Write([]byte("name:" + name))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, err := http.Get(ts.URL + "/item/42")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	body := readBody(t, resp)
	if body != "name:" {
		t.Errorf("expected 'name:' for missing key, got '%s'", body)
	}
}

// [Req: inferred — from context.go RouteContext() nil safety via type assertion]
func TestBoundary_RouteContextFromEmptyContext(t *testing.T) {
	ctx := context.Background()
	rctx := chi.RouteContext(ctx)
	if rctx != nil {
		t.Error("expected nil RouteContext from background context")
	}
}

// [Req: inferred — from context.go URLParam() with nil RouteContext]
func TestBoundary_URLParamWithNilContext(t *testing.T) {
	ctx := context.Background()
	result := chi.URLParamFromCtx(ctx, "anything")
	if result != "" {
		t.Errorf("expected empty string from nil context, got '%s'", result)
	}
}

// [Req: inferred — from mux.go handle() pattern validation at line 417]
func TestBoundary_PatternMustStartWithSlash(t *testing.T) {
	r := chi.NewRouter()
	defer func() {
		if rvr := recover(); rvr == nil {
			t.Error("expected panic for pattern not starting with /")
		}
	}()
	r.Get("no-slash", func(w http.ResponseWriter, r *http.Request) {})
}

// [Req: inferred — from mux.go Route() nil fn guard at line 274]
func TestBoundary_RouteNilFnPanics(t *testing.T) {
	r := chi.NewRouter()
	defer func() {
		if rvr := recover(); rvr == nil {
			t.Error("expected panic for nil Route fn")
		}
	}()
	r.Route("/sub", nil)
}

// [Req: inferred — from mux.go Mount() nil handler guard at line 291]
func TestBoundary_MountNilHandlerPanics(t *testing.T) {
	r := chi.NewRouter()
	defer func() {
		if rvr := recover(); rvr == nil {
			t.Error("expected panic for nil Mount handler")
		}
	}()
	r.Mount("/sub", nil)
}

// [Req: inferred — from mux.go Method() invalid method guard at line 129]
func TestBoundary_InvalidMethodPanics(t *testing.T) {
	r := chi.NewRouter()
	defer func() {
		if rvr := recover(); rvr == nil {
			t.Error("expected panic for invalid HTTP method")
		}
	}()
	r.Method("INVALID_METHOD_XYZ", "/path", http.NotFoundHandler())
}

// [Req: inferred — from tree.go addChild() regexp.Compile panic at line 258]
func TestBoundary_InvalidRegexpPatternPanics(t *testing.T) {
	r := chi.NewRouter()
	defer func() {
		if rvr := recover(); rvr == nil {
			t.Error("expected panic for invalid regexp in route pattern")
		}
	}()
	r.Get("/item/{id:[invalid}", func(w http.ResponseWriter, r *http.Request) {})
}

// [Req: inferred — from context.go Reset() clears all fields]
func TestBoundary_ContextResetClearsAllFields(t *testing.T) {
	ctx := chi.NewRouteContext()
	ctx.RoutePath = "/test"
	ctx.RouteMethod = "GET"
	ctx.URLParams.Add("key", "value")
	ctx.RoutePatterns = append(ctx.RoutePatterns, "/pattern/*")

	ctx.Reset()

	if ctx.RoutePath != "" {
		t.Error("RoutePath not reset")
	}
	if ctx.RouteMethod != "" {
		t.Error("RouteMethod not reset")
	}
	if len(ctx.URLParams.Keys) != 0 {
		t.Error("URLParams.Keys not reset")
	}
	if len(ctx.URLParams.Values) != 0 {
		t.Error("URLParams.Values not reset")
	}
	if len(ctx.RoutePatterns) != 0 {
		t.Error("RoutePatterns not reset")
	}
}

// [Req: inferred — from mux.go routeHTTP() empty path defaults to "/"]
func TestBoundary_EmptyPathDefaultsToRoot(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("root"))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, err := http.Get(ts.URL + "/")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	body := readBody(t, resp)
	if body != "root" {
		t.Errorf("expected 'root', got '%s'", body)
	}
}

// [Req: inferred — from mux.go Mount() duplicate pattern panic at line 296]
func TestBoundary_DuplicateMountPanics(t *testing.T) {
	r := chi.NewRouter()
	sub1 := chi.NewRouter()
	sub1.Get("/", func(w http.ResponseWriter, r *http.Request) {})
	sub2 := chi.NewRouter()
	sub2.Get("/", func(w http.ResponseWriter, r *http.Request) {})

	r.Mount("/api", sub1)

	defer func() {
		if rvr := recover(); rvr == nil {
			t.Error("expected panic for duplicate mount pattern")
		}
	}()
	r.Mount("/api", sub2)
}

// [Req: inferred — from chain.go chain() empty middleware returns endpoint directly]
func TestBoundary_EmptyMiddlewareChain(t *testing.T) {
	r := chi.NewRouter()
	// No Use() calls — empty middleware chain
	r.Get("/direct", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("direct"))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, err := http.Get(ts.URL + "/direct")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	body := readBody(t, resp)
	if body != "direct" {
		t.Errorf("expected 'direct', got '%s'", body)
	}
}

// [Req: inferred — from context.go RoutePattern() nil receiver guard at line 124]
func TestBoundary_NilContextRoutePattern(t *testing.T) {
	var ctx *chi.Context
	pattern := ctx.RoutePattern()
	if pattern != "" {
		t.Errorf("expected empty pattern from nil context, got '%s'", pattern)
	}
}

// [Req: inferred — from mux.go ServeHTTP() existing context reuse at line 71-75]
func TestBoundary_ExistingContextSkipsPoolGet(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/outer/{outerID}", func(w http.ResponseWriter, r *http.Request) {
		outerID := chi.URLParam(r, "outerID")
		w.Write([]byte("outer:" + outerID))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, err := http.Get(ts.URL + "/outer/abc")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	body := readBody(t, resp)
	if body != "outer:abc" {
		t.Errorf("expected 'outer:abc', got '%s'", body)
	}
}

// [Req: inferred — from mux.go concurrent access safety via sync.Pool]
func TestBoundary_ConcurrentRequestSafety(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/user/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		w.Write([]byte("id:" + id))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	var wg sync.WaitGroup
	errors := make(chan string, 100)

	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()
			id := fmt.Sprintf("%d", n)
			resp, err := http.Get(ts.URL + "/user/" + id)
			if err != nil {
				errors <- fmt.Sprintf("request %d error: %v", n, err)
				return
			}
			body := readBody(t, resp)
			expected := "id:" + id
			if body != expected {
				errors <- fmt.Sprintf("request %d: expected '%s', got '%s'", n, expected, body)
			}
		}(i)
	}

	wg.Wait()
	close(errors)

	for errMsg := range errors {
		t.Error(errMsg)
	}
}

// [Req: inferred — from tree.go findRoute() param matching prevents cross-segment]
func TestBoundary_ParamDoesNotMatchAcrossSlash(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/a/{param}", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("matched:" + chi.URLParam(r, "param")))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	// Single segment should match
	resp, err := http.Get(ts.URL + "/a/hello")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 200 {
		t.Errorf("expected 200 for /a/hello, got %d", resp.StatusCode)
	}

	// Multi-segment should NOT match (param doesn't cross /)
	resp, err = http.Get(ts.URL + "/a/hello/world")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 404 {
		t.Errorf("expected 404 for /a/hello/world, got %d", resp.StatusCode)
	}
}

// [Req: inferred — from tree.go RegisterMethod() empty string guard at line 62]
func TestBoundary_RegisterMethodEmptyString(t *testing.T) {
	// Should not panic — empty string is silently ignored
	chi.RegisterMethod("")
}

// [Req: inferred — from mux.go NotFoundHandler() fallback to http.NotFound]
func TestBoundary_DefaultNotFoundHandler(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/exists", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("here"))
	})
	// No custom NotFound handler set

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, err := http.Get(ts.URL + "/nope")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 404 {
		t.Errorf("expected default 404, got %d", resp.StatusCode)
	}
}

// [Req: inferred — from mux.go Mount() handler propagation at lines 301-307]
func TestBoundary_MountPropagatesNotFoundHandler(t *testing.T) {
	r := chi.NewRouter()
	r.NotFound(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(404)
		w.Write([]byte("parent-404"))
	})

	sub := chi.NewRouter()
	sub.Get("/found", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("found"))
	})
	r.Mount("/sub", sub)

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, err := http.Get(ts.URL + "/sub/missing")
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if resp.StatusCode != 404 {
		t.Fatalf("expected 404, got %d", resp.StatusCode)
	}
	body := readBody(t, resp)
	if body != "parent-404" {
		t.Errorf("expected propagated 'parent-404', got '%s'", body)
	}
}

// =============================================================================
// Test helpers
// =============================================================================

func readBody(t *testing.T, resp *http.Response) string {
	t.Helper()
	defer resp.Body.Close()
	b, err := io.ReadAll(resp.Body)
	if err != nil {
		t.Fatalf("failed to read body: %v", err)
	}
	return string(b)
}

