git checkout 62c385896

Review the following files against this requirement principle. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement principle:**
Protocol commands with out-of-range numeric parameters should produce recoverable errors or clamped values, not fatal errors that terminate the connection. Clients should not be disconnected for providing values outside an allowed range.

Also report any other bugs you find in these files. This principle is not the only thing worth checking.

Files to review:
- nsqd/protocol_v2.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_abstract/NSQ-14_review.md

git checkout master
