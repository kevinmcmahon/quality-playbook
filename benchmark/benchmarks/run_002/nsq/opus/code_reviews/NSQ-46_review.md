# Code Review: apps/nsqd/main_test.go

## apps/nsqd/main_test.go

- **Line 26:** **BUG** (Medium). `toml.DecodeReader(f, &cfg)` returns `(toml.MetaData, error)` but both return values are discarded. If the example config file has a syntax error or cannot be decoded, the test silently continues with a zero-valued `cfg`, and the final assertion on `TLSMinVersion` would pass or fail for the wrong reason. The error should be checked with `t.Fatalf` so a decode failure is caught immediately rather than masked.

- **Line 25-26:** **BUG** (Low). The file handle `f` opened by `os.Open` is never closed. While this is a minor resource leak in a test (cleaned up on process exit), it is still a correctness defect — the file descriptor is held open for the lifetime of the test process. A `defer f.Close()` should follow the error check on line 23-25.

- **Line 30:** **BUG** (Medium). `nsqd.New(opts)` returns `(*NSQD, error)` but both return values are discarded. If `New` fails (e.g., due to invalid resolved options, port binding issues, or TLS configuration errors), the test silently ignores the failure and proceeds to assert on `opts.TLSMinVersion`, which may have been set correctly even though the NSQD instance could not be created. The error should be checked. Additionally, if `New` succeeds, the returned `*NSQD` is never closed, potentially leaking goroutines and listeners.

## Summary

| Severity | Count |
|----------|-------|
| Medium   | 2     |
| Low      | 1     |

- **Total findings:** 3
- **Overall assessment:** FIX FIRST — Two unchecked errors mean the test can pass while masking real failures in config parsing or NSQD initialization.
