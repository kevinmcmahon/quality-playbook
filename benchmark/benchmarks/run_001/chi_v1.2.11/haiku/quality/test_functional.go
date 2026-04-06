// Package quality provides functional tests for chi router
package quality

import (
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"regexp"
	"strings"
	"sync"
	"testing"

	"github.com/go-chi/chi/v5"
)

// ============================================================================
// SPEC REQUIREMENT TESTS
// ============================================================================

// TestBasicRouting validates spec requirement: GET, POST, PUT, DELETE routes work
func TestBasicRouting(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/users", func(w http.ResponseWriter, r *http.Request) { w.Write([]byte("GET users")) })
	r.Post("/users", func(w http.ResponseWriter, r *http.Request) { w.Write([]byte("POST users")) })
	r.Put("/users/{id}", func(w http.ResponseWriter, r *http.Request) { w.Write([]byte("PUT user")) })
	r.Delete("/users/{id}", func(w http.ResponseWriter, r *http.Request) { w.Write([]byte("DELETE user")) })

	tests := []struct {
		method   string
		path     string
		expected string
	}{
		{"GET", "/users", "GET users"},
		{"POST", "/users", "POST users"},
		{"PUT", "/users/123", "PUT user"},
		{"DELETE", "/users/123", "DELETE user"},
	}

	for _, test := range tests {
		req := httptest.NewRequest(test.method, test.path, nil)
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)
		if got := w.Body.String(); got != test.expected {
			t.Errorf("method=%s path=%s: expected %q, got %q", test.method, test.path, test.expected, got)
		}
	}
}

// TestURLParameters validates spec requirement: URL parameters extracted from path
func TestURLParameters(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/users/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		w.Write([]byte("id=" + id))
	})
	r.Get("/posts/{year}-{month}-{day}", func(w http.ResponseWriter, r *http.Request) {
		year := chi.URLParam(r, "year")
		month := chi.URLParam(r, "month")
		day := chi.URLParam(r, "day")
		w.Write([]byte(fmt.Sprintf("date=%s-%s-%s", year, month, day)))
	})

	tests := []struct {
		path     string
		expected string
	}{
		{"/users/42", "id=42"},
		{"/users/john-doe", "id=john-doe"},
		{"/posts/2025-03-31", "date=2025-03-31"},
	}

	for _, test := range tests {
		req := httptest.NewRequest("GET", test.path, nil)
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)
		if got := w.Body.String(); got != test.expected {
			t.Errorf("path=%s: expected %q, got %q", test.path, test.expected, got)
		}
	}
}

// TestRegexParameters validates spec requirement: parameters with regex constraints
func TestRegexParameters(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/posts/{id:[0-9]+}", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("numeric"))
	})
	r.Get("/slugs/{slug:[a-z-]+}", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("slug"))
	})

	tests := []struct {
		path       string
		statusCode int
		expected   string
	}{
		{"/posts/123", 200, "numeric"},
		{"/posts/abc", 404, ""},       // numeric constraint fails
		{"/slugs/my-post", 200, "slug"},
		{"/slugs/my_post", 404, ""},   // underscore not in [a-z-]
	}

	for _, test := range tests {
		req := httptest.NewRequest("GET", test.path, nil)
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)
		if w.Code != test.statusCode {
			t.Errorf("path=%s: expected status %d, got %d", test.path, test.statusCode, w.Code)
		}
		if test.expected != "" && w.Body.String() != test.expected {
			t.Errorf("path=%s: expected body %q, got %q", test.path, test.expected, w.Body.String())
		}
	}
}

// TestCatchAll validates spec requirement: wildcard path matching
func TestCatchAll(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/files/*", func(w http.ResponseWriter, r *http.Request) {
		path := chi.URLParam(r, "*")
		w.Write([]byte("file:" + path))
	})

	tests := []struct {
		path     string
		expected string
	}{
		{"/files/doc.txt", "file:doc.txt"},
		{"/files/dir/subdir/file.pdf", "file:dir/subdir/file.pdf"},
		{"/files/", "file:"},
	}

	for _, test := range tests {
		req := httptest.NewRequest("GET", test.path, nil)
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)
		if got := w.Body.String(); got != test.expected {
			t.Errorf("path=%s: expected %q, got %q", test.path, test.expected, got)
		}
	}
}

// TestMiddlewareExecution validates spec requirement: middlewares wrap handlers
func TestMiddlewareExecution(t *testing.T) {
	r := chi.NewRouter()

	var calls []string
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			calls = append(calls, "mw1-in")
			next.ServeHTTP(w, r)
			calls = append(calls, "mw1-out")
		})
	})
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			calls = append(calls, "mw2-in")
			next.ServeHTTP(w, r)
			calls = append(calls, "mw2-out")
		})
	})
	r.Get("/test", func(w http.ResponseWriter, r *http.Request) {
		calls = append(calls, "handler")
		w.Write([]byte("ok"))
	})

	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	expected := []string{"mw1-in", "mw2-in", "handler", "mw2-out", "mw1-out"}
	if !stringSliceEqual(calls, expected) {
		t.Errorf("middleware order: expected %v, got %v", expected, calls)
	}
}

// TestNotFoundHandler validates spec requirement: 404 on undefined routes
func TestNotFoundHandler(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/users", func(w http.ResponseWriter, r *http.Request) { w.Write([]byte("users")) })

	req := httptest.NewRequest("GET", "/undefined", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("undefined route: expected 404, got %d", w.Code)
	}
}

// TestMethodNotAllowedHandler validates spec requirement: 405 on unsupported method
func TestMethodNotAllowedHandler(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/users/{id}", func(w http.ResponseWriter, r *http.Request) { w.Write([]byte("get")) })

	req := httptest.NewRequest("DELETE", "/users/123", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if w.Code != http.StatusMethodNotAllowed {
		t.Errorf("unsupported method on existing route: expected 405, got %d", w.Code)
	}
}

// TestRequestContext validates spec requirement: context values propagated through handlers
func TestRequestContext(t *testing.T) {
	r := chi.NewRouter()
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ctx := context.WithValue(r.Context(), "user", "alice")
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	})
	r.Get("/profile", func(w http.ResponseWriter, r *http.Request) {
		user := r.Context().Value("user")
		w.Write([]byte("user:" + user.(string)))
	})

	req := httptest.NewRequest("GET", "/profile", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if got := w.Body.String(); got != "user:alice" {
		t.Errorf("context propagation: expected %q, got %q", "user:alice", got)
	}
}

// TestSubrouterMounting validates spec requirement: Mount() for composable routers
func TestSubrouterMounting(t *testing.T) {
	apiRouter := chi.NewRouter()
	apiRouter.Get("/status", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("api-ok"))
	})

	r := chi.NewRouter()
	r.Mount("/api", apiRouter)
	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("ok"))
	})

	tests := []struct {
		path     string
		expected string
	}{
		{"/health", "ok"},
		{"/api/status", "api-ok"},
	}

	for _, test := range tests {
		req := httptest.NewRequest("GET", test.path, nil)
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)
		if got := w.Body.String(); got != test.expected {
			t.Errorf("path=%s: expected %q, got %q", test.path, test.expected, got)
		}
	}
}

// TestRouteGrouping validates spec requirement: Route() for nested groups
func TestRouteGrouping(t *testing.T) {
	r := chi.NewRouter()
	r.Route("/api", func(api chi.Router) {
		api.Get("/users", func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("users"))
		})
		api.Post("/users", func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("created"))
		})
		api.Route("/posts", func(posts chi.Router) {
			posts.Get("/", func(w http.ResponseWriter, r *http.Request) {
				w.Write([]byte("posts"))
			})
		})
	})

	tests := []struct {
		method   string
		path     string
		expected string
	}{
		{"GET", "/api/users", "users"},
		{"POST", "/api/users", "created"},
		{"GET", "/api/posts/", "posts"},
	}

	for _, test := range tests {
		req := httptest.NewRequest(test.method, test.path, nil)
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)
		if got := w.Body.String(); got != test.expected {
			t.Errorf("method=%s path=%s: expected %q, got %q", test.method, test.path, test.expected, got)
		}
	}
}

// ============================================================================
// FITNESS SCENARIO TESTS
// ============================================================================

// TestScenario1RegexCompilationError validates Scenario 1: invalid regex panics at registration
func TestScenario1RegexCompilationError(t *testing.T) {
	// Test that invalid regex patterns panic during registration, not at request time
	defer func() {
		if r := recover(); r == nil {
			t.Error("invalid regex pattern should panic during registration")
		}
	}()

	r := chi.NewRouter()
	r.Get("/posts/{id:[", func(w http.ResponseWriter, r *http.Request) {}) // invalid regex: unclosed [
}

// TestScenario2DuplicateParametersReject validates Scenario 2: duplicate parameter names panic
func TestScenario2DuplicateParametersReject(t *testing.T) {
	defer func() {
		if r := recover(); r == nil {
			t.Error("duplicate parameter names should panic during registration")
		}
	}()

	r := chi.NewRouter()
	r.Get("/posts/{id}/{id}", func(w http.ResponseWriter, r *http.Request) {}) // duplicate {id}
}

// TestScenario3EmptyPatternReject validates Scenario 3: empty patterns panic
func TestScenario3EmptyPatternReject(t *testing.T) {
	defer func() {
		if r := recover(); r == nil {
			t.Error("empty pattern should panic during registration")
		}
	}()

	r := chi.NewRouter()
	r.Get("", func(w http.ResponseWriter, r *http.Request) {}) // empty pattern
}

// TestScenario4MethodNotAllowedCorrectly validates Scenario 4: 405 not 404 for method unsupported
func TestScenario4MethodNotAllowedCorrectly(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/users/{id}", func(w http.ResponseWriter, r *http.Request) { w.Write([]byte("get")) })
	r.Post("/users/{id}", func(w http.ResponseWriter, r *http.Request) { w.Write([]byte("post")) })

	tests := []struct {
		method     string
		path       string
		statusCode int
		desc       string
	}{
		{"GET", "/users/123", 200, "valid GET"},
		{"POST", "/users/123", 200, "valid POST"},
		{"PUT", "/users/123", 405, "unsupported PUT on existing path"},
		{"DELETE", "/users/123", 405, "unsupported DELETE on existing path"},
		{"GET", "/posts/123", 404, "not found completely different path"},
	}

	for _, test := range tests {
		req := httptest.NewRequest(test.method, test.path, nil)
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)
		if w.Code != test.statusCode {
			t.Errorf("%s: expected %d, got %d", test.desc, test.statusCode, w.Code)
		}
	}
}

// TestScenario5ContextPoolReuse validates Scenario 5: context reused from pool is clean
func TestScenario5ContextPoolReuse(t *testing.T) {
	r := chi.NewRouter()

	var request1Params map[string]string
	r.Get("/first/{id}/{version}", func(w http.ResponseWriter, r *http.Request) {
		request1Params = map[string]string{
			"id":      chi.URLParam(r, "id"),
			"version": chi.URLParam(r, "version"),
		}
		w.Write([]byte("ok"))
	})

	// First request
	req1 := httptest.NewRequest("GET", "/first/alice/v1", nil)
	w1 := httptest.NewRecorder()
	r.ServeHTTP(w1, req1)

	// Second request with different params
	var request2Params map[string]string
	r2 := chi.NewRouter()
	r2.Get("/simple/{id}", func(w http.ResponseWriter, r *http.Request) {
		request2Params = map[string]string{
			"id": chi.URLParam(r, "id"),
		}
		w.Write([]byte("ok"))
	})
	req2 := httptest.NewRequest("GET", "/simple/bob", nil)
	w2 := httptest.NewRecorder()
	r2.ServeHTTP(w2, req2)

	// Verify first request had correct params
	if request1Params["id"] != "alice" || request1Params["version"] != "v1" {
		t.Errorf("request 1 params: expected id=alice version=v1, got id=%s version=%s",
			request1Params["id"], request1Params["version"])
	}

	// Verify second request had only its params, not first's
	if request2Params["id"] != "bob" {
		t.Errorf("request 2 params: expected id=bob, got id=%s", request2Params["id"])
	}
}

// TestScenario6ConcurrentParameterExtraction validates Scenario 6: concurrent requests don't mix parameters
func TestScenario6ConcurrentParameterExtraction(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/users/{id}/posts/{postID}", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		postID := chi.URLParam(r, "postID")
		w.Write([]byte(fmt.Sprintf("%s:%s", id, postID)))
	})

	var wg sync.WaitGroup
	results := make([]string, 10)

	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			path := fmt.Sprintf("/users/user%d/posts/post%d", idx, idx*10)
			req := httptest.NewRequest("GET", path, nil)
			w := httptest.NewRecorder()
			r.ServeHTTP(w, req)
			results[idx] = w.Body.String()
		}(i)
	}

	wg.Wait()

	for i := 0; i < 10; i++ {
		expected := fmt.Sprintf("user%d:post%d", i, i*10)
		if results[i] != expected {
			t.Errorf("concurrent request %d: expected %q, got %q", i, expected, results[i])
		}
	}
}

// TestScenario7WildcardPatternConflict validates Scenario 7: wildcard placement constraints
func TestScenario7WildcardPatternConflict(t *testing.T) {
	defer func() {
		if r := recover(); r == nil {
			t.Error("wildcard not at end should panic")
		}
	}()

	r := chi.NewRouter()
	r.Get("/files/*/other", func(w http.ResponseWriter, r *http.Request) {}) // wildcard not at end
}

// TestScenario8RouteInsertionOrderConsistency validates Scenario 8: insertion order doesn't affect routing
func TestScenario8RouteInsertionOrderConsistency(t *testing.T) {
	// Order 1: static then param
	r1 := chi.NewRouter()
	r1.Get("/users/admin", func(w http.ResponseWriter, r *http.Request) { w.Write([]byte("admin")) })
	r1.Get("/users/{id}", func(w http.ResponseWriter, r *http.Request) { w.Write([]byte("user")) })

	// Order 2: param then static
	r2 := chi.NewRouter()
	r2.Get("/users/{id}", func(w http.ResponseWriter, r *http.Request) { w.Write([]byte("user")) })
	r2.Get("/users/admin", func(w http.ResponseWriter, r *http.Request) { w.Write([]byte("admin")) })

	tests := []struct {
		path     string
		expected string
	}{
		{"/users/admin", "admin"},
		{"/users/bob", "user"},
		{"/users/123", "user"},
	}

	for _, test := range tests {
		// Test both orders produce same result
		req1 := httptest.NewRequest("GET", test.path, nil)
		w1 := httptest.NewRecorder()
		r1.ServeHTTP(w1, req1)

		req2 := httptest.NewRequest("GET", test.path, nil)
		w2 := httptest.NewRecorder()
		r2.ServeHTTP(w2, req2)

		if w1.Body.String() != test.expected {
			t.Errorf("order 1 path=%s: expected %q, got %q", test.path, test.expected, w1.Body.String())
		}
		if w2.Body.String() != test.expected {
			t.Errorf("order 2 path=%s: expected %q, got %q", test.path, test.expected, w2.Body.String())
		}
		if w1.Body.String() != w2.Body.String() {
			t.Errorf("insertion order path=%s: order 1 got %q, order 2 got %q", test.path, w1.Body.String(), w2.Body.String())
		}
	}
}

// TestScenario9NestedRouterParameterIsolation validates Scenario 9: nested routers isolate parameters
func TestScenario9NestedRouterParameterIsolation(t *testing.T) {
	r := chi.NewRouter()
	r.Route("/v{version}", func(v chi.Router) {
		v.Route("/orgs/{orgID}", func(org chi.Router) {
			org.Get("/users/{userID}", func(w http.ResponseWriter, r *http.Request) {
				version := chi.URLParam(r, "version")
				orgID := chi.URLParam(r, "orgID")
				userID := chi.URLParam(r, "userID")
				w.Write([]byte(fmt.Sprintf("v=%s org=%s user=%s", version, orgID, userID)))
			})
		})
	})

	tests := []struct {
		path     string
		expected string
	}{
		{"/v2/orgs/org123/users/user456", "v=2 org=org123 user=user456"},
		{"/v1/orgs/acme/users/alice", "v=1 org=acme user=alice"},
	}

	for _, test := range tests {
		req := httptest.NewRequest("GET", test.path, nil)
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)
		if got := w.Body.String(); got != test.expected {
			t.Errorf("path=%s: expected %q, got %q", test.path, test.expected, got)
		}
	}
}

// TestScenario10RegexAnchoringBehavior validates Scenario 10: regex patterns match correctly
func TestScenario10RegexAnchoringBehavior(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/articles/{id:[0-9]{3}}", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("3-digit"))
	})
	r.Get("/posts/{slug:[a-z-]+}", func(w http.ResponseWriter, r *http.Request) {
		slug := chi.URLParam(r, "slug")
		w.Write([]byte(slug))
	})

	tests := []struct {
		path       string
		statusCode int
		expected   string
	}{
		{"/articles/123", 200, "3-digit"},
		{"/articles/12", 404, ""},    // only 2 digits, [0-9]{3} requires 3
		{"/articles/1234", 404, ""},  // 4 digits, [0-9]{3} requires 3
		{"/posts/my-post", 200, "my-post"},
		{"/posts/my_post", 404, ""},  // underscore not in [a-z-]
	}

	for _, test := range tests {
		req := httptest.NewRequest("GET", test.path, nil)
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)
		if w.Code != test.statusCode {
			t.Errorf("path=%s: expected status %d, got %d", test.path, test.statusCode, w.Code)
		}
		if test.expected != "" && w.Body.String() != test.expected {
			t.Errorf("path=%s: expected body %q, got %q", test.path, test.expected, w.Body.String())
		}
	}
}

// ============================================================================
// DEFENSIVE PATTERN TESTS (Boundary & Edge Cases)
// ============================================================================

// TestEmptyRouterNilHandler validates pattern: no routes registered returns 404
func TestEmptyRouterNilHandler(t *testing.T) {
	r := chi.NewRouter()
	// No routes registered

	req := httptest.NewRequest("GET", "/anything", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if w.Code != http.StatusNotFound {
		t.Errorf("empty router: expected 404, got %d", w.Code)
	}
}

// TestMiddlewareBeforeRouteEnforcement validates pattern: middlewares must be registered before routes
func TestMiddlewareBeforeRouteEnforcement(t *testing.T) {
	defer func() {
		if r := recover(); r == nil {
			t.Error("middleware after route should panic")
		}
	}()

	r := chi.NewRouter()
	r.Get("/test", func(w http.ResponseWriter, r *http.Request) {})
	r.Use(func(next http.Handler) http.Handler { return next }) // middleware after route
}

// TestPatternMustStartWithSlash validates pattern: patterns must begin with /
func TestPatternMustStartWithSlash(t *testing.T) {
	defer func() {
		if r := recover(); r == nil {
			t.Error("pattern without leading / should panic")
		}
	}()

	r := chi.NewRouter()
	r.Get("users", func(w http.ResponseWriter, r *http.Request) {}) // no leading /
}

// TestMountWithNilHandler validates pattern: Mount() with nil handler panics
func TestMountWithNilHandler(t *testing.T) {
	defer func() {
		if r := recover(); r == nil {
			t.Error("Mount with nil handler should panic")
		}
	}()

	r := chi.NewRouter()
	r.Mount("/api", nil) // nil handler
}

// TestRouteWithNilHandler validates pattern: Route() with nil subrouter panics
func TestRouteWithNilHandler(t *testing.T) {
	defer func() {
		if r := recover(); r == nil {
			t.Error("Route with nil handler should panic")
		}
	}()

	r := chi.NewRouter()
	r.Route("/api", nil) // nil subrouter
}

// TestURLParamOnMultipleMatches validates boundary: URLParam returns correct value
func TestURLParamOnMultipleMatches(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/{year}/{month}/{day}", func(w http.ResponseWriter, r *http.Request) {
		year := chi.URLParam(r, "year")
		month := chi.URLParam(r, "month")
		day := chi.URLParam(r, "day")
		w.Write([]byte(fmt.Sprintf("%s-%s-%s", year, month, day)))
	})

	req := httptest.NewRequest("GET", "/2025/03/31", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if got := w.Body.String(); got != "2025-03-31" {
		t.Errorf("multi-param extraction: expected 2025-03-31, got %s", got)
	}
}

// TestRegexSpecialCharactersInPatternNames validates boundary: parameter names are safe
func TestRegexSpecialCharactersInPatternNames(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/{user_id}/{post-id}", func(w http.ResponseWriter, r *http.Request) {
		userID := chi.URLParam(r, "user_id")
		postID := chi.URLParam(r, "post-id")
		w.Write([]byte(fmt.Sprintf("%s:%s", userID, postID)))
	})

	req := httptest.NewRequest("GET", "/alice/42", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if got := w.Body.String(); got != "alice:42" {
		t.Errorf("special chars in param names: expected alice:42, got %s", got)
	}
}

// TestWildcardEmptySegment validates boundary: wildcard can match empty string
func TestWildcardEmptySegment(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/files/*", func(w http.ResponseWriter, r *http.Request) {
		path := chi.URLParam(r, "*")
		w.Write([]byte("path=" + path))
	})

	req := httptest.NewRequest("GET", "/files/", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if got := w.Body.String(); got != "path=" {
		t.Errorf("wildcard empty match: expected 'path=', got %q", got)
	}
}

// TestMultipleWildcardsRejected validates pattern: only one wildcard allowed per route
func TestMultipleWildcardsRejected(t *testing.T) {
	defer func() {
		if r := recover(); r == nil {
			t.Error("multiple wildcards should panic")
		}
	}()

	r := chi.NewRouter()
	r.Get("/files/*/more/*", func(w http.ResponseWriter, r *http.Request) {}) // multiple wildcards
}

// TestRoutePatternConstruction validates boundary: RoutePattern() returns full matched pattern
func TestRoutePatternConstruction(t *testing.T) {
	r := chi.NewRouter()
	var capturedPattern string
	r.Get("/users/{id}", func(w http.ResponseWriter, r *http.Request) {
		capturedPattern = chi.RoutePattern(r)
		w.Write([]byte("ok"))
	})

	req := httptest.NewRequest("GET", "/users/123", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if capturedPattern != "/users/{id}" {
		t.Errorf("RoutePattern: expected '/users/{id}', got %q", capturedPattern)
	}
}

// TestSubrouterParameterAccumulation validates boundary: nested routers accumulate all parameters
func TestSubrouterParameterAccumulation(t *testing.T) {
	r := chi.NewRouter()
	r.Route("/api/{version}", func(api chi.Router) {
		api.Route("/users/{userID}", func(users chi.Router) {
			users.Get("/posts/{postID}", func(w http.ResponseWriter, r *http.Request) {
				version := chi.URLParam(r, "version")
				userID := chi.URLParam(r, "userID")
				postID := chi.URLParam(r, "postID")
				if version == "" || userID == "" || postID == "" {
					w.WriteHeader(500)
					w.Write([]byte("missing params"))
					return
				}
				w.Write([]byte("ok"))
			})
		})
	})

	req := httptest.NewRequest("GET", "/api/v2/users/alice/posts/42", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if w.Code != 200 || w.Body.String() != "ok" {
		t.Errorf("param accumulation: expected 200 ok, got %d %s", w.Code, w.Body.String())
	}
}

// TestMiddlewareStackOrder validates pattern: middleware stack executes in registration order
func TestMiddlewareStackOrder(t *testing.T) {
	r := chi.NewRouter()
	var order []string

	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			order = append(order, "1-in")
			next.ServeHTTP(w, r)
			order = append(order, "1-out")
		})
	})

	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			order = append(order, "2-in")
			next.ServeHTTP(w, r)
			order = append(order, "2-out")
		})
	})

	r.Get("/test", func(w http.ResponseWriter, r *http.Request) {
		order = append(order, "handler")
	})

	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	expected := []string{"1-in", "2-in", "handler", "2-out", "1-out"}
	if !stringSliceEqual(order, expected) {
		t.Errorf("middleware order: expected %v, got %v", expected, order)
	}
}

// TestWithMiddlewareInlineApplication validates boundary: With() applies middleware to specific routes
func TestWithMiddlewareInlineApplication(t *testing.T) {
	r := chi.NewRouter()
	var calls []string

	mw := func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			calls = append(calls, "mw")
			next.ServeHTTP(w, r)
		})
	}

	r.With(mw).Get("/protected", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("protected"))
	})
	r.Get("/public", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("public"))
	})

	// Call protected route
	calls = nil
	req1 := httptest.NewRequest("GET", "/protected", nil)
	w1 := httptest.NewRecorder()
	r.ServeHTTP(w1, req1)
	if !contains(calls, "mw") {
		t.Error("With middleware should apply to /protected")
	}

	// Call public route
	calls = nil
	req2 := httptest.NewRequest("GET", "/public", nil)
	w2 := httptest.NewRecorder()
	r.ServeHTTP(w2, req2)
	if contains(calls, "mw") {
		t.Error("With middleware should not apply to /public")
	}
}

// TestGroupMiddlewareAppliedToGroup validates boundary: Group() middlewares apply to group only
func TestGroupMiddlewareAppliedToGroup(t *testing.T) {
	r := chi.NewRouter()
	var calls []string

	mw := func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			calls = append(calls, "mw")
			next.ServeHTTP(w, r)
		})
	}

	r.Route("/admin", func(admin chi.Router) {
		admin.Use(mw)
		admin.Get("/dashboard", func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("dashboard"))
		})
	})

	r.Get("/public", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("public"))
	})

	// Admin route should apply middleware
	calls = nil
	req1 := httptest.NewRequest("GET", "/admin/dashboard", nil)
	w1 := httptest.NewRecorder()
	r.ServeHTTP(w1, req1)
	if !contains(calls, "mw") {
		t.Error("Group middleware should apply to routes in group")
	}

	// Public route should not apply group middleware
	calls = nil
	req2 := httptest.NewRequest("GET", "/public", nil)
	w2 := httptest.NewRecorder()
	r.ServeHTTP(w2, req2)
	if contains(calls, "mw") {
		t.Error("Group middleware should not apply outside group")
	}
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

func stringSliceEqual(a, b []string) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}

func contains(slice []string, elem string) bool {
	for _, v := range slice {
		if v == elem {
			return true
		}
	}
	return false
}
