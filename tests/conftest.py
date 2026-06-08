"""Pytest fixtures for CLI integration tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from fileglide.app import create_cli


@pytest.fixture()
def runner() -> CliRunner:
    """Create an isolated click test runner."""

    return CliRunner()


@pytest.fixture()
def cli():
    """Create the fileglide root command."""

    return create_cli()


@pytest.fixture()
def fixture_root() -> Path:
    """Return the static test fixture root."""

    return Path(__file__).parent / "fixtures"


@pytest.fixture()
def workspace(tmp_path: Path) -> Path:
    """Create a temporary workspace with representative files."""

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "alpha.txt").write_text(
        "alpha\nbeta\ngamma\n", encoding="utf-8"
    )
    (tmp_path / "docs" / "notes.log").write_text(
        "line one\nmatch this line\n", encoding="utf-8"
    )
    (tmp_path / "bytes.bin").write_bytes(bytes.fromhex("00010203ff"))
    return tmp_path


@pytest.fixture()
def sample_plan_path(tmp_path: Path) -> Path:
    """Write a minimal JSON batch plan into the temp workspace."""

    plan = {
        "steps": [
            {
                "action": "file.create",
                "arguments": {
                    "root": str(tmp_path),
                    "target": "generated.txt",
                    "parents": False,
                    "exist_ok": False,
                },
                "destructive": False,
            },
            {
                "action": "text.write",
                "arguments": {
                    "root": str(tmp_path),
                    "target": "generated.txt",
                    "content": "hello from batch\n",
                    "mode": "overwrite",
                },
                "destructive": True,
            },
        ]
    }
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return plan_path
