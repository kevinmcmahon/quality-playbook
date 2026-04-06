# NSQ-50 Code Review: apps/nsq_to_file/nsq_to_file.go

Reviewed files:
- `apps/nsq_to_file/nsq_to_file.go`
- `apps/nsq_to_file/file_logger.go` (supporting context)
- `apps/nsq_to_file/topic_discoverer.go` (supporting context)
- `apps/nsq_to_file/options.go` (supporting context)

---

### apps/nsq_to_file/nsq_to_file.go

- **Line 139-140:** BUG (Medium). `hupChan` and `termChan` are created as unbuffered channels (`make(chan os.Signal)`) and passed to `signal.Notify`. The Go `signal.Notify` documentation states: "Package signal will not block sending to c: the caller must ensure that c has sufficient buffer space to keep up with the expected signal rate. For a channel used for notification of just one signal value, a buffer of size 1 is sufficient." With unbuffered channels, signals arriving when the receiver is not in a ready `select` case will be silently dropped. This means a SIGHUP or SIGTERM/SIGINT could be lost if the `TopicDiscoverer.run()` loop is busy processing a ticker or updateTopics call at that moment. Both channels should be `make(chan os.Signal, 1)`.

- **Line 134:** BUG (Low). `cfgFlag.Set(opt)` return value is discarded. If a user passes an invalid `--consumer-opt` value, the error is silently ignored and the consumer runs with unexpected default configuration. The error should be checked and the program should exit with a diagnostic message, consistent with how other invalid flags are handled (lines 100-121).

- **Line 32:** QUESTION (Low). `flag.NewFlagSet("nsqd", flag.ExitOnError)` uses the name `"nsqd"` but this is the `nsq_to_file` utility. This causes `--help` output to show `Usage of nsqd:` instead of `Usage of nsq_to_file:`. Unclear if intentional or a copy-paste error.

### apps/nsq_to_file/file_logger.go

- **Line 348-349:** BUG (High). After `f.out.Stat()` fails, the code logs a FATAL message but does NOT call `os.Exit(1)`, unlike every other FATAL log point in this file (lines 119-120, 124-125, 139-140, 171, 177, 182, 198-199, 216-217, 299-300, 340-341). Execution falls through to line 350 (`f.filesize = fi.Size()`) where `fi` is nil, causing a nil pointer dereference panic. Expected: `os.Exit(1)` after the log statement on line 349, consistent with all other fatal error paths.

- **Line 196:** BUG (Medium). In `Close()`, when `WorkDir != OutputDir` and the optimistic `exclusiveRename` succeeds, the function returns early at line 196 without setting `f.out = nil` (which happens at line 224). This leaves `f.out` referencing a closed `*os.File`. Subsequent calls to `needsRotation()` (line 258) see `f.out != nil` and may skip rotation. On the HUP path (router line 100-101, 152-154), after `Close()` completes, the loop continues; the next incoming message calls `needsRotation()` which sees `f.out` as non-nil, and if the filename hasn't changed, returns false. The subsequent `f.Write()` then writes to the closed file via `f.writer` (which also references the closed gzip writer or closed os.File), causing a write error and `os.Exit(1)`. Expected: `f.out = nil` should be set before the early return at line 196, or the nil assignment should be moved before the rename block.

### apps/nsq_to_file/topic_discoverer.go

- **Line 87-89:** QUESTION (Low). The HUP handler sends to each `fl.hupChan` synchronously in a loop. Since `hupChan` is unbuffered (`make(chan bool)`, file_logger.go line 59), if any FileLogger's router goroutine is busy (e.g., performing a long sync or write), the send blocks, preventing subsequent FileLoggers from receiving the HUP and also blocking the main select loop (no SIGTERM handling possible during this time). With many topics and slow I/O, this could cause noticeable delays. Unclear if this is an accepted design tradeoff.

---

### Summary

| Severity | Count |
|----------|-------|
| BUG (High) | 1 |
| BUG (Medium) | 2 |
| BUG (Low) | 1 |
| QUESTION | 2 |

**Files with no findings:** `options.go`, `strftime.go`

**Overall assessment:** FIX FIRST — The nil pointer panic on stat failure (file_logger.go:348) is a crash bug that should be fixed. The `f.out` not being nil'd on early return (file_logger.go:196) causes data loss on HUP when using a work directory. The unbuffered signal channels (nsq_to_file.go:139-140) can silently drop signals.
