"""Every script in scripts/ AND every module in src/app/ must import cleanly,
and every CLI among them must answer --help with exit 0.

This closes the untested-path class that bit us twice:
  - the ONNX pooling bug lived on a shipping path no test ever exercised;
  - `migrate_chunk_ids.py` imported `HEADER_RE` from `eval_retriever` after that
    name was removed in the parser consolidation, so it ImportError'd on load —
    and nothing caught it, because no test ever loaded a scripts/ module.

A module that cannot even be imported (or a CLI whose --help crashes) is dead on
arrival for a judge. These cheap checks make that failure loud in CI. src/app/
is now covered too: the application layer (cli.py / pipeline.py) is exactly the
kind of thin glue where a stale import or a broken argparse wiring would
otherwise only surface in a live demo.

Both checks run in a SUBPROCESS so a heavy module's imports never pollute the
test process, and so an ImportError surfaces as a non-zero exit.

Requires only what the modules import at load time (numpy, pdfplumber, tokenizers
— the declared deps). export_onnx.py imports torch lazily, and app/pipeline.py
imports onnxruntime/retriever/tokenizers lazily, so importing them needs neither.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = sorted((ROOT / "scripts").glob("*.py"))
APP = sorted((ROOT / "src" / "app").glob("*.py"))

# Import-cleanliness applies to everything; --help applies only to the CLIs
# (every script has an argparse main; in app/, only cli.py is a CLI).
IMPORTABLE = SCRIPTS + APP
HELP_CLIS = SCRIPTS + [ROOT / "src" / "app" / "cli.py"]

IMPORT_IDS = [str(p.relative_to(ROOT)) for p in IMPORTABLE]
HELP_IDS = [str(p.relative_to(ROOT)) for p in HELP_CLIS]


@pytest.mark.parametrize("module", IMPORTABLE, ids=IMPORT_IDS)
def test_module_imports_cleanly(module: Path):
    """Loading the module (running its top-level code, NOT __main__) must not raise.
    Catches the HEADER_RE-style ImportError and any module-level side effect.

    The module is registered in sys.modules before exec: a dataclass declared
    under `from __future__ import annotations` resolves its field annotations via
    sys.modules[cls.__module__] at decoration time, which is None (→ AttributeError)
    for an unregistered module. Registering it is the importlib-documented way to
    exec a module and is what lets app/pipeline.py's dataclasses load here."""
    code = (
        "import importlib.util as u, sys;"
        f"s=u.spec_from_file_location('_smoke', r'{module}');"
        "m=u.module_from_spec(s);"
        "sys.modules['_smoke']=m;"
        "s.loader.exec_module(m)"
    )
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert r.returncode == 0, f"{module.name} failed to import:\n{r.stderr}"


@pytest.mark.parametrize("cli", HELP_CLIS, ids=HELP_IDS)
def test_cli_help_exits_zero(cli: Path):
    """`python <cli> --help` must exit 0 — proves the module loads AND that
    argument handling is wired up (a missing __main__/argparse or a crash shows up
    here). Kept offline and side-effect-free: --help returns before any real work."""
    r = subprocess.run(
        [sys.executable, str(cli), "--help"], capture_output=True, text=True
    )
    assert r.returncode == 0, f"{cli.name} --help exited {r.returncode}:\n{r.stderr}"
