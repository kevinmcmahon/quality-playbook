git checkout d3d0bbf

Review the following files for bugs. Be thorough — read every function body, check boundary conditions, trace error paths, look for race conditions and resource leaks. Report only real bugs, not style issues.

Files to review:
- nsqd/nsqd.go
- nsqd/tcp.go
- nsqd/protocol_v2.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_control/NSQ-47_review.md

git checkout master
