"""Every script in scripts/ must import cleanly and answer --help with exit 0.

This closes the untested-path class that bit us twice:
  - the ONNX pooling bug lived on a shipping path no test ever exercised;
  - `migrate_chunk_ids.py` imported `HEADER_RE` from `eval_retriever` after that
    name was removed in the parser consolidation, so it ImportError'd on load —
    and nothing caught it, because no test ever loaded a scripts/ module.

A script that cannot even be imported (or whose --help crashes) is dead on
arrival for a judge. These two cheap checks make that failure loud in CI.

Both checks run in a SUBPROCESS so a heavy script's module-level imports never
pollute the test process, and so an ImportError surfaces as a non-zero exit.

Requires only what the scripts themselves import at module load (numpy, pdfplumber,
tokenizers — the declared deps). export_onnx.py imports torch lazily inside its
functions, so importing it needs no torch.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = sorted((ROOT / "scripts").glob("*.py"))
IDS = [p.name for p in SCRIPTS]


@pytest.mark.parametrize("script", SCRIPTS, ids=IDS)
def test_script_imports_cleanly(script: Path):
    """Loading the module (running its top-level code, NOT __main__) must not raise.
    Catches the HEADER_RE-style ImportError and any module-level side effect."""
    code = (
        "import importlib.util as u, sys;"
        f"s=u.spec_from_file_location('_m', r'{script}');"
        "m=u.module_from_spec(s);"
        "s.loader.exec_module(m)"
    )
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert r.returncode == 0, f"{script.name} failed to import:\n{r.stderr}"


@pytest.mark.parametrize("script", SCRIPTS, ids=IDS)
def test_script_help_exits_zero(script: Path):
    """`python scripts/X.py --help` must exit 0 — proves the module loads AND that
    argument handling is wired up (a missing __main__/argparse or a crash shows up
    here). Kept offline and side-effect-free: --help returns before any real work."""
    r = subprocess.run(
        [sys.executable, str(script), "--help"], capture_output=True, text=True
    )
    assert r.returncode == 0, f"{script.name} --help exited {r.returncode}:\n{r.stderr}"
