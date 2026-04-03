git checkout ac1627bba

Review the following files against this specific requirement. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement to check:**
NSQD.Exit() must close ALL active TCP connections (both producer and consumer), not just close the listener. Goroutines blocked on conn.Read() will hang indefinitely if the connection is not explicitly closed. Check that Exit() iterates over active connections and closes each one.

Also report any other bugs you find in these files. This requirement is not the only thing worth checking.

Files to review:
- nsqd/nsqd.go
- nsqd/tcp.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_specific/NSQ-04_review.md

git checkout master
