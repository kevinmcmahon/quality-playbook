"""Quality Playbook gate script — package entry point.

The main module lives alongside this file at quality_gate.py. Re-exporting
its public names here lets tests and callers use `quality_gate.FUNC`
interchangeably whether `quality_gate` resolves to this package (as pytest
does) or to the module file directly (as a bare `sys.path` import does).
"""
from .quality_gate import *  # noqa: F401,F403
