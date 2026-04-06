// Package chi_quality_tests contains functional tests for github.com/go-chi/chi/v5.
//
// Tests are organized into three groups:
//   - Spec Requirements: one test per testable requirement from the README and chi.go interface docs
//   - Fitness Scenarios: one test per QUALITY.md scenario (1:1 mapping)
//   - Boundaries and Edge Cases: one test per defensive pattern from Step 5 exploration
//
// Run with: go test -v ./... from the quality/ directory
// (requires Go 1.23+; replace directive in go.mod points to local chi repo)
package chi_quality_tests

import (
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	chi "github.com/go-chi/chi/v5"
)

// mustPanic asserts that fn() panics, and optionally that the panic message
// contains wantMsg. Returns the recovered value for additional assertions.
func mustPanic(t *testing.T, wantMsg string, fn func()) {
	t.Helper()
	defer func() {
		r := recover()
		if r == nil {
			t.Fatalf("expected panic, but function did not panic")
		}
		if wantMsg != "" {
			msg := fmt.Sprintf("%v", r)
			if !strings.Contains(msg, wantMsg) {
				t.Fatalf("panic message %q does not contain %q", msg, wantMsg)
			}
		}
	}()
	fn()
}

// makeRequest sends a test HTTP request through the given handler and returns the recorder.
func makeRequest(t *testing.T, h http.Handler, method, path string) *httptest.ResponseRecorder {
	t.Helper()
	req := httptest.NewRequest(method, path, nil)
	w := httptest.NewRecorder()
	h.ServeHTTP(w, req)
	return w
}

// bodyString reads and returns the response body as a string.
func bodyString(t *testing.T, w *httptest.ResponseRecorder) string {
	t.Helper()
	body, err := io.ReadAll(w.Body)
	if err != nil {
		t.Fatalf("reading body: %v", err)
	}
	return string(body)
}

// =============================================================================
// Group 1: Spec Requirements
// One test per testable requirement from the README and chi.go interface docs.
// =============================================================================

// TestSpec_NewRouter_IsFunctionalMux verifies NewRouter() returns a working mux that
// implements http.Handler. [Req: formal — README "As easy as:" example]
func TestSpec_NewRouter_IsFunctionalMux(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("welcome"))
	})
	w := makeRequest(t, r, "GET", "/")
	if w.Code != 200 {
		t.Fatalf("expected 200, got %d", w.Code)
	}
	if body := bodyString(t, w); body != "welcome" {
		t.Fatalf("expected body 'welcome', got %q", body)
	}
}

// TestSpec_NamedParam_MatchesPathSegment verifies that {name} matches any sequence
// of characters up to the next slash. [Req: formal — chi.go package doc]
func TestSpec_NamedParam_MatchesPathSegment(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/user/{name}", func(w http.ResponseWriter, r *http.Request) {
		name := chi.URLParam(r, "name")
		w.Write([]byte("user:" + name))
	})

	cases := []struct {
		path string
		want string
	}{
		{"/user/jsmith", "user:jsmith"},
		{"/user/alice", "user:alice"},
		{"/user/123", "user:123"},
	}
	for _, tc := range cases {
		w := makeRequest(t, r, "GET", tc.path)
		if w.Code != 200 {
			t.Errorf("path %s: expected 200, got %d", tc.path, w.Code)
		}
		if body := bodyString(t, w); body != tc.want {
			t.Errorf("path %s: expected %q, got %q", tc.path, tc.want, body)
		}
	}
}

// TestSpec_NamedParam_DoesNotMatchSlash verifies that a named param {name} does NOT
// match a path containing a slash. [Req: formal — chi.go: "/user/{name} matches /user/jsmith
// but not /user/jsmith/info"]
func TestSpec_NamedParam_DoesNotMatchSlash(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/user/{name}", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("matched"))
	})
	w := makeRequest(t, r, "GET", "/user/jsmith/info")
	if w.Code != 404 {
		t.Fatalf("/user/jsmith/info: expected 404, got %d", w.Code)
	}
}

// TestSpec_Wildcard_MatchesRestOfPath verifies that * matches the rest of the URL
// including slashes. [Req: formal — chi.go: "/page/* matches /page/intro/latest"]
func TestSpec_Wildcard_MatchesRestOfPath(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/page/*", func(w http.ResponseWriter, r *http.Request) {
		wild := chi.URLParam(r, "*")
		w.Write([]byte("wild:" + wild))
	})

	cases := []struct {
		path string
		want string
	}{
		{"/page/intro/latest", "wild:intro/latest"},
		{"/page/a/b/c/d", "wild:a/b/c/d"},
		{"/page/", "wild:"},
	}
	for _, tc := range cases {
		w := makeRequest(t, r, "GET", tc.path)
		if w.Code != 200 {
			t.Errorf("path %s: expected 200, got %d", tc.path, w.Code)
		}
		if body := bodyString(t, w); body != tc.want {
			t.Errorf("path %s: expected %q, got %q", tc.path, tc.want, body)
		}
	}
}

// TestSpec_RegexpParam_MatchesPattern verifies that {key:regexp} matches only
// paths satisfying the regexp. [Req: formal — chi.go regexp syntax description]
func TestSpec_RegexpParam_MatchesPattern(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/date/{yyyy:\\d\\d\\d\\d}/{mm:\\d\\d}/{dd:\\d\\d}", func(w http.ResponseWriter, r *http.Request) {
		yyyy := chi.URLParam(r, "yyyy")
		mm := chi.URLParam(r, "mm")
		dd := chi.URLParam(r, "dd")
		w.Write([]byte(yyyy + "-" + mm + "-" + dd))
	})

	w := makeRequest(t, r, "GET", "/date/2017/04/01")
	if w.Code != 200 {
		t.Fatalf("expected 200, got %d", w.Code)
	}
	if body := bodyString(t, w); body != "2017-04-01" {
		t.Fatalf("expected '2017-04-01', got %q", body)
	}
}

// TestSpec_RegexpParam_RejectsNonMatch verifies that a regexp param rejects
// values not matching the pattern. [Req: formal — chi.go regexp syntax description]
func TestSpec_RegexpParam_RejectsNonMatch(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/item/{id:\\d+}", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("ok"))
	})
	// "abc" does not match \d+
	w := makeRequest(t, r, "GET", "/item/abc")
	if w.Code != 404 {
		t.Fatalf("expected 404 for non-matching regexp, got %d", w.Code)
	}
}

// TestSpec_HTTPMethodRouting verifies that method-specific routes (GET, POST, PUT,
// DELETE, PATCH) are dispatched correctly. [Req: formal — Router interface in chi.go]
func TestSpec_HTTPMethodRouting(t *testing.T) {
	r := chi.NewRouter()
	methods := []string{"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
	for _, m := range methods {
		method := m // capture
		r.Method(method, "/resource", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte(method))
		}))
	}

	for _, m := range methods {
		w := makeRequest(t, r, m, "/resource")
		if w.Code != 200 {
			t.Errorf("method %s: expected 200, got %d", m, w.Code)
		}
		if m != "HEAD" { // HEAD has no body by convention
			if body := bodyString(t, w); body != m {
				t.Errorf("method %s: expected body %q, got %q", m, m, body)
			}
		}
	}
}

// TestSpec_Default404 verifies that an unregistered route returns 404. [Req: formal — README]
func TestSpec_Default404(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/exists", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("ok"))
	})
	w := makeRequest(t, r, "GET", "/does-not-exist")
	if w.Code != 404 {
		t.Fatalf("expected 404, got %d", w.Code)
	}
}

// TestSpec_Default405_WithAllowHeader verifies that a registered path accessed with
// an unregistered method returns 405 with an Allow header. [Req: formal — RFC 9110 §15.5.5,
// enforced by chi mux.go methodNotAllowedHandler]
func TestSpec_Default405_WithAllowHeader(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/items", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("ok"))
	})
	w := makeRequest(t, r, "DELETE", "/items")
	if w.Code != 405 {
		t.Fatalf("expected 405, got %d", w.Code)
	}
	allow := w.Header().Get("Allow")
	if allow == "" {
		t.Fatal("expected non-empty Allow header on 405 response")
	}
	if !strings.Contains(allow, "GET") {
		t.Fatalf("Allow header %q should contain GET", allow)
	}
}

// TestSpec_CustomNotFound verifies that a custom NotFound handler is used for 404s.
// [Req: formal — Router.NotFound() in chi.go]
func TestSpec_CustomNotFound(t *testing.T) {
	r := chi.NewRouter()
	r.NotFound(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(404)
		w.Write([]byte("custom-not-found"))
	})
	w := makeRequest(t, r, "GET", "/nope")
	if w.Code != 404 {
		t.Fatalf("expected 404, got %d", w.Code)
	}
	if body := bodyString(t, w); body != "custom-not-found" {
		t.Fatalf("expected 'custom-not-found', got %q", body)
	}
}

// TestSpec_CustomMethodNotAllowed verifies that a custom MethodNotAllowed handler is used.
// [Req: formal — Router.MethodNotAllowed() in chi.go]
func TestSpec_CustomMethodNotAllowed(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/exists", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("ok"))
	})
	r.MethodNotAllowed(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(405)
		w.Write([]byte("custom-not-allowed"))
	})
	w := makeRequest(t, r, "POST", "/exists")
	if w.Code != 405 {
		t.Fatalf("expected 405, got %d", w.Code)
	}
	if body := bodyString(t, w); body != "custom-not-allowed" {
		t.Fatalf("expected 'custom-not-allowed', got %q", body)
	}
}

// TestSpec_URLParam_ReturnsValue verifies that chi.URLParam retrieves the correct
// value from the request context. [Req: formal — README URL parameters section]
func TestSpec_URLParam_ReturnsValue(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/users/{userID}", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "userID")
		w.Write([]byte(id))
	})
	w := makeRequest(t, r, "GET", "/users/42")
	if w.Code != 200 {
		t.Fatalf("expected 200, got %d", w.Code)
	}
	if body := bodyString(t, w); body != "42" {
		t.Fatalf("expected '42', got %q", body)
	}
}

// TestSpec_Mount_AttachesSubrouter verifies that Mount() attaches a subrouter and
// routes through it correctly. [Req: formal — README subrouters / Mount section]
func TestSpec_Mount_AttachesSubrouter(t *testing.T) {
	sub := chi.NewRouter()
	sub.Get("/status", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("admin-status"))
	})

	r := chi.NewRouter()
	r.Mount("/admin", sub)

	w := makeRequest(t, r, "GET", "/admin/status")
	if w.Code != 200 {
		t.Fatalf("expected 200, got %d", w.Code)
	}
	if body := bodyString(t, w); body != "admin-status" {
		t.Fatalf("expected 'admin-status', got %q", body)
	}
}

// TestSpec_Use_MiddlewareAppliedToAllRoutes verifies that middleware registered via
// Use() is applied to all routes on the mux. [Req: formal — README middleware section]
func TestSpec_Use_MiddlewareAppliedToAllRoutes(t *testing.T) {
	var called []string
	trackMW := func(name string) func(http.Handler) http.Handler {
		return func(next http.Handler) http.Handler {
			return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				called = append(called, name)
				next.ServeHTTP(w, r)
			})
		}
	}

	r := chi.NewRouter()
	r.Use(trackMW("mw1"))
	r.Use(trackMW("mw2"))
	r.Get("/a", func(w http.ResponseWriter, r *http.Request) { w.Write([]byte("a")) })
	r.Get("/b", func(w http.ResponseWriter, r *http.Request) { w.Write([]byte("b")) })

	called = nil
	makeRequest(t, r, "GET", "/a")
	if len(called) != 2 || called[0] != "mw1" || called[1] != "mw2" {
		t.Fatalf("expected [mw1 mw2], got %v", called)
	}

	called = nil
	makeRequest(t, r, "GET", "/b")
	if len(called) != 2 || called[0] != "mw1" || called[1] != "mw2" {
		t.Fatalf("expected [mw1 mw2] for /b, got %v", called)
	}
}

// =============================================================================
// Group 2: Fitness Scenarios
// One test per QUALITY.md scenario (1:1 mapping).
// =============================================================================

// TestScenario1_MiddlewareAfterRoutePanics verifies that calling Use() after the
// first route registration panics immediately.
// [Req: inferred — mux.go:102 panic guard]
func TestScenario1_MiddlewareAfterRoutePanics(t *testing.T) {
	mustPanic(t, "all middlewares must be defined before routes on a mux", func() {
		r := chi.NewRouter()
		r.Get("/hello", func(w http.ResponseWriter, r *http.Request) {})
		r.Use(func(next http.Handler) http.Handler { return next }) // too late
	})
}

// TestScenario2_WildcardNotLastPanics verifies that a wildcard * not at the final
// position causes a panic at route registration time.
// [Req: inferred — tree.go:697 and tree.go:750 panic guards]
func TestScenario2_WildcardNotLastPanics(t *testing.T) {
	// Wildcard before a named param
	mustPanic(t, "wildcard", func() {
		r := chi.NewRouter()
		r.Get("/api/*/users", func(w http.ResponseWriter, r *http.Request) {})
	})
}

// TestScenario2b_WildcardWithTrailingTextPanics verifies that * with trailing
// non-wildcard text also panics.
// [Req: inferred — tree.go:750 panic guard]
func TestScenario2b_WildcardWithTrailingTextPanics(t *testing.T) {
	mustPanic(t, "wildcard", func() {
		r := chi.NewRouter()
		r.Get("/api/*extra", func(w http.ResponseWriter, r *http.Request) {})
	})
}

// TestScenario3_DuplicateParamKeyPanics verifies that a pattern with duplicate
// parameter keys panics at registration.
// [Req: inferred — tree.go:765 panic guard]
func TestScenario3_DuplicateParamKeyPanics(t *testing.T) {
	mustPanic(t, "duplicate param key", func() {
		r := chi.NewRouter()
		r.Get("/{id}/path/{id}", func(w http.ResponseWriter, r *http.Request) {})
	})
}

// TestScenario4_NilHandlerMountPanics verifies that Mount() with a nil handler panics.
// [Req: inferred — mux.go:291 panic guard]
func TestScenario4_NilHandlerMountPanics(t *testing.T) {
	mustPanic(t, "nil handler", func() {
		r := chi.NewRouter()
		r.Mount("/api", nil)
	})
}

// TestScenario4b_NilRouteFuncPanics verifies that Route() with a nil function panics.
// [Req: inferred — mux.go:274 panic guard]
func TestScenario4b_NilRouteFuncPanics(t *testing.T) {
	mustPanic(t, "nil subrouter", func() {
		r := chi.NewRouter()
		r.Route("/api", nil)
	})
}

// TestScenario5_ContextPoolReuseIsSafe verifies that sequential requests through the
// same mux do not leak URL params from one request into the next.
// [Req: inferred — mux.go:81-91 sync.Pool context reuse]
func TestScenario5_ContextPoolReuseIsSafe(t *testing.T) {
	r := chi.NewRouter()

	var capturedID string
	r.Get("/users/{id}", func(w http.ResponseWriter, r *http.Request) {
		capturedID = chi.URLParam(r, "id")
		w.Write([]byte(capturedID))
	})
	r.Get("/about", func(w http.ResponseWriter, r *http.Request) {
		// This handler should NOT see "id" from the previous /users/99 request
		capturedID = chi.URLParam(r, "id")
		w.Write([]byte("about"))
	})

	// First request sets "id" = "99"
	w1 := makeRequest(t, r, "GET", "/users/99")
	if w1.Code != 200 {
		t.Fatalf("first request: expected 200, got %d", w1.Code)
	}
	if bodyString(t, w1) != "99" {
		t.Fatalf("first request: expected '99'")
	}

	// Second request must not inherit "id" = "99" from first
	w2 := makeRequest(t, r, "GET", "/about")
	if w2.Code != 200 {
		t.Fatalf("second request: expected 200, got %d", w2.Code)
	}
	if capturedID != "" {
		t.Fatalf("context pool reuse leaked id=%q from first request into second", capturedID)
	}
}

// TestScenario6_MethodNotAllowedVsNotFound verifies the 405/404 distinction:
// - Registered path, wrong method → 405 with Allow header
// - Unregistered path → 404
// [Req: inferred — mux.go:480-484, tree.go methodNotAllowed flag]
func TestScenario6_MethodNotAllowedVsNotFound(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/items", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("items"))
	})
	r.Post("/items", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("created"))
	})

	// DELETE to /items → 405 (path exists, method not registered)
	w1 := makeRequest(t, r, "DELETE", "/items")
	if w1.Code != 405 {
		t.Fatalf("DELETE /items: expected 405, got %d", w1.Code)
	}
	allow := w1.Header().Get("Allow")
	if allow == "" {
		t.Fatal("DELETE /items: expected Allow header on 405")
	}

	// GET to /unknown → 404 (path not registered at all)
	w2 := makeRequest(t, r, "GET", "/unknown")
	if w2.Code != 404 {
		t.Fatalf("GET /unknown: expected 404, got %d", w2.Code)
	}
}

// TestScenario7_NestedRouterURLParams verifies that URL params captured at parent
// router level are accessible inside subrouter handlers.
// [Req: inferred — tree.go:387-388 URLParams append; mux.go Mount mountHandler]
func TestScenario7_NestedRouterURLParams(t *testing.T) {
	r := chi.NewRouter()
	r.Route("/{org}", func(r chi.Router) {
		r.Route("/api", func(r chi.Router) {
			r.Get("/{repo}", func(w http.ResponseWriter, r *http.Request) {
				org := chi.URLParam(r, "org")
				repo := chi.URLParam(r, "repo")
				w.Write([]byte(org + "/" + repo))
			})
		})
	})

	w := makeRequest(t, r, "GET", "/acme/api/myrepo")
	if w.Code != 200 {
		t.Fatalf("expected 200, got %d", w.Code)
	}
	body := bodyString(t, w)
	if body != "acme/myrepo" {
		t.Fatalf("expected 'acme/myrepo', got %q", body)
	}
}

// TestScenario8_RoutePatternWildcardCleanup verifies that RoutePattern() removes
// intermediate /* segments from the accumulated route pattern stack.
// [Req: inferred — context.go:139-144 replaceWildcards]
func TestScenario8_RoutePatternWildcardCleanup(t *testing.T) {
	// Simulate the pattern stack produced by nested Mount/Route calls
	rctx := chi.NewRouteContext()
	rctx.RoutePatterns = []string{"/v1/*", "/resources/*", "/{resource_id}"}

	got := rctx.RoutePattern()
	want := "/v1/resources/{resource_id}"
	if got != want {
		t.Fatalf("RoutePattern() = %q, want %q", got, want)
	}
}

// TestScenario8b_RoutePatternMultipleWildcards verifies that consecutive wildcards
// are also collapsed correctly.
// [Req: inferred — context.go replaceWildcards iterative loop]
func TestScenario8b_RoutePatternMultipleWildcards(t *testing.T) {
	rctx := chi.NewRouteContext()
	rctx.RoutePatterns = []string{"/v1/*", "/resources/*", "/*", "/{resource_id}"}

	got := rctx.RoutePattern()
	want := "/v1/resources/{resource_id}"
	if got != want {
		t.Fatalf("RoutePattern() = %q, want %q", got, want)
	}
}

// TestScenario9_InvalidRegexpPanics verifies that a route with an invalid regexp
// pattern panics at registration time.
// [Req: inferred — tree.go:258 regexp.Compile panic guard]
func TestScenario9_InvalidRegexpPanics(t *testing.T) {
	mustPanic(t, "invalid regexp", func() {
		r := chi.NewRouter()
		r.Get("/item/{id:[invalid}", func(w http.ResponseWriter, r *http.Request) {})
	})
}

// TestScenario10_DuplicateMountPanics verifies that mounting two handlers at the
// same path prefix panics.
// [Req: inferred — mux.go:296-299 findPattern duplicate mount check]
func TestScenario10_DuplicateMountPanics(t *testing.T) {
	mustPanic(t, "existing path", func() {
		sub1 := chi.NewRouter()
		sub1.Get("/", func(w http.ResponseWriter, r *http.Request) {})
		sub2 := chi.NewRouter()
		sub2.Get("/", func(w http.ResponseWriter, r *http.Request) {})

		r := chi.NewRouter()
		r.Mount("/api", sub1)
		r.Mount("/api", sub2) // duplicate — must panic
	})
}

// =============================================================================
// Group 3: Boundaries and Edge Cases
// One test per defensive pattern from Step 5 exploration.
// =============================================================================

// TestBoundary_URLParam_ReturnsEmptyWhenNotFound verifies that chi.URLParam returns
// "" when the key is not present in the routing context.
// [Req: inferred — context.go:10-14, URLParam nil guard]
func TestBoundary_URLParam_ReturnsEmptyWhenNotFound(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/ping", func(w http.ResponseWriter, r *http.Request) {
		val := chi.URLParam(r, "nonexistent")
		w.Write([]byte("val:" + val))
	})
	w := makeRequest(t, r, "GET", "/ping")
	if body := bodyString(t, w); body != "val:" {
		t.Fatalf("expected 'val:', got %q", body)
	}
}

// TestBoundary_URLParam_ReturnsEmptyWithNoContext verifies that URLParam on a plain
// request (no chi context) returns "".
// [Req: inferred — context.go RouteContext nil guard]
func TestBoundary_URLParam_ReturnsEmptyWithNoContext(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	val := chi.URLParam(req, "id")
	if val != "" {
		t.Fatalf("expected empty string without chi context, got %q", val)
	}
}

// TestBoundary_NilContext_RoutePattern verifies that RoutePattern() on a nil
// *Context returns "" without panicking.
// [Req: inferred — context.go:123 nil receiver guard]
func TestBoundary_NilContext_RoutePattern(t *testing.T) {
	var ctx *chi.Context
	if p := ctx.RoutePattern(); p != "" {
		t.Fatalf("nil Context.RoutePattern() = %q, want \"\"", p)
	}
}

// TestBoundary_PatternMustBeginWithSlash verifies that any route pattern not
// starting with '/' causes a panic.
// [Req: inferred — mux.go:418 panic guard]
func TestBoundary_PatternMustBeginWithSlash(t *testing.T) {
	mustPanic(t, "routing pattern must begin with '/'", func() {
		r := chi.NewRouter()
		r.Get("noslash", func(w http.ResponseWriter, r *http.Request) {})
	})
}

// TestBoundary_UnsupportedHTTPMethod panics when Method() is called with an
// unrecognized method string.
// [Req: inferred — mux.go:130 panic guard]
func TestBoundary_UnsupportedHTTPMethod(t *testing.T) {
	mustPanic(t, "http method is not supported", func() {
		r := chi.NewRouter()
		r.Method("FROBNICATE", "/", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {}))
	})
}

// TestBoundary_RegisterCustomMethod verifies that RegisterMethod adds support for a
// custom HTTP method without panicking.
// [Req: inferred — tree.go RegisterMethod function]
func TestBoundary_RegisterCustomMethod(t *testing.T) {
	chi.RegisterMethod("PURGE")
	r := chi.NewRouter()
	r.Method("PURGE", "/cache", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("purged"))
	}))
	w := makeRequest(t, r, "PURGE", "/cache")
	if w.Code != 200 {
		t.Fatalf("PURGE /cache: expected 200, got %d", w.Code)
	}
	if body := bodyString(t, w); body != "purged" {
		t.Fatalf("expected 'purged', got %q", body)
	}
}

// TestBoundary_CatchAll_MatchesIncludingSlashes verifies the catch-all node
// behavior for paths with multiple segments.
// [Req: inferred — tree.go ntCatchAll node handling]
func TestBoundary_CatchAll_MatchesIncludingSlashes(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/files/*", func(w http.ResponseWriter, r *http.Request) {
		wildcard := chi.URLParam(r, "*")
		w.Write([]byte(wildcard))
	})
	cases := []struct{ path, want string }{
		{"/files/a/b/c.txt", "a/b/c.txt"},
		{"/files/", ""},
		{"/files/single", "single"},
	}
	for _, tc := range cases {
		w := makeRequest(t, r, "GET", tc.path)
		if w.Code != 200 {
			t.Errorf("path %s: expected 200, got %d", tc.path, w.Code)
		}
		if body := bodyString(t, w); body != tc.want {
			t.Errorf("path %s: expected %q, got %q", tc.path, tc.want, body)
		}
	}
}

// TestBoundary_GroupMiddleware_Isolation verifies that Group() middleware applies
// only to routes within the group, not to sibling routes.
// [Req: inferred — mux.go Group/With inline middleware isolation]
func TestBoundary_GroupMiddleware_Isolation(t *testing.T) {
	var groupMWCalled bool
	r := chi.NewRouter()
	r.Group(func(r chi.Router) {
		r.Use(func(next http.Handler) http.Handler {
			return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				groupMWCalled = true
				next.ServeHTTP(w, r)
			})
		})
		r.Get("/protected", func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("protected"))
		})
	})
	r.Get("/public", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("public"))
	})

	// /public should NOT trigger group middleware
	groupMWCalled = false
	makeRequest(t, r, "GET", "/public")
	if groupMWCalled {
		t.Fatal("group middleware ran for /public route outside the group")
	}

	// /protected SHOULD trigger group middleware
	groupMWCalled = false
	makeRequest(t, r, "GET", "/protected")
	if !groupMWCalled {
		t.Fatal("group middleware did not run for /protected route inside the group")
	}
}

// TestBoundary_WithInlineMiddleware verifies that With() applies middleware only
// to that specific route, not to sibling routes.
// [Req: inferred — mux.go With() inline middleware design]
func TestBoundary_WithInlineMiddleware(t *testing.T) {
	var inlineMWCalled bool
	inlineMW := func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			inlineMWCalled = true
			next.ServeHTTP(w, r)
		})
	}

	r := chi.NewRouter()
	r.With(inlineMW).Get("/special", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("special"))
	})
	r.Get("/normal", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("normal"))
	})

	inlineMWCalled = false
	makeRequest(t, r, "GET", "/normal")
	if inlineMWCalled {
		t.Fatal("inline middleware ran for /normal route not using With()")
	}

	inlineMWCalled = false
	makeRequest(t, r, "GET", "/special")
	if !inlineMWCalled {
		t.Fatal("inline middleware did not run for /special route using With()")
	}
}

// TestBoundary_Find_UnknownMethod returns empty string for unknown HTTP methods.
// [Req: inferred — mux.go Find() methodMap lookup guard]
func TestBoundary_Find_UnknownMethod(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/ping", func(w http.ResponseWriter, r *http.Request) {})

	rctx := chi.NewRouteContext()
	pattern := r.Find(rctx, "UNKNOWN_METHOD_XYZ", "/ping")
	if pattern != "" {
		t.Fatalf("Find() with unknown method: expected empty pattern, got %q", pattern)
	}
}

// TestBoundary_Match_ReturnsBoolCorrectly verifies Match() returns true for a
// registered pattern and false for an unregistered one.
// [Req: inferred — mux.go Match() delegates to Find()]
func TestBoundary_Match_ReturnsBoolCorrectly(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/hello/{name}", func(w http.ResponseWriter, r *http.Request) {})

	rctx1 := chi.NewRouteContext()
	if !r.Match(rctx1, "GET", "/hello/world") {
		t.Fatal("Match() returned false for registered route /hello/world")
	}

	rctx2 := chi.NewRouteContext()
	if r.Match(rctx2, "GET", "/unknown") {
		t.Fatal("Match() returned true for unregistered route /unknown")
	}
}

// TestBoundary_Handle_ParsesMethodFromPattern verifies Handle() parses "METHOD path"
// from a single pattern string as a convenience form.
// [Req: inferred — mux.go Handle() string parsing: strings.IndexAny for space/tab]
func TestBoundary_Handle_ParsesMethodFromPattern(t *testing.T) {
	r := chi.NewRouter()
	r.Handle("GET /ping", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("pong"))
	}))
	w := makeRequest(t, r, "GET", "/ping")
	if w.Code != 200 {
		t.Fatalf("expected 200, got %d", w.Code)
	}
	if body := bodyString(t, w); body != "pong" {
		t.Fatalf("expected 'pong', got %q", body)
	}
}

// TestBoundary_RouteContext_IsAccessible verifies that chi.RouteContext returns
// the chi context set in the request, and is nil for a plain request.
// [Req: inferred — context.go RouteContext() type assertion with ok]
func TestBoundary_RouteContext_IsAccessible(t *testing.T) {
	// Plain request has no chi context
	req := httptest.NewRequest("GET", "/", nil)
	if chi.RouteContext(req.Context()) != nil {
		t.Fatal("expected nil RouteContext for plain request")
	}

	// Request served through chi has a context
	r := chi.NewRouter()
	var gotCtx *chi.Context
	r.Get("/ctx", func(w http.ResponseWriter, r *http.Request) {
		gotCtx = chi.RouteContext(r.Context())
		w.Write([]byte("ok"))
	})
	makeRequest(t, r, "GET", "/ctx")
	if gotCtx == nil {
		t.Fatal("expected non-nil RouteContext after chi routing")
	}
}

// TestBoundary_AllHTTPMethods_Parametrized verifies correct routing across all nine
// standard HTTP methods defined in chi's method map.
// [Req: formal — Router interface method list in chi.go; tree.go methodMap definition]
func TestBoundary_AllHTTPMethods_Parametrized(t *testing.T) {
	methods := []string{
		http.MethodGet, http.MethodPost, http.MethodPut, http.MethodDelete,
		http.MethodPatch, http.MethodHead, http.MethodOptions,
		http.MethodConnect, http.MethodTrace,
	}

	r := chi.NewRouter()
	for _, m := range methods {
		method := m
		r.Method(method, "/test", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("X-Method", method)
			w.WriteHeader(200)
		}))
	}

	for _, m := range methods {
		w := makeRequest(t, r, m, "/test")
		if w.Code != 200 {
			t.Errorf("method %s: expected 200, got %d", m, w.Code)
		}
		got := w.Header().Get("X-Method")
		if got != m {
			t.Errorf("method %s: X-Method header = %q, want %q", m, got, m)
		}
	}
}
