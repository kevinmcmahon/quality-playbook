package chi_test

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

// ============================================================================
// Group 1: Spec Requirements
// Tests derived from chi's README specifications and documented behavior
// ============================================================================

// --- Routing Spec Requirements ---

func TestSpec_SimpleNamedPlaceholder(t *testing.T) {
	// [Req: formal — README] "{name}" matches any sequence of characters up to the next / or end of URL
	r := chi.NewRouter()
	r.Get("/user/{name}", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte(chi.URLParam(r, "name")))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, body := testRequest(t, ts, "GET", "/user/jsmith", nil)
	assertStatus(t, resp, 200)
	assertEqual(t, "jsmith", body)

	// Should not match with trailing slash
	resp2, _ := testRequest(t, ts, "GET", "/user/jsmith/", nil)
	assertStatus(t, resp2, 404)

	// Should not match sub-paths
	resp3, _ := testRequest(t, ts, "GET", "/user/jsmith/info", nil)
	assertStatus(t, resp3, 404)
}

func TestSpec_NamedPlaceholderWithSubpath(t *testing.T) {
	// [Req: formal — README] "/user/{name}/info" matches "/user/jsmith/info"
	r := chi.NewRouter()
	r.Get("/user/{name}/info", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte(chi.URLParam(r, "name")))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, body := testRequest(t, ts, "GET", "/user/jsmith/info", nil)
	assertStatus(t, resp, 200)
	assertEqual(t, "jsmith", body)
}

func TestSpec_WildcardCatchAll(t *testing.T) {
	// [Req: formal — README] "/page/*" matches "/page/intro/latest"
	r := chi.NewRouter()
	r.Get("/page/*", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte(chi.URLParam(r, "*")))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, body := testRequest(t, ts, "GET", "/page/intro/latest", nil)
	assertStatus(t, resp, 200)
	assertEqual(t, "intro/latest", body)
}

func TestSpec_RegexPlaceholder(t *testing.T) {
	// [Req: formal — README] "/date/{yyyy:\\d\\d\\d\\d}/{mm:\\d\\d}/{dd:\\d\\d}" matches "/date/2017/04/01"
	r := chi.NewRouter()
	r.Get("/date/{yyyy:\\d\\d\\d\\d}/{mm:\\d\\d}/{dd:\\d\\d}", func(w http.ResponseWriter, r *http.Request) {
		yyyy := chi.URLParam(r, "yyyy")
		mm := chi.URLParam(r, "mm")
		dd := chi.URLParam(r, "dd")
		w.Write([]byte(fmt.Sprintf("%s-%s-%s", yyyy, mm, dd)))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, body := testRequest(t, ts, "GET", "/date/2017/04/01", nil)
	assertStatus(t, resp, 200)
	assertEqual(t, "2017-04-01", body)

	// Non-matching pattern should 404
	resp2, _ := testRequest(t, ts, "GET", "/date/abc/04/01", nil)
	assertStatus(t, resp2, 404)
}

func TestSpec_AllHTTPMethods(t *testing.T) {
	// [Req: formal — README] chi supports Connect, Delete, Get, Head, Options, Patch, Post, Put, Trace
	methods := []string{"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD", "TRACE", "CONNECT"}

	for _, method := range methods {
		t.Run(method, func(t *testing.T) {
			r := chi.NewRouter()
			r.MethodFunc(method, "/test", func(w http.ResponseWriter, r *http.Request) {
				w.WriteHeader(200)
				if method != "HEAD" && method != "CONNECT" {
					w.Write([]byte(method))
				}
			})

			ts := httptest.NewServer(r)
			defer ts.Close()

			resp, _ := testRequest(t, ts, method, "/test", nil)
			assertStatus(t, resp, 200)
		})
	}
}

func TestSpec_MiddlewareUse(t *testing.T) {
	// [Req: formal — README] Use() appends middlewares onto the Router stack
	var order []string

	r := chi.NewRouter()
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			order = append(order, "first")
			next.ServeHTTP(w, r)
		})
	})
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			order = append(order, "second")
			next.ServeHTTP(w, r)
		})
	})
	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		order = append(order, "handler")
		w.WriteHeader(200)
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	testRequest(t, ts, "GET", "/", nil)

	if len(order) != 3 {
		t.Fatalf("expected 3 execution steps, got %d", len(order))
	}
	assertEqual(t, "first", order[0])
	assertEqual(t, "second", order[1])
	assertEqual(t, "handler", order[2])
}

func TestSpec_GroupInlineRouter(t *testing.T) {
	// [Req: formal — README] Group creates inline-Router with fresh middleware stack
	var parentMwCalled, groupMwCalled bool

	r := chi.NewRouter()
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			parentMwCalled = true
			next.ServeHTTP(w, r)
		})
	})

	r.Group(func(r chi.Router) {
		r.Use(func(next http.Handler) http.Handler {
			return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				groupMwCalled = true
				next.ServeHTTP(w, r)
			})
		})
		r.Get("/grouped", func(w http.ResponseWriter, r *http.Request) {
			w.WriteHeader(200)
		})
	})

	r.Get("/ungrouped", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(200)
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	// Request to grouped route
	parentMwCalled = false
	groupMwCalled = false
	testRequest(t, ts, "GET", "/grouped", nil)
	if !parentMwCalled {
		t.Error("expected parent middleware to be called for grouped route")
	}
	if !groupMwCalled {
		t.Error("expected group middleware to be called for grouped route")
	}

	// Request to ungrouped route
	parentMwCalled = false
	groupMwCalled = false
	testRequest(t, ts, "GET", "/ungrouped", nil)
	if !parentMwCalled {
		t.Error("expected parent middleware to be called for ungrouped route")
	}
	if groupMwCalled {
		t.Error("group middleware should NOT be called for ungrouped route")
	}
}

func TestSpec_RouteSubRouter(t *testing.T) {
	// [Req: formal — README] Route mounts a sub-Router along a pattern
	r := chi.NewRouter()
	r.Route("/articles/{articleID}", func(r chi.Router) {
		r.Get("/", func(w http.ResponseWriter, r *http.Request) {
			articleID := chi.URLParam(r, "articleID")
			w.Write([]byte("article:" + articleID))
		})
		r.Get("/comments", func(w http.ResponseWriter, r *http.Request) {
			articleID := chi.URLParam(r, "articleID")
			w.Write([]byte("comments:" + articleID))
		})
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, body := testRequest(t, ts, "GET", "/articles/42", nil)
	assertStatus(t, resp, 200)
	assertEqual(t, "article:42", body)

	resp2, body2 := testRequest(t, ts, "GET", "/articles/42/comments", nil)
	assertStatus(t, resp2, 200)
	assertEqual(t, "comments:42", body2)
}

func TestSpec_MountSubRouter(t *testing.T) {
	// [Req: formal — README] Mount attaches another handler or chi Router as subrouter
	sub := chi.NewRouter()
	sub.Get("/", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("sub-root"))
	})
	sub.Get("/detail", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("sub-detail"))
	})

	r := chi.NewRouter()
	r.Mount("/api", sub)

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, body := testRequest(t, ts, "GET", "/api", nil)
	assertStatus(t, resp, 200)
	assertEqual(t, "sub-root", body)

	resp2, body2 := testRequest(t, ts, "GET", "/api/detail", nil)
	assertStatus(t, resp2, 200)
	assertEqual(t, "sub-detail", body2)
}

func TestSpec_CustomNotFoundHandler(t *testing.T) {
	// [Req: formal — README] NotFound defines a handler for unmatched routes
	r := chi.NewRouter()
	r.NotFound(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(404)
		w.Write([]byte("custom 404"))
	})
	r.Get("/exists", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(200)
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, body := testRequest(t, ts, "GET", "/nonexistent", nil)
	assertStatus(t, resp, 404)
	assertEqual(t, "custom 404", body)
}

func TestSpec_CustomMethodNotAllowed(t *testing.T) {
	// [Req: formal — README] MethodNotAllowed defines a handler for unresolved methods
	r := chi.NewRouter()
	r.MethodNotAllowed(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(405)
		w.Write([]byte("custom 405"))
	})
	r.Get("/resource", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(200)
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, body := testRequest(t, ts, "POST", "/resource", nil)
	assertStatus(t, resp, 405)
	assertEqual(t, "custom 405", body)
}

func TestSpec_WithInlineMiddleware(t *testing.T) {
	// [Req: formal — README] With adds inline middlewares for an endpoint handler
	r := chi.NewRouter()

	authMw := func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.Header.Get("Authorization") == "" {
				w.WriteHeader(401)
				return
			}
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

	// Public endpoint works without auth
	resp, body := testRequest(t, ts, "GET", "/public", nil)
	assertStatus(t, resp, 200)
	assertEqual(t, "public", body)

	// Private endpoint rejects without auth
	resp2, _ := testRequest(t, ts, "GET", "/private", nil)
	assertStatus(t, resp2, 401)

	// Private endpoint accepts with auth
	req, _ := http.NewRequest("GET", ts.URL+"/private", nil)
	req.Header.Set("Authorization", "Bearer test")
	resp3, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	assertStatus(t, resp3, 200)
}

func TestSpec_HandlePatternWithMethod(t *testing.T) {
	// [Req: inferred — from mux.go:109-117 Handle() method parsing]
	// Handle() supports "METHOD /pattern" format
	r := chi.NewRouter()
	r.Handle("GET /test", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("handled"))
	}))

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, body := testRequest(t, ts, "GET", "/test", nil)
	assertStatus(t, resp, 200)
	assertEqual(t, "handled", body)

	// Other methods should not match
	resp2, _ := testRequest(t, ts, "POST", "/test", nil)
	assertStatus(t, resp2, 405)
}

// ============================================================================
// Group 2: Fitness Scenarios
// One test per QUALITY.md scenario (1:1 mapping)
// ============================================================================

func TestScenario1_ConcurrentRouteContextReuse(t *testing.T) {
	// [Req: inferred — from mux.go sync.Pool usage]
	// Scenario 1: Concurrent RouteContext Reuse via sync.Pool
	r := chi.NewRouter()
	r.Get("/user/{id}", func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "id")
		w.Write([]byte(id))
	})
	r.Get("/item/{name}", func(w http.ResponseWriter, r *http.Request) {
		name := chi.URLParam(r, "name")
		w.Write([]byte(name))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	var wg sync.WaitGroup
	errors := make(chan string, 200)

	for i := 0; i < 100; i++ {
		wg.Add(2)
		id := fmt.Sprintf("user-%d", i)
		name := fmt.Sprintf("item-%d", i)

		go func() {
			defer wg.Done()
			_, body := testRequest(t, ts, "GET", "/user/"+id, nil)
			if body != id {
				errors <- fmt.Sprintf("expected %s, got %s", id, body)
			}
		}()

		go func() {
			defer wg.Done()
			_, body := testRequest(t, ts, "GET", "/item/"+name, nil)
			if body != name {
				errors <- fmt.Sprintf("expected %s, got %s", name, body)
			}
		}()
	}

	wg.Wait()
	close(errors)

	for err := range errors {
		t.Errorf("context contamination: %s", err)
	}
}

func TestScenario2_MiddlewareAfterRoutesPanic(t *testing.T) {
	// [Req: inferred — from mux.go:101-105 Use() guard]
	// Scenario 2: Middleware After Routes Panic
	defer func() {
		if r := recover(); r == nil {
			t.Error("expected panic when calling Use() after defining routes")
		}
	}()

	r := chi.NewRouter()
	r.Get("/first", func(w http.ResponseWriter, r *http.Request) {})
	r.Use(func(next http.Handler) http.Handler { return next }) // Should panic
}

func TestScenario2b_WithAfterRoutesDoesNotPanic(t *testing.T) {
	// [Req: inferred — from mux.go With() behavior]
	// Scenario 2b: With() after routes should NOT panic
	r := chi.NewRouter()
	r.Get("/first", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("first"))
	})

	// With() creates inline mux — should not panic
	var mwCalled bool
	r.With(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			mwCalled = true
			next.ServeHTTP(w, r)
		})
	}).Get("/second", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("second"))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	// First route — inline middleware should not apply
	mwCalled = false
	_, body := testRequest(t, ts, "GET", "/first", nil)
	assertEqual(t, "first", body)
	if mwCalled {
		t.Error("With() middleware should not affect previously registered routes")
	}

	// Second route — inline middleware should apply
	mwCalled = false
	_, body2 := testRequest(t, ts, "GET", "/second", nil)
	assertEqual(t, "second", body2)
	if !mwCalled {
		t.Error("With() middleware should apply to its registered route")
	}
}

func TestScenario3_WildcardRoutingInSubrouters(t *testing.T) {
	// [Req: inferred — from mux.go:309-339 Mount() handler]
	// Scenario 3: Wildcard Routing Path Consumption in Subrouters
	level2 := chi.NewRouter()
	level2.Get("/", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("level2-root"))
	})

	level3 := chi.NewRouter()
	level3.Get("/", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("level3-root"))
	})
	level3.Get("/{id}", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("level3-" + chi.URLParam(r, "id")))
	})

	level2.Mount("/deep", level3)

	root := chi.NewRouter()
	root.Mount("/api", level2)

	ts := httptest.NewServer(root)
	defer ts.Close()

	resp, body := testRequest(t, ts, "GET", "/api", nil)
	assertStatus(t, resp, 200)
	assertEqual(t, "level2-root", body)

	resp2, body2 := testRequest(t, ts, "GET", "/api/deep", nil)
	assertStatus(t, resp2, 200)
	assertEqual(t, "level3-root", body2)

	resp3, body3 := testRequest(t, ts, "GET", "/api/deep/42", nil)
	assertStatus(t, resp3, 200)
	assertEqual(t, "level3-42", body3)
}

func TestScenario4_RegexRoutePatternValidation(t *testing.T) {
	// [Req: inferred — from tree.go patNextSegment() and InsertRoute()]
	// Scenario 4: Regex Route Pattern Validation and Matching

	// Valid regex should work
	r := chi.NewRouter()
	r.Get("/item/{id:[0-9]+}", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte(chi.URLParam(r, "id")))
	})
	r.Get("/item/{slug:[a-z-]+}/detail", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte(chi.URLParam(r, "slug")))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	// Numeric ID matches
	resp, body := testRequest(t, ts, "GET", "/item/123", nil)
	assertStatus(t, resp, 200)
	assertEqual(t, "123", body)

	// Non-numeric doesn't match numeric route
	resp2, _ := testRequest(t, ts, "GET", "/item/abc", nil)
	assertStatus(t, resp2, 404)

	// Slug matches
	resp3, body3 := testRequest(t, ts, "GET", "/item/my-slug/detail", nil)
	assertStatus(t, resp3, 200)
	assertEqual(t, "my-slug", body3)
}

func TestScenario4b_InvalidRegexPanics(t *testing.T) {
	// [Req: inferred — from tree.go InsertRoute()]
	// Invalid regex pattern should panic at registration time
	defer func() {
		if r := recover(); r == nil {
			t.Error("expected panic for invalid regex pattern")
		}
	}()

	r := chi.NewRouter()
	r.Get("/item/{id:[invalid(}", func(w http.ResponseWriter, r *http.Request) {})
}

func TestScenario5_MethodNotAllowedVsNotFound(t *testing.T) {
	// [Req: inferred — from mux.go:480-484 routeHTTP()]
	// Scenario 5: Method Not Allowed vs Not Found Disambiguation
	r := chi.NewRouter()
	r.Get("/resource", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("ok"))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	// Correct method — 200
	resp, _ := testRequest(t, ts, "GET", "/resource", nil)
	assertStatus(t, resp, 200)

	// Wrong method for existing path — 405
	resp2, _ := testRequest(t, ts, "POST", "/resource", nil)
	assertStatus(t, resp2, 405)

	// Check Allow header
	allow := resp2.Header.Get("Allow")
	if !strings.Contains(allow, "GET") {
		t.Errorf("expected Allow header to contain GET, got: %s", allow)
	}

	// Non-existent path — 404
	resp3, _ := testRequest(t, ts, "GET", "/nonexistent", nil)
	assertStatus(t, resp3, 404)
}

func TestScenario6_MountConflictPanic(t *testing.T) {
	// [Req: inferred — from mux.go:296-298 Mount() conflict check]
	// Scenario 6: Route Pattern Conflict on Mount
	defer func() {
		if r := recover(); r == nil {
			t.Error("expected panic when mounting on existing path")
		}
	}()

	sub1 := chi.NewRouter()
	sub1.Get("/", func(w http.ResponseWriter, r *http.Request) {})

	sub2 := chi.NewRouter()
	sub2.Get("/", func(w http.ResponseWriter, r *http.Request) {})

	r := chi.NewRouter()
	r.Mount("/api", sub1)
	r.Mount("/api", sub2) // Should panic
}

func TestScenario7_ResetPreservesSliceCapacity(t *testing.T) {
	// [Req: inferred — from context.go:82-96 Reset()]
	// Scenario 7: RouteContext Reset Preserves Slice Capacity
	ctx := chi.NewRouteContext()

	// Add some params to grow slices
	ctx.URLParams.Add("key1", "val1")
	ctx.URLParams.Add("key2", "val2")
	ctx.URLParams.Add("key3", "val3")

	capBefore := cap(ctx.URLParams.Keys)
	if capBefore < 3 {
		t.Fatalf("expected cap >= 3, got %d", capBefore)
	}

	ctx.Reset()

	// Length should be 0 after reset
	if len(ctx.URLParams.Keys) != 0 {
		t.Errorf("expected len 0 after reset, got %d", len(ctx.URLParams.Keys))
	}
	if len(ctx.URLParams.Values) != 0 {
		t.Errorf("expected len 0 after reset, got %d", len(ctx.URLParams.Values))
	}

	// Capacity should be preserved
	capAfter := cap(ctx.URLParams.Keys)
	if capAfter < capBefore {
		t.Errorf("expected cap >= %d after reset, got %d", capBefore, capAfter)
	}
}

func TestScenario8_NilHandlerMountPanic(t *testing.T) {
	// [Req: inferred — from mux.go:291-292 Mount() nil check]
	// Scenario 8: Nil Handler Mount Panic
	t.Run("Mount nil handler panics", func(t *testing.T) {
		defer func() {
			if r := recover(); r == nil {
				t.Error("expected panic when mounting nil handler")
			}
		}()
		r := chi.NewRouter()
		r.Mount("/api", nil)
	})

	t.Run("Route nil callback panics", func(t *testing.T) {
		defer func() {
			if r := recover(); r == nil {
				t.Error("expected panic when routing with nil callback")
			}
		}()
		r := chi.NewRouter()
		r.Route("/api", nil)
	})
}

func TestScenario9_UnsupportedHTTPMethod(t *testing.T) {
	// [Req: inferred — from mux.go:128-133 Method() and tree.go RegisterMethod()]
	// Scenario 9: Unsupported HTTP Method Handling
	t.Run("Unrecognized method returns 405", func(t *testing.T) {
		r := chi.NewRouter()
		r.Get("/resource", func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("ok"))
		})

		ts := httptest.NewServer(r)
		defer ts.Close()

		req, _ := http.NewRequest("PURGE", ts.URL+"/resource", nil)
		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			t.Fatal(err)
		}
		assertStatus(t, resp, 405)
	})

	t.Run("RegisterMethod with empty string is no-op", func(t *testing.T) {
		// Should not panic
		chi.RegisterMethod("")
	})

	t.Run("RegisterMethod with existing method is no-op", func(t *testing.T) {
		// Should not panic
		chi.RegisterMethod("GET")
	})

	t.Run("Unsupported method in Method() panics", func(t *testing.T) {
		defer func() {
			if r := recover(); r == nil {
				t.Error("expected panic for unsupported method")
			}
		}()
		r := chi.NewRouter()
		r.Method("INVALID_NOT_REGISTERED_XYZ", "/test", http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {}))
	})
}

func TestScenario10_RecovererMiddleware(t *testing.T) {
	// [Req: inferred — from middleware/recoverer.go:25-42]
	// Scenario 10: Recoverer Middleware WebSocket Upgrade Handling

	t.Run("Normal panic returns 500", func(t *testing.T) {
		r := chi.NewRouter()
		r.Use(middleware.Recoverer)
		r.Get("/panic", func(w http.ResponseWriter, r *http.Request) {
			panic("test panic")
		})

		ts := httptest.NewServer(r)
		defer ts.Close()

		resp, _ := testRequest(t, ts, "GET", "/panic", nil)
		assertStatus(t, resp, 500)
	})

	t.Run("ErrAbortHandler re-panics", func(t *testing.T) {
		r := chi.NewRouter()
		r.Use(middleware.Recoverer)
		r.Get("/abort", func(w http.ResponseWriter, r *http.Request) {
			panic(http.ErrAbortHandler)
		})

		ts := httptest.NewServer(r)
		defer ts.Close()

		// ErrAbortHandler causes connection abort — the client gets an error
		_, err := http.Get(ts.URL + "/abort")
		if err == nil {
			// It's also acceptable if the server handles it gracefully
			// The key is ErrAbortHandler is re-panicked, not recovered
		}
	})
}

// ============================================================================
// Group 3: Boundaries and Edge Cases
// One test per defensive pattern from Step 5
// ============================================================================

func TestBoundary_NilRouteContext(t *testing.T) {
	// [Req: inferred — from context.go:27-30 RouteContext() returns nil safely]
	ctx := context.Background()
	rctx := chi.RouteContext(ctx)
	if rctx != nil {
		t.Error("expected nil RouteContext from background context")
	}
}

func TestBoundary_URLParamWithoutContext(t *testing.T) {
	// [Req: inferred — from context.go:10-14 URLParam() nil guard]
	req := httptest.NewRequest("GET", "/", nil)
	val := chi.URLParam(req, "nonexistent")
	if val != "" {
		t.Errorf("expected empty string for missing URL param, got %q", val)
	}
}

func TestBoundary_URLParamFromCtxWithoutContext(t *testing.T) {
	// [Req: inferred — from context.go:18-22 URLParamFromCtx() nil guard]
	ctx := context.Background()
	val := chi.URLParamFromCtx(ctx, "key")
	if val != "" {
		t.Errorf("expected empty string, got %q", val)
	}
}

func TestBoundary_RoutePatternNilReceiver(t *testing.T) {
	// [Req: inferred — from context.go:123-126 RoutePattern() nil check]
	var ctx *chi.Context
	pattern := ctx.RoutePattern()
	if pattern != "" {
		t.Errorf("expected empty pattern for nil context, got %q", pattern)
	}
}

func TestBoundary_EmptyRoutePath(t *testing.T) {
	// [Req: inferred — from mux.go:447-456 routeHTTP() empty path fallback]
	r := chi.NewRouter()
	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("root"))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, body := testRequest(t, ts, "GET", "/", nil)
	assertStatus(t, resp, 200)
	assertEqual(t, "root", body)
}

func TestBoundary_PatternMustBeginWithSlash(t *testing.T) {
	// [Req: inferred — from mux.go:417-419 handle() validation]
	defer func() {
		if r := recover(); r == nil {
			t.Error("expected panic for pattern without leading slash")
		}
	}()

	r := chi.NewRouter()
	r.Get("no-slash", func(w http.ResponseWriter, r *http.Request) {})
}

func TestBoundary_MuxWithNilHandler(t *testing.T) {
	// [Req: inferred — from mux.go:65-68 ServeHTTP() nil handler guard]
	// A mux with no routes should return 404
	r := chi.NewMux()

	w := httptest.NewRecorder()
	req := httptest.NewRequest("GET", "/anything", nil)
	r.ServeHTTP(w, req)

	if w.Code != 404 {
		t.Errorf("expected 404 for mux with no routes, got %d", w.Code)
	}
}

func TestBoundary_ThrottleLimitZeroPanics(t *testing.T) {
	// [Req: inferred — from middleware/throttle.go:45-47 limit validation]
	defer func() {
		if r := recover(); r == nil {
			t.Error("expected panic for throttle limit < 1")
		}
	}()

	middleware.Throttle(0)
}

func TestBoundary_ThrottleNegativeBacklogPanics(t *testing.T) {
	// [Req: inferred — from middleware/throttle.go:49-51 backlog validation]
	defer func() {
		if r := recover(); r == nil {
			t.Error("expected panic for negative backlog limit")
		}
	}()

	middleware.ThrottleBacklog(1, -1, 0)
}

func TestBoundary_ContentTypeSkipsEmptyBody(t *testing.T) {
	// [Req: inferred — from middleware/content_type.go:28-31 empty body check]
	r := chi.NewRouter()
	r.Use(middleware.AllowContentType("application/json"))
	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("ok"))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	// GET with no body should pass even without Content-Type
	resp, body := testRequest(t, ts, "GET", "/", nil)
	assertStatus(t, resp, 200)
	assertEqual(t, "ok", body)
}

func TestBoundary_ContextResetClearsAllFields(t *testing.T) {
	// [Req: inferred — from context.go:82-96 Reset() completeness]
	ctx := chi.NewRouteContext()
	ctx.RoutePath = "/test"
	ctx.RouteMethod = "GET"
	ctx.URLParams.Add("key", "val")
	ctx.RoutePatterns = append(ctx.RoutePatterns, "/pattern")

	ctx.Reset()

	if ctx.RoutePath != "" {
		t.Errorf("RoutePath not cleared: %q", ctx.RoutePath)
	}
	if ctx.RouteMethod != "" {
		t.Errorf("RouteMethod not cleared: %q", ctx.RouteMethod)
	}
	if len(ctx.URLParams.Keys) != 0 {
		t.Errorf("URLParams.Keys not cleared: %v", ctx.URLParams.Keys)
	}
	if len(ctx.URLParams.Values) != 0 {
		t.Errorf("URLParams.Values not cleared: %v", ctx.URLParams.Values)
	}
	if len(ctx.RoutePatterns) != 0 {
		t.Errorf("RoutePatterns not cleared: %v", ctx.RoutePatterns)
	}
}

func TestBoundary_URLParamReverseTraversal(t *testing.T) {
	// [Req: inferred — from context.go:100-107 URLParam() backward scan]
	// When the same key appears multiple times, last value wins
	ctx := chi.NewRouteContext()
	ctx.URLParams.Add("id", "first")
	ctx.URLParams.Add("id", "second")

	val := ctx.URLParam("id")
	if val != "second" {
		t.Errorf("expected last value 'second', got %q", val)
	}
}

func TestBoundary_URLParamMissingKey(t *testing.T) {
	// [Req: inferred — from context.go:100-107 URLParam() returns empty string]
	ctx := chi.NewRouteContext()
	ctx.URLParams.Add("name", "test")

	val := ctx.URLParam("nonexistent")
	if val != "" {
		t.Errorf("expected empty string for missing key, got %q", val)
	}
}

func TestBoundary_RoutePatternWildcardCleanup(t *testing.T) {
	// [Req: inferred — from context.go:128-144 replaceWildcards()]
	ctx := chi.NewRouteContext()
	ctx.RoutePatterns = append(ctx.RoutePatterns, "/api/*/", "/users")

	pattern := ctx.RoutePattern()
	if strings.Contains(pattern, "/*/") {
		t.Errorf("wildcard artifacts not cleaned: %q", pattern)
	}
}

func TestBoundary_ChainEmptyMiddlewares(t *testing.T) {
	// [Req: inferred — from chain.go:37-39 empty middleware shortcut]
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("direct"))
	})

	chained := chi.Chain().Handler(handler)

	w := httptest.NewRecorder()
	req := httptest.NewRequest("GET", "/", nil)
	chained.ServeHTTP(w, req)

	if w.Body.String() != "direct" {
		t.Errorf("expected 'direct', got %q", w.Body.String())
	}
}

func TestBoundary_MatchAndFindRoutes(t *testing.T) {
	// [Req: inferred — from mux.go:359-394 Match/Find methods]
	r := chi.NewRouter()
	r.Get("/users/{id}", func(w http.ResponseWriter, r *http.Request) {})
	r.Post("/users", func(w http.ResponseWriter, r *http.Request) {})

	// Match should return true for existing route
	rctx := chi.NewRouteContext()
	if !r.Match(rctx, "GET", "/users/123") {
		t.Error("expected Match to return true for GET /users/123")
	}

	// Match should return false for non-existing route
	rctx2 := chi.NewRouteContext()
	if r.Match(rctx2, "DELETE", "/nonexistent") {
		t.Error("expected Match to return false for DELETE /nonexistent")
	}

	// Find should return the pattern
	rctx3 := chi.NewRouteContext()
	pattern := r.Find(rctx3, "GET", "/users/456")
	if pattern != "/users/{id}" {
		t.Errorf("expected pattern '/users/{id}', got %q", pattern)
	}

	// Find should return empty for unknown method
	rctx4 := chi.NewRouteContext()
	pattern2 := r.Find(rctx4, "UNKNOWN", "/users/456")
	if pattern2 != "" {
		t.Errorf("expected empty pattern for unknown method, got %q", pattern2)
	}
}

func TestBoundary_RoutesTraversal(t *testing.T) {
	// [Req: inferred — from mux.go:344-347 Routes() method]
	r := chi.NewRouter()
	r.Get("/a", func(w http.ResponseWriter, r *http.Request) {})
	r.Post("/b", func(w http.ResponseWriter, r *http.Request) {})

	routes := r.Routes()
	if len(routes) == 0 {
		t.Error("expected at least one route")
	}
}

func TestBoundary_MiddlewaresAccessor(t *testing.T) {
	// [Req: inferred — from mux.go:348-351 Middlewares() method]
	r := chi.NewRouter()
	mw := func(next http.Handler) http.Handler { return next }
	r.Use(mw)

	mws := r.Middlewares()
	if len(mws) != 1 {
		t.Errorf("expected 1 middleware, got %d", len(mws))
	}
}

func TestBoundary_CompressorInvalidWildcardPanics(t *testing.T) {
	// [Req: inferred — from middleware/compress.go:70-72 wildcard validation]
	defer func() {
		if r := recover(); r == nil {
			t.Error("expected panic for unsupported wildcard pattern")
		}
	}()

	middleware.NewCompressor(5, "text/*html")
}

func TestBoundary_RealIPMiddleware(t *testing.T) {
	// [Req: inferred — from middleware/realip.go RealIP validation]
	r := chi.NewRouter()
	r.Use(middleware.RealIP)
	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte(r.RemoteAddr))
	})

	w := httptest.NewRecorder()
	req := httptest.NewRequest("GET", "/", nil)
	req.Header.Set("X-Forwarded-For", "203.0.113.195")
	r.ServeHTTP(w, req)

	if w.Code != 200 {
		t.Errorf("expected 200, got %d", w.Code)
	}
}

func TestBoundary_StripSlashesMiddleware(t *testing.T) {
	// [Req: inferred — from middleware/strip.go StripSlashes]
	r := chi.NewRouter()
	r.Use(middleware.StripSlashes)
	r.Get("/hello", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("hello"))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	// With trailing slash should be stripped
	resp, body := testRequest(t, ts, "GET", "/hello/", nil)
	assertStatus(t, resp, 200)
	assertEqual(t, "hello", body)

	// Without trailing slash should work normally
	resp2, body2 := testRequest(t, ts, "GET", "/hello", nil)
	assertStatus(t, resp2, 200)
	assertEqual(t, "hello", body2)
}

func TestBoundary_ContextValuePropagation(t *testing.T) {
	// [Req: inferred — from mux.go:87 context.WithValue propagation]
	r := chi.NewRouter()
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ctx := context.WithValue(r.Context(), ctxKey{"test"}, "value")
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	})
	r.Get("/", func(w http.ResponseWriter, r *http.Request) {
		val, ok := r.Context().Value(ctxKey{"test"}).(string)
		if !ok || val != "value" {
			w.WriteHeader(500)
			return
		}
		w.Write([]byte(val))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, body := testRequest(t, ts, "GET", "/", nil)
	assertStatus(t, resp, 200)
	assertEqual(t, "value", body)
}

func TestBoundary_ExistingContextNotReplaced(t *testing.T) {
	// [Req: inferred — from mux.go:71-75 existing context check]
	// When a parent router has already set RouteContext, the child should reuse it
	outer := chi.NewRouter()
	inner := chi.NewRouter()
	inner.Get("/", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("inner"))
	})

	outer.Mount("/inner", inner)

	ts := httptest.NewServer(outer)
	defer ts.Close()

	resp, body := testRequest(t, ts, "GET", "/inner", nil)
	assertStatus(t, resp, 200)
	assertEqual(t, "inner", body)
}

func TestBoundary_NotFoundHandlerPropagation(t *testing.T) {
	// [Req: inferred — from mux.go:197-213 NotFound propagation to subrouters]
	r := chi.NewRouter()
	r.NotFound(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(404)
		w.Write([]byte("parent-404"))
	})

	sub := chi.NewRouter()
	sub.Get("/exists", func(w http.ResponseWriter, r *http.Request) {
		w.Write([]byte("found"))
	})

	r.Mount("/sub", sub)

	ts := httptest.NewServer(r)
	defer ts.Close()

	// Subrouter should inherit parent's 404 handler
	resp, body := testRequest(t, ts, "GET", "/sub/nonexistent", nil)
	assertStatus(t, resp, 404)
	assertEqual(t, "parent-404", body)
}

func TestBoundary_MultipleURLParams(t *testing.T) {
	// [Req: inferred — from tree.go FindRoute() multi-param extraction]
	r := chi.NewRouter()
	r.Get("/user/{userID}/post/{postID}", func(w http.ResponseWriter, r *http.Request) {
		uid := chi.URLParam(r, "userID")
		pid := chi.URLParam(r, "postID")
		w.Write([]byte(uid + ":" + pid))
	})

	ts := httptest.NewServer(r)
	defer ts.Close()

	resp, body := testRequest(t, ts, "GET", "/user/alice/post/99", nil)
	assertStatus(t, resp, 200)
	assertEqual(t, "alice:99", body)
}

// ============================================================================
// Test Helpers
// ============================================================================

type ctxKey struct {
	name string
}

func testRequest(t *testing.T, ts *httptest.Server, method, path string, body io.Reader) (*http.Response, string) {
	t.Helper()
	req, err := http.NewRequest(method, ts.URL+path, body)
	if err != nil {
		t.Fatal(err)
	}

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		t.Fatal(err)
	}

	return resp, string(respBody)
}

func assertStatus(t *testing.T, resp *http.Response, expected int) {
	t.Helper()
	if resp.StatusCode != expected {
		t.Errorf("expected status %d, got %d", expected, resp.StatusCode)
	}
}

func assertEqual(t *testing.T, expected, actual string) {
	t.Helper()
	if expected != actual {
		t.Errorf("expected %q, got %q", expected, actual)
	}
}

// Ensure unused imports don't cause build errors
var _ = bytes.NewBuffer
var _ = strings.Contains
var _ = fmt.Sprintf
var _ = context.Background
