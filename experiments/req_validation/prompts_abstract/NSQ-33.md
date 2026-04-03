git checkout 51b270f

Review the following files against this requirement principle. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement principle:**
All mutating endpoints must enforce authorization consistently. If some admin endpoints check permissions but others skip the check, unauthenticated users can perform administrative operations through the unguarded endpoints.

Also report any other bugs you find in these files. This principle is not the only thing worth checking.

Files to review:
- nsqadmin/http.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_abstract/NSQ-33_review.md

git checkout master
