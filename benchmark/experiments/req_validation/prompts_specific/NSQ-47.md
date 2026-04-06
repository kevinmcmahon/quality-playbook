git checkout d3d0bbf

Review the following files against this specific requirement. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement to check:**
NSQD.Exit() must close all active TCP client connections (consumer connections, not just producer connections). Clients remaining connected after shutdown prevent clean process exit. Check whether Exit() reaches consumer connections or only producer connections.

Also report any other bugs you find in these files. This requirement is not the only thing worth checking.

Files to review:
- nsqd/nsqd.go
- nsqd/tcp.go
- nsqd/protocol_v2.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_specific/NSQ-47_review.md

git checkout master
