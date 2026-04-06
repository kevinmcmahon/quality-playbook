git checkout 3ee16a5

Review the following files against this requirement principle. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement principle:**
Protocol negotiation responses must confirm actual negotiated values, not defaults. When a client requests a specific parameter and the server accepts it, the response must reflect the agreed value.

Also report any other bugs you find in these files. This principle is not the only thing worth checking.

Files to review:
- nsqd/protocol_v2.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_abstract/NSQ-55_review.md

git checkout master
