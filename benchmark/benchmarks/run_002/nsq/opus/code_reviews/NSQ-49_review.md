# NSQ-49 Code Review: apps/nsq_to_file/file_logger.go

## file_logger.go

- **Line 194:** [BUG] (High) `Close()` returns early without setting `f.out = nil`. When `WorkDir != OutputDir` and `exclusiveRename` succeeds, the method returns at line 194 but `f.out = nil` (line 222) is never reached. This leaves `f.out` pointing to an already-closed file descriptor. Consequences: (1) `needsRotation()` (line 256) sees `f.out != nil` and skips the "file not open" rotation trigger; (2) the next call to `Close()` (e.g., from `updateFile()` line 295 or the `closeFile` path in `router()` line 151) will attempt to `Sync()` and `Close()` an already-closed `*os.File`, producing errors or undefined behavior. Fix: set `f.out = nil` before the `return` on line 194, or move `f.out = nil` before the rename block.

- **Line 339-340:** [BUG] (High) Missing `os.Exit(1)` after FATAL log on `Stat()` failure. Every other FATAL log in this file is immediately followed by `os.Exit(1)`, but line 339 only logs and continues. On error, `fi` is `nil` (it's an `os.FileInfo` interface), so `fi.Size()` on line 341 will panic with a nil pointer dereference. Fix: add `os.Exit(1)` after line 339, consistent with the rest of the file.

- **Line 206:** [QUESTION] (Low) Infinite loop in revision-bump rename with no upper bound. If the output directory has a huge number of existing revisions (or a filesystem error consistently returns `os.IsExist`), this `for` loop will spin indefinitely. This is unlikely in practice but there is no circuit-breaker or maximum revision limit. The same pattern appears in `updateFile()` at line 299. May be intentional given the `os.Exit` on non-IsExist errors.

- **Line 371-379:** [QUESTION] (Medium) `exclusiveRename()` is not atomic if `os.Remove` fails after `os.Link` succeeds. If `Link(src, dst)` succeeds but `Remove(src)` fails, both `src` and `dst` point to the same file (hard link). The caller at line 193-198 will hit the FATAL exit, but the destination file has already been created. On restart, the file exists in the output directory and will be skipped via the revision-bump logic, so data is not lost, but the source file also remains in the work directory and could be re-processed.

## Summary

| Severity | Count |
|----------|-------|
| BUG (High) | 2 |
| QUESTION (Medium) | 1 |
| QUESTION (Low) | 1 |

**Overall assessment: FIX FIRST** — The two high-severity bugs are real correctness issues. The missing `os.Exit(1)` at line 339 will cause a guaranteed panic on stat failure. The missing `f.out = nil` at line 194 causes double-close of file descriptors when using separate work/output directories.
