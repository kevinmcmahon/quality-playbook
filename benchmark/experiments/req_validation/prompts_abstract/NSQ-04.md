git checkout ac1627bba

Review the following files against this requirement principle. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement principle:**
Graceful shutdown must release all held resources. When a server stops, every active connection must be closed — stopping the listener alone is insufficient if existing connections remain open.

Also report any other bugs you find in these files. This principle is not the only thing worth checking.

Files to review:
- nsqd/nsqd.go
- nsqd/tcp.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_abstract/NSQ-04_review.md

git checkout master
