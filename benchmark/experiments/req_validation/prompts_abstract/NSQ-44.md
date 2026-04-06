git checkout 1d183d9

Review the following files against this requirement principle. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement principle:**
Outbound TLS connections must use the configured certificate authority, not system defaults. When a service is configured with a custom CA, all outbound TLS connections from that service must honor that configuration.

Also report any other bugs you find in these files. This principle is not the only thing worth checking.

Files to review:
- internal/auth/authorizations.go
- nsqd/nsqd.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_abstract/NSQ-44_review.md

git checkout master
