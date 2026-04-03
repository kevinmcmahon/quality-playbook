git checkout cb83885

Review the following files against this specific requirement. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement to check:**
E2E processing latency percentile configuration values must be validated at parse time to be in the range (0, 1.0]. Values like 0, negative numbers, or values > 1.0 (e.g. 100.0) must be rejected with a clear error at startup. Check whether the config parsing validates this constraint.

Also report any other bugs you find in these files. This requirement is not the only thing worth checking.

Files to review:
- nsqd/nsqd.go
- nsqd/options.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_specific/NSQ-36_review.md

git checkout master
