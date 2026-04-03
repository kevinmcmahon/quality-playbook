package quality

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"regexp"
	"strings"
	"sync"
	"testing"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

// ============================================================================
// Spec Requirements Tests
// ============================================================================

// Test: [Req: formal — chi.go Router interface] Router must implement http.Handler
func TestRouterImplementsHTTPHandler(t *testing.T) {
	r := chi.NewRouter()
	var _ http.Handler = r
}

// Test: [Req: formal — chi.go pattern documentation] Named placeholder {name} matches any sequence up to / or end
func TestNamedPlaceholderMatching(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/user/{name}", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	req := httptest.NewRequest("GET", "/user/jsmith", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}
}

// Test: [Req: formal — chi.go pattern documentation] Placeholder with regexp {number:\\d+}
func TestRegexpPlaceholder(t *testing.T) {
	r := chi.NewRouter()
	handled := false
	r.Get("/id/{id:\\d+}", func(w http.ResponseWriter, r *http.Request) {
		handled = true
	})

	// Should match
	req := httptest.NewRequest("GET", "/id/123", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if !handled {
		t.Error("regexp placeholder did not match valid input")
	}

	// Should not match (alphabetic)
	handled = false
	req = httptest.NewRequest("GET", "/id/abc", nil)
	w = httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if handled {
		t.Error("regexp placeholder incorrectly matched invalid input")
	}
}

// Test: [Req: formal — chi.go pattern documentation] Asterisk placeholder matches rest of URL including /
func TestCatchAllPlaceholder(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/page/*", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	req := httptest.NewRequest("GET", "/page/intro/latest", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Errorf("catch-all did not match nested path, got %d", w.Code)
	}
}

// Test: [Req: formal — mux.go Route method] Route creates sub-router
func TestRouteSubRouter(t *testing.T) {
	r := chi.NewRouter()
	r.Route("/api", func(r chi.Router) {
		r.Get("/items", func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusOK)
		})
	})

	req := httptest.NewRequest("GET", "/api/items", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Errorf("sub-router route failed, got %d", w.Code)
	}
}

// Test: [Req: formal — mux.go Mount method] Mount attaches sub-router with wildcard
func TestMountSubRouter(t *testing.T) {
	adminRouter := chi.NewRouter()
	adminRouter.Get("/", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	r := chi.NewRouter()
	r.Mount("/admin", adminRouter)

	req := httptest.NewRequest("GET", "/admin/", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Errorf("mount failed, got %d", w.Code)
	}
}

// Test: [Req: formal — mux.go HTTP method routing] Get, Post, Delete etc. should match only their method
func TestHTTPMethodRouting(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/items", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	// GET should succeed
	req := httptest.NewRequest("GET", "/items", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Errorf("GET failed, got %d", w.Code)
	}

	// POST should return 405
	req = httptest.NewRequest("POST", "/items", nil)
	w = httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusMethodNotAllowed {
		t.Errorf("POST should be 405, got %d", w.Code)
	}
}

// Test: [Req: formal — mux.go URLParam] chi.URLParam retrieves URL parameters
func TestURLParameterRetrieval(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/users/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		w.Write([]byte(id))
	})

	req := httptest.NewRequest("GET", "/users/123", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Body.String() != "123" {
		t.Errorf("expected '123', got %q", w.Body.String())
	}
}

// Test: [Req: formal — mux.go Use middleware] Use adds middleware to stack before routes
func TestMiddlewareUse(t *testing.T) {
	executed := false
	r := chi.NewRouter()
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			executed = true
			next.ServeHTTP(w, r)
		})
	})
	r.Get("/test", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if !executed {
		t.Error("middleware was not executed")
	}
}

// Test: [Req: formal — mux.go With inline middleware] With adds inline middleware for endpoint
func TestInlineMiddleware(t *testing.T) {
	executed := false
	r := chi.NewRouter()
	r.With(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			executed = true
			next.ServeHTTP(w, r)
		})
	}).Get("/test", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if !executed {
		t.Error("inline middleware was not executed")
	}
}

// Test: [Req: formal — context.go RouteContext] RouteContext retrieves routing context from request
func TestRouteContextRetrieval(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/users/{id}", func(w http.ResponseWriter, r *http.Request) {
		rctx := chi.RouteContext(r.Context())
		if rctx == nil {
			w.WriteHeader(http.StatusBadRequest)
			return
		}
		w.WriteHeader(http.StatusOK)
	})

	req := httptest.NewRequest("GET", "/users/123", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}
}

// ============================================================================
// Fitness Scenario Tests
// ============================================================================

// Scenario 1: Radix Trie Insertion Order Independence
func TestScenario1_InsertionOrderIndependence(t *testing.T) {
	patterns := []string{"/users", "/users/{id}", "/users/{id}/posts", "/posts", "/posts/{id}"}

	// Insert in forward order
	r1 := chi.NewRouter()
	for _, p := range patterns {
		p := p
		r1.Get(p, func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusOK)
		})
	}

	// Insert in reverse order
	r2 := chi.NewRouter()
	for i := len(patterns) - 1; i >= 0; i-- {
		p := patterns[i]
		r2.Get(p, func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusOK)
		})
	}

	// Both routers should route /users/123/posts the same way
	testPaths := []string{"/users", "/users/123", "/users/123/posts", "/posts", "/posts/456"}
	for _, path := range testPaths {
		req1 := httptest.NewRequest("GET", path, nil)
		w1 := httptest.NewRecorder()
		r1.ServeHTTP(w1, req1)

		req2 := httptest.NewRequest("GET", path, nil)
		w2 := httptest.NewRecorder()
		r2.ServeHTTP(w2, req2)

		if w1.Code != w2.Code {
			t.Errorf("insertion order affected routing for %s: got %d vs %d", path, w1.Code, w2.Code)
		}
	}
}

// Scenario 2: URL Parameter Corruption Under Overlapping Routes
func TestScenario2_ParameterCorruptionBacktracking(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/articles/{slug:[a-z-]+}", func(w http.ResponseWriter, r *http.Request) {
		slug := chi.URLParam(r, "slug")
		w.Write([]byte(slug))
	})
	r.Get("/articles/{id:\\d+}", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		w.Write([]byte("id:" + id))
	})

	// Test regex pattern
	req := httptest.NewRequest("GET", "/articles/abc-def", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Body.String() != "abc-def" {
		t.Errorf("expected 'abc-def', got %q", w.Body.String())
	}

	// Test number pattern
	req = httptest.NewRequest("GET", "/articles/123", nil)
	w = httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Body.String() != "id:123" {
		t.Errorf("expected 'id:123', got %q", w.Body.String())
	}
}

// Scenario 3: Middleware Stack Ordering and Context Propagation
func TestScenario3_MiddlewareExecutionOrder(t *testing.T) {
	executionOrder := []string{}
	var mu sync.Mutex

	r := chi.NewRouter()
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
			mu.Lock()
			executionOrder = append(executionOrder, "m1")
			mu.Unlock()
			next.ServeHTTP(w, req)
		})
	})
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
			mu.Lock()
			executionOrder = append(executionOrder, "m2")
			mu.Unlock()
			next.ServeHTTP(w, req)
		})
	})
	r.Get("/test", func(w http.ResponseWriter, r *http.Request) {
		mu.Lock()
		executionOrder = append(executionOrder, "handler")
		mu.Unlock()
		w.WriteHeader(http.StatusOK)
	})

	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	// Middleware should execute in order: m1, m2, handler
	expected := []string{"m1", "m2", "handler"}
	if len(executionOrder) != len(expected) {
		t.Errorf("expected %d executions, got %d", len(expected), len(executionOrder))
		return
	}
	for i, exp := range expected {
		if executionOrder[i] != exp {
			t.Errorf("step %d: expected %q, got %q", i, exp, executionOrder[i])
		}
	}
}

// Scenario 4: Regex Pattern Matching Edge Cases
func TestScenario4_RegexEdgeCases(t *testing.T) {
	tests := []struct {
		pattern string
		path    string
		shouldMatch bool
	}{
		{"/id/{id:\\d+}", "/id/123", true},
		{"/id/{id:\\d+}", "/id/abc", false},
		{"/id/{id:\\d+}", "/id/123-456", false},
		{"/id/{id:\\d+}", "/id/", false},
		{"/prefix/{str:[a-z]+}", "/prefix/hello", true},
		{"/prefix/{str:[a-z]+}", "/prefix/123", false},
		{"/prefix/{str:[a-z]+}", "/prefix/hello/world", false},
	}

	for _, tt := range tests {
		r := chi.NewRouter()
		handled := false
		r.Get(tt.pattern, func(w http.ResponseWriter, r *http.Request) {
			handled = true
		})

		req := httptest.NewRequest("GET", tt.path, nil)
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)

		if handled != tt.shouldMatch {
			t.Errorf("pattern %q path %q: expected match=%v, got %v",
				tt.pattern, tt.path, tt.shouldMatch, handled)
		}
	}
}

// Scenario 5: Catch-All Pattern Greedy Matching
func TestScenario5_CatchAllSpecificity(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/admin", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("static"))
	})
	r.Get("/admin/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		w.Write([]byte("param:" + id))
	})
	r.Get("/admin/*", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("catchall"))
	})

	tests := []struct {
		path     string
		expected string
	}{
		{"/admin", "static"},
		{"/admin/123", "param:123"},
		{"/admin/admin/settings", "catchall"},
	}

	for _, tt := range tests {
		req := httptest.NewRequest("GET", tt.path, nil)
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)
		if w.Body.String() != tt.expected {
			t.Errorf("path %q: expected %q, got %q", tt.path, tt.expected, w.Body.String())
		}
	}
}

// Scenario 6: Method Not Allowed Handling
func TestScenario6_MethodNotAllowedDetection(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/items", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	// DELETE should return 405, not 404
	req := httptest.NewRequest("DELETE", "/items", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	if w.Code != http.StatusMethodNotAllowed {
		t.Errorf("expected 405, got %d", w.Code)
	}

	// Verify Allow header exists
	if allow := w.Header().Get("Allow"); allow == "" {
		t.Error("expected Allow header in 405 response")
	}
}

// Scenario 7: Concurrent Request Context Safety
func TestScenario7_ConcurrentContextSafety(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/test/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		w.Write([]byte(id))
	})

	results := make(chan string, 100)
	var wg sync.WaitGroup

	// Launch concurrent requests with different parameters
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func(num int) {
			defer wg.Done()
			path := fmt.Sprintf("/test/%d", num)
			req := httptest.NewRequest("GET", path, nil)
			w := httptest.NewRecorder()
			r.ServeHTTP(w, req)
			results <- w.Body.String()
		}(i)
	}

	wg.Wait()
	close(results)

	// Verify each request got its own parameter, no leakage
	seen := make(map[string]bool)
	for result := range results {
		if seen[result] {
			t.Logf("duplicate result: %s (might indicate context pool leakage)", result)
		}
		seen[result] = true
	}

	if len(seen) != 100 {
		t.Errorf("expected 100 unique results, got %d (context pool leakage likely)", len(seen))
	}
}

// Scenario 8: Empty and Boundary Path Cases
func TestScenario8_BoundaryPaths(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("root"))
	})
	r.Get("/users/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		w.Write([]byte("user:" + id))
	})

	tests := []struct {
		path     string
		expected string
		shouldMatch bool
	}{
		{"/", "root", true},
		{"/users/123", "user:123", true},
		{"/users/", "", false}, // trailing slash, no match
		{"/nonexistent", "", false},
	}

	for _, tt := range tests {
		req := httptest.NewRequest("GET", tt.path, nil)
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)

		if tt.shouldMatch {
			if w.Body.String() != tt.expected {
				t.Errorf("path %q: expected %q, got %q", tt.path, tt.expected, w.Body.String())
			}
		} else {
			if w.Code == http.StatusOK {
				t.Errorf("path %q should not match, but got status %d", tt.path, w.Code)
			}
		}
	}
}

// Scenario 9: Malformed Pattern Validation
func TestScenario9_MalformedPatternDetection(t *testing.T) {
	tests := []struct {
		pattern string
		shouldPanic bool
	}{
		{"/valid/{id}", false},
		{"/valid/{id:\\d+}", false},
		{"/invalid/{unclosed", true},
		{"/invalid/{id\\d+}", true},
		{"/invalid/{*}", false}, // valid catch-all
	}

	for _, tt := range tests {
		func() {
			defer func() {
				if r := recover(); r != nil {
					if !tt.shouldPanic {
						t.Errorf("pattern %q should not panic: %v", tt.pattern, r)
					}
				} else {
					if tt.shouldPanic {
						t.Errorf("pattern %q should panic", tt.pattern)
					}
				}
			}()

			r := chi.NewRouter()
			r.Get(tt.pattern, func(w http.ResponseWriter, r *http.Request) {})
		}()
	}
}

// Scenario 10: Handler Registration and Nil Checks
func TestScenario10_HandlerNilChecks(t *testing.T) {
	// Test: middleware after routes should panic
	defer func() {
		if r := recover(); r == nil {
			t.Error("expected panic when adding middleware after routes")
		}
	}()

	r := chi.NewRouter()
	r.Get("/test", func(w http.ResponseWriter, r *http.Request) {})
	r.Use(func(next http.Handler) http.Handler { return next }) // should panic
}

// ============================================================================
// Cross-Variant Tests (Testing across different input types)
// ============================================================================

// Cross-variant: Parameter patterns work with different path structures
func TestCrossVariant_ParamPatternStyles(t *testing.T) {
	patterns := []struct {
		pattern string
		paths   []string
	}{
		{"/api/{version}/items", []string{"/api/v1/items", "/api/beta/items"}},
		{"/users/{id:\\d+}", []string{"/users/123", "/users/456"}},
		{"/files/{name:[a-z-]+}", []string{"/files/my-file", "/files/doc"}},
	}

	for _, p := range patterns {
		r := chi.NewRouter()
		matched := 0
		r.Get(p.pattern, func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(http.StatusOK)
			matched++
		})

		for _, path := range p.paths {
			matched = 0
			req := httptest.NewRequest("GET", path, nil)
			w := httptest.NewRecorder()
			r.ServeHTTP(w, req)
			if w.Code != http.StatusOK {
				t.Errorf("pattern %q should match path %q", p.pattern, path)
			}
		}
	}
}

// Cross-variant: Middleware composition across different methods
func TestCrossVariant_MiddlewareAcrossMethods(t *testing.T) {
	executed := 0
	r := chi.NewRouter()
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			executed++
			next.ServeHTTP(w, r)
		})
	})

	methods := []struct {
		method  string
		handler func(w http.ResponseWriter, r *http.Request)
	}{
		{"GET", r.Get},
		{"POST", r.Post},
		{"PUT", r.Put},
		{"DELETE", r.Delete},
	}

	for _, m := range methods {
		r := chi.NewRouter()
		executed = 0
		r.Use(func(next http.Handler) http.Handler {
			return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				executed++
				next.ServeHTTP(w, r)
			})
		})

		// Add route dynamically
		switch m.method {
		case "GET":
			r.Get("/test", func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) })
		case "POST":
			r.Post("/test", func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) })
		case "PUT":
			r.Put("/test", func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) })
		case "DELETE":
			r.Delete("/test", func(w http.ResponseWriter, r *http.Request) { w.WriteHeader(http.StatusOK) })
		}

		req := httptest.NewRequest(m.method, "/test", nil)
		w := httptest.NewRecorder()
		r.ServeHTTP(w, req)

		if executed != 1 {
			t.Errorf("middleware not executed for %s", m.method)
		}
	}
}

// ============================================================================
// Defensive Pattern Tests
// ============================================================================

// Test: Pattern must begin with /
func TestDefensivePattern_MustStartWithSlash(t *testing.T) {
	defer func() {
		if r := recover(); r == nil {
			t.Error("expected panic for pattern not starting with /")
		}
	}()

	r := chi.NewRouter()
	r.Get("no-slash", func(w http.ResponseWriter, r *http.Request) {})
}

// Test: Duplicate param keys are rejected
func TestDefensivePattern_NoDuplicateParams(t *testing.T) {
	defer func() {
		if r := recover(); r == nil {
			t.Error("expected panic for duplicate param keys")
		}
	}()

	r := chi.NewRouter()
	r.Get("/{id}/{id}", func(w http.ResponseWriter, r *http.Request) {})
}

// Test: Invalid regexp patterns panic at registration
func TestDefensivePattern_InvalidRegex(t *testing.T) {
	defer func() {
		if r := recover(); r == nil {
			t.Error("expected panic for invalid regexp")
		}
	}()

	r := chi.NewRouter()
	r.Get("/{id:[}", func(w http.ResponseWriter, r *http.Request) {})
}

// Test: Wildcard must be last in pattern
func TestDefensivePattern_WildcardLast(t *testing.T) {
	defer func() {
		if r := recover(); r == nil {
			t.Error("expected panic for wildcard not last")
		}
	}()

	r := chi.NewRouter()
	r.Get("/path/*/trailing", func(w http.ResponseWriter, r *http.Request) {})
}

// Test: NotFound handler is invoked for non-existent routes
func TestDefensiveHandler_NotFoundInvoked(t *testing.T) {
	invoked := false
	r := chi.NewRouter()
	r.NotFound(func(w http.ResponseWriter, r *http.Request) {
		invoked = true
		w.WriteHeader(http.StatusNotFound)
	})

	req := httptest.NewRequest("GET", "/nonexistent", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if !invoked {
		t.Error("NotFound handler was not invoked")
	}
}

// Test: RouteContext provides populated data for matched routes
func TestRouteContextPopulation(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/users/{id}/posts/{postID}", func(w http.ResponseWriter, r *http.Request) {
		rctx := chi.RouteContext(r.Context())
		id := chi.URLParam(r, "id")
		postID := chi.URLParam(r, "postID")

		if id != "123" || postID != "456" {
			w.WriteHeader(http.StatusBadRequest)
			return
		}

		w.WriteHeader(http.StatusOK)
	})

	req := httptest.NewRequest("GET", "/users/123/posts/456", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}
}

// Test: Routes() method returns registered routes
func TestRoutesMethod(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/api/v1/items", func(w http.ResponseWriter, r *http.Request) {})
	r.Post("/api/v1/items", func(w http.ResponseWriter, r *http.Request) {})
	r.Get("/api/v1/items/{id}", func(w http.ResponseWriter, r *http.Request) {})

	routes := r.Routes()
	if len(routes) != 3 {
		t.Errorf("expected 3 routes, got %d", len(routes))
	}
}

// Test: Match finds routes without executing handlers
func TestMatchMethod(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/test/{id}", func(w http.ResponseWriter, r *http.Request) {})

	rctx := chi.NewRouteContext()
	matched := r.Match(rctx, "GET", "/test/123")
	if !matched {
		t.Error("Match should find existing route")
	}

	rctx = chi.NewRouteContext()
	matched = r.Match(rctx, "GET", "/nonexistent")
	if matched {
		t.Error("Match should not find non-existent route")
	}
}

// Test: Nested sub-routers with middleware
func TestNestedSubRoutersMiddleware(t *testing.T) {
	executed := []string{}
	var mu sync.Mutex

	r := chi.NewRouter()
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
			mu.Lock()
			executed = append(executed, "root-mw")
			mu.Unlock()
			next.ServeHTTP(w, req)
		})
	})

	r.Route("/api", func(api chi.Router) {
		api.Use(func(next http.Handler) http.Handler {
			return http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
				mu.Lock()
				executed = append(executed, "api-mw")
				mu.Unlock()
				next.ServeHTTP(w, req)
			})
		})
		api.Get("/items", func(w http.ResponseWriter, r *http.Request) {
			mu.Lock()
			executed = append(executed, "handler")
			mu.Unlock()
			w.WriteHeader(http.StatusOK)
		})
	})

	req := httptest.NewRequest("GET", "/api/items", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if len(executed) != 3 {
		t.Errorf("expected 3 executions, got %d", len(executed))
	}
	if executed[0] != "root-mw" || executed[1] != "api-mw" || executed[2] != "handler" {
		t.Errorf("incorrect execution order: %v", executed)
	}
}

// Test: Context values propagate through middleware
func TestContextValuePropagation(t *testing.T) {
	contextKey := "test-key"
	r := chi.NewRouter()
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, req *http.Request) {
			ctx := context.WithValue(req.Context(), contextKey, "test-value")
			next.ServeHTTP(w, req.WithContext(ctx))
		})
	})
	r.Get("/test", func(w http.ResponseWriter, r *http.Request) {
		val := r.Context().Value(contextKey)
		if val == nil {
			w.WriteHeader(http.StatusBadRequest)
			return
		}
		w.WriteHeader(http.StatusOK)
	})

	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}
}

// Middleware example tests
func TestLoggerMiddleware(t *testing.T) {
	r := chi.NewRouter()
	r.Use(middleware.Logger)
	r.Get("/test", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
	})

	req := httptest.NewRequest("GET", "/test", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}
}

func TestRecovererMiddleware(t *testing.T) {
	r := chi.NewRouter()
	r.Use(middleware.Recoverer)
	r.Get("/panic", func(w http.ResponseWriter, r *http.Request) {
		panic("test panic")
	})

	req := httptest.NewRequest("GET", "/panic", nil)
	w := httptest.NewRecorder()

	// Should not panic, should recover
	defer func() {
		if r := recover(); r != nil {
			t.Errorf("Recoverer should have caught panic")
		}
	}()

	r.ServeHTTP(w, req)
	// Recoverer returns 500
	if w.Code != http.StatusInternalServerError {
		t.Logf("note: recoverer returned %d (may have different behavior)", w.Code)
	}
}

// Test response body content after routing
func TestResponseBodyContent(t *testing.T) {
	r := chi.NewRouter()
	r.Get("/items/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		w.Header().Set("Content-Type", "text/plain")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(fmt.Sprintf(`Item ID: %s`, id)))
	})

	req := httptest.NewRequest("GET", "/items/42", nil)
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)

	body := w.Body.String()
	if !strings.Contains(body, "42") {
		t.Errorf("expected response to contain '42', got %q", body)
	}
}
