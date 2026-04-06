git checkout 62c385896

Review the following files against this specific requirement. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement to check:**
When a REQ command specifies a timeout outside the valid range [0, MaxReqTimeout], the server must clamp the value to the valid range and continue processing. It must NOT send E_INVALID (a fatal protocol error) that disconnects the client. Out-of-range parameters are a recoverable condition, not a protocol violation.

Also report any other bugs you find in these files. This requirement is not the only thing worth checking.

Files to review:
- nsqd/protocol_v2.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_specific/NSQ-14_review.md

git checkout master
