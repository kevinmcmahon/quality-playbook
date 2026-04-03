git checkout 9faeb4a84

Review the following files against this specific requirement. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement to check:**
TCPServer must track all spawned per-connection handler goroutines using a WaitGroup or equivalent, and wait for them to complete during shutdown. Currently, the server returns from its serve loop without waiting for handlers, allowing goroutines to access freed resources.

Also report any other bugs you find in these files. This requirement is not the only thing worth checking.

Files to review:
- internal/protocol/tcp_server.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_specific/NSQ-22_review.md

git checkout master
