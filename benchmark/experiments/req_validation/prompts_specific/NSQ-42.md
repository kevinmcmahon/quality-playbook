git checkout 47034fb

Review the following files against this specific requirement. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement to check:**
nsqadmin node list links must bracket IPv6 addresses when constructing URLs. Without brackets, URLs like http://::1:4171/stats produce broken links. Check all places where node addresses are embedded in HTML links or URLs.

Also report any other bugs you find in these files. This requirement is not the only thing worth checking.

Files to review:
- nsqadmin/http.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_specific/NSQ-42_review.md

git checkout master
