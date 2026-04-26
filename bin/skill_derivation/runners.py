"""runners.py — LLM runner abstraction for skill_derivation passes.

Two concrete runners ship: ClaudeRunner (subprocess `claude --print
--model sonnet`) and CopilotRunner (subprocess `gh copilot --prompt
--model claude-sonnet-4.6`). Tests use MockRunner from
test_skill_derivation_pass_a.py.

Default to claude-print for Phase 3 self-audit runs because Phase 3
fires 60-100+ LLM calls per run and gh-copilot's weekly quota has
been under pressure -- defaulting to claude routes Phase 3 cost to
Anthropic's quota.

The CLI flag (`--runner claude|copilot`) follows the existing
bin/run_playbook.py convention; do not introduce a parallel env-var
scheme.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Protocol


@dataclass
class RunnerResult:
    stdout: str
    stderr: str
    elapsed_ms: int
    returncode: int


class LLMRunner(Protocol):
    """Minimal contract: turn a prompt into a stdout response.

    Implementations are responsible for measuring elapsed time and
    capturing stderr for debugging.
    """

    def run(self, prompt: str) -> RunnerResult:
        ...


@dataclass
class ClaudeRunner:
    """Subprocess wrapper for `claude --print --model <model>`.

    Sends the prompt on stdin to avoid command-line length limits on
    long section bodies + recovery preamble + output schema.
    """

    model: str = "sonnet"
    timeout_seconds: int = 600  # 10 minutes per call; long enough for substantive sections

    def run(self, prompt: str) -> RunnerResult:
        import time
        start = time.monotonic()
        try:
            result = subprocess.run(
                ["claude", "--print", "--model", self.model],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return RunnerResult(
                stdout=result.stdout,
                stderr=result.stderr,
                elapsed_ms=elapsed_ms,
                returncode=result.returncode,
            )
        except subprocess.TimeoutExpired:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return RunnerResult(
                stdout="",
                stderr=f"timeout after {self.timeout_seconds}s",
                elapsed_ms=elapsed_ms,
                returncode=124,
            )


@dataclass
class CopilotRunner:
    """Subprocess wrapper for `gh copilot --prompt --model <model>`.

    Burns gh-copilot weekly quota; opt in explicitly via --runner
    copilot. Default Phase 3 runs use ClaudeRunner.
    """

    model: str = "claude-sonnet-4.6"
    timeout_seconds: int = 600

    def run(self, prompt: str) -> RunnerResult:
        import time
        start = time.monotonic()
        try:
            result = subprocess.run(
                ["gh", "copilot", "--prompt", prompt, "--model", self.model],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return RunnerResult(
                stdout=result.stdout,
                stderr=result.stderr,
                elapsed_ms=elapsed_ms,
                returncode=result.returncode,
            )
        except subprocess.TimeoutExpired:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return RunnerResult(
                stdout="",
                stderr=f"timeout after {self.timeout_seconds}s",
                elapsed_ms=elapsed_ms,
                returncode=124,
            )


def make_runner(name: str) -> LLMRunner:
    """Factory. CLI flag value -> runner instance."""
    if name == "claude":
        return ClaudeRunner()
    if name == "copilot":
        return CopilotRunner()
    raise ValueError(
        f"unknown runner {name!r}; valid values: claude, copilot"
    )
