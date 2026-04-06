git checkout 9faeb4a84

Review the following files against this requirement principle. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement principle:**
Server shutdown must wait for all spawned handler goroutines to complete before returning. Goroutines that outlive their parent server can access freed resources and cause data races.

Also report any other bugs you find in these files. This principle is not the only thing worth checking.

Files to review:
- internal/protocol/tcp_server.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_abstract/NSQ-22_review.md

git checkout master
