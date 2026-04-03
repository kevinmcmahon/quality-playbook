git checkout 51b270f

Review the following files against this specific requirement. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement to check:**
All mutating admin endpoints in nsqadmin must call isAuthorizedAdminRequest() before processing. Check that tombstoneNodeForTopicHandler has the same authorization check as the other admin mutation handlers (delete topic, delete channel, pause, unpause).

Also report any other bugs you find in these files. This requirement is not the only thing worth checking.

Files to review:
- nsqadmin/http.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_specific/NSQ-33_review.md

git checkout master
