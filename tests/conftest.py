from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from evolution.genome import GenomeRegistry
from evolution.genome.bootstrap import bootstrap
from evolution.telemetry import Telemetry
from services.common import ROOT
from services.register import Store

REGRESSION = ROOT / "evolution" / "evals" / "regression" / "resolution.json"


@pytest.fixture()
def registry(tmp_path: Path) -> GenomeRegistry:
    """A clean, throwaway genome registry (seed genomes only)."""
    root = tmp_path / "genome"
    bootstrap(root)
    return GenomeRegistry(root)


@pytest.fixture()
def telemetry(tmp_path: Path) -> Telemetry:
    return Telemetry(tmp_path / "telemetry.jsonl")


@pytest.fixture()
def store(tmp_path: Path) -> Store:
    return Store(tenant_id="test", path=tmp_path / "store.json")


@pytest.fixture()
def clean_regression():
    backup = REGRESSION.read_text(encoding="utf-8") if REGRESSION.exists() else None
    REGRESSION.unlink(missing_ok=True)
    yield
    if backup is None:
        REGRESSION.unlink(missing_ok=True)
    else:
        REGRESSION.write_text(backup, encoding="utf-8")
