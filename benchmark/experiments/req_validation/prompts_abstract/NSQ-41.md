git checkout 77a46db

Review the following files against this requirement principle. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement principle:**
When multiple configuration flags control related security behavior, one flag must not silently override another. The interaction between security flags must preserve explicit operator intent.

Also report any other bugs you find in these files. This principle is not the only thing worth checking.

Files to review:
- nsqd/nsqd.go
- nsqd/options.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_abstract/NSQ-41_review.md

git checkout master
