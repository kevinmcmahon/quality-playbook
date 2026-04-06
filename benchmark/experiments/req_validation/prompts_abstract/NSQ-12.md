git checkout 6774510b9

Review the following files against this requirement principle. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement principle:**
Configuration values of zero must mean 'disabled/none', not 'zero-sized'. When a capacity parameter is set to 0, the feature should be bypassed entirely rather than creating a zero-capacity resource that blocks.

Also report any other bugs you find in these files. This principle is not the only thing worth checking.

Files to review:
- nsqd/channel.go
- nsqd/topic.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_abstract/NSQ-12_review.md

git checkout master
