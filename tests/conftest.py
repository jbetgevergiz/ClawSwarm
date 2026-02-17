"""
Pytest configuration and shared fixtures for ClawSwarm tests.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# Enable pytest-asyncio for async tests
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """A temporary directory for test files."""
    return tmp_path


@pytest.fixture
def env_cleanup():
    """
    Restore os.environ after test. Use with monkeypatch or manually
    set/delete keys in test.
    """
    before = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(before)


@pytest.fixture
def mock_memory_path(monkeypatch, tmp_path):
    """Point agent memory to a temp file."""
    memory_file = tmp_path / "agent_memory.md"

    def _get_memory_path():
        return memory_file

    monkeypatch.setattr(
        "claw_swarm.memory.get_memory_path",
        _get_memory_path,
    )
    return memory_file
