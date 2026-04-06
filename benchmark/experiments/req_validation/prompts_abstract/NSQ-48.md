git checkout 5ea1012

Review the following files against this requirement principle. Determine whether the code satisfies it. Report any violations with file, line number, severity, and description.

**Requirement principle:**
Layered resource cleanup must flush higher-level wrappers before lower-level ones. When a compressed stream wraps a file, the compressor must be flushed before the file is synced or closed.

Also report any other bugs you find in these files. This principle is not the only thing worth checking.

Files to review:
- apps/nsq_to_file/file_logger.go

For each bug found: file, line number, severity (Critical/High/Medium/Low), description of what's wrong.

Save findings to reviews_abstract/NSQ-48_review.md

git checkout master
