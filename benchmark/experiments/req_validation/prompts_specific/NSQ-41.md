git checkout 77a46db

Review the following files against this specific requirement. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement to check:**
When -tls-required is set to true, the -tls-client-auth-policy flag must not silently override or downgrade that setting. If an operator explicitly sets -tls-required=true but doesn't set -tls-client-auth-policy, the TLS requirement must be preserved. Check the flag interaction logic in New().

Also report any other bugs you find in these files. This requirement is not the only thing worth checking.

Files to review:
- nsqd/nsqd.go
- nsqd/options.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_specific/NSQ-41_review.md

git checkout master
