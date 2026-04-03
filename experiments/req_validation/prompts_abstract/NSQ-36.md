git checkout cb83885

Review the following files against this requirement principle. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement principle:**
Configuration values with domain-specific constraints must be validated at parse time, not silently accepted. Percentile values, ratios, and other bounded parameters must be range-checked before use.

Also report any other bugs you find in these files. This principle is not the only thing worth checking.

Files to review:
- nsqd/nsqd.go
- nsqd/options.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_abstract/NSQ-36_review.md

git checkout master
