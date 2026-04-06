git checkout e8e1040d4

Review the following files against this requirement principle. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement principle:**
Protocol negotiation must honor the client's requested parameters within configured bounds. The server must not substitute defaults when the client provides a valid value within the allowed range.

Also report any other bugs you find in these files. This principle is not the only thing worth checking.

Files to review:
- nsqd/protocol_v2.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_abstract/NSQ-19_review.md

git checkout master
