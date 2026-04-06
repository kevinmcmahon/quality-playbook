git checkout d3d0bbf

Review the following files against this requirement principle. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement principle:**
Graceful shutdown must close all active connections across all connection types. If different client types connect through different paths, shutdown must reach all of them.

Also report any other bugs you find in these files. This principle is not the only thing worth checking.

Files to review:
- nsqd/nsqd.go
- nsqd/tcp.go
- nsqd/protocol_v2.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_abstract/NSQ-47_review.md

git checkout master
