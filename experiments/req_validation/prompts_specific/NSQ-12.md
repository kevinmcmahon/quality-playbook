git checkout 6774510b9

Review the following files against this specific requirement. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement to check:**
When --mem-queue-size=0 and the topic/channel is not ephemeral, no memory channel should be created. An unbuffered channel (make(chan *Message, 0)) is not equivalent to 'no channel' — it blocks on every send. The implementation must skip memory channel creation entirely and route to the backend disk queue.

Also report any other bugs you find in these files. This requirement is not the only thing worth checking.

Files to review:
- nsqd/channel.go
- nsqd/topic.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_specific/NSQ-12_review.md

git checkout master
