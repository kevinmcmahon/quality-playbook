git checkout 1d183d9

Review the following files against this specific requirement. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement to check:**
The HTTP client used for nsqauth (auth server) requests must use the TLS configuration from --tls-root-ca-file, not the system default CAs. If a custom root CA is configured for the cluster, auth requests must use that same CA. Check whether the auth HTTP client's TLS config includes the configured RootCAs.

Also report any other bugs you find in these files. This requirement is not the only thing worth checking.

Files to review:
- internal/auth/authorizations.go
- nsqd/nsqd.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_specific/NSQ-44_review.md

git checkout master
