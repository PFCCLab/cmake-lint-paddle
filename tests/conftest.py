from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest

TEST_DIR = Path(tempfile.mkdtemp())


def pytest_sessionstart(session: pytest.Session):
    TEST_DIR.mkdir(exist_ok=True)
    shutil.copytree("samples", TEST_DIR / "samples")


def pytest_sessionfinish(session: pytest.Session, exitstatus: int):
    if TEST_DIR.exists():
        shutil.rmtree(TEST_DIR)
