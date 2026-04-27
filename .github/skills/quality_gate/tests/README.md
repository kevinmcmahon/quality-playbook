# `.github/skills/quality_gate/tests/` — canonical runner

Run this suite with **`unittest discover`**, not pytest:

```sh
cd ~/Documents/QPB && \
python3 -m unittest discover -s .github/skills/quality_gate/tests/ -p 'test_*.py'
```

Pytest fails on this suite due to a pre-existing import-shadowing
issue: `quality_gate.py` lives at the same directory level as the
test files, and pytest's package-collection logic treats the
sibling `__init__.py` as a package marker, so `quality_gate.FAIL`
(the global counter the helpers mutate) ends up as a copy in
pytest's import context rather than a reference to the canonical
module. The result is failing assertions that pass under
`unittest discover`.

The Phase 5 acceptance gate (per DQ-5-8) specifies `unittest
discover` as the canonical runner; v1.5.4+ may revisit the import
architecture if pytest support becomes desirable.

The bin-side suite (`bin/tests/`) works under both pytest and
unittest discover; the pre-existing pytest issue is local to this
directory only.
