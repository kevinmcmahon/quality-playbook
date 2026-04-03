# NSQ-48 Code Review: apps/nsq_to_file/file_logger.go

## file_logger.go

- **Line 160-165:** BUG (Medium). `Close()` calls `f.out.Sync()` on line 160 **before** `f.gzipWriter.Close()` on line 163. The gzip `Close()` writes the gzip footer (trailer with CRC32 and size) to `f.out`. This final data is never `fsync`'d — only `f.out.Close()` follows, which does not guarantee durability. On a crash or power loss immediately after `Close()` returns, the gzip file on disk may be missing its footer, rendering the entire file unreadable by standard gzip decoders. The `Sync()` call should be moved to after `gzipWriter.Close()`:
  ```go
  if f.gzipWriter != nil {
      f.gzipWriter.Close()
  }
  f.out.Sync()
  f.out.Close()
  ```

- **Line 205 / Line 162:** QUESTION (Low). `Close()` sets `f.out = nil` on line 205 but never sets `f.gzipWriter = nil`. Between a `Close()` call and the next `updateFile()`, `f.gzipWriter` holds a reference to a closed writer. If `Sync()` (line 214-220) were ever called in this window, it would call `Flush()` on the closed gzip writer. Current control flow in `router()` appears to prevent this (Sync is only called when `pos > 0`, which requires a prior write, which requires `updateFile()` to have run). However, the stale reference is fragile — any future refactoring that calls `Sync()` without a preceding `updateFile()` would hit this. Setting `f.gzipWriter = nil` in `Close()` would make this safe.

- **Line 327:** QUESTION (Low). `gzip.NewWriterLevel` error is discarded with `_`. While `GZIPLevel` is validated at startup in `nsq_to_file.go:99-100` (must be 1-9), silently ignoring the error means a nil `gzipWriter` and nil-pointer dereference if the validation were ever relaxed or bypassed. Defensive code would check the error.

- **Line 345-353:** QUESTION (Low). `exclusiveRename` uses `os.Link()` + `os.Remove()` to simulate an atomic exclusive rename. If `Link` succeeds (line 345) but `Remove` fails (line 350), both `src` and `dst` exist as hard links to the same inode. The caller in `Close()` (line 176-179) handles this by calling `log.Fatalf`, so data is not silently corrupted, but the source file is left behind. On filesystems that don't support hard links (e.g., some network mounts), `Link` will always fail, making the entire WorkDir feature non-functional with no clear error guidance.

## Summary

| Severity | Count |
|----------|-------|
| BUG      | 1     |
| QUESTION | 3     |

**Overall assessment:** FIX FIRST — The gzip sync ordering bug (line 160-165) is a real data durability issue that should be fixed before shipping. The remaining items are low-severity but worth addressing.
