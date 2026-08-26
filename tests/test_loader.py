"""Tests for the loader that points python-magic at the bundled libmagic."""

from __future__ import annotations

import os

import pytest

from hermetic.magic.loader import load_lib


@pytest.fixture(autouse=True)
def _clear_magic_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MAGIC", raising=False)


def test_load_lib_sets_magic_env_to_bundled_database() -> None:
    load_lib()

    assert os.environ["MAGIC"].endswith("magic.mgc")


def test_load_lib_does_not_override_existing_magic_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAGIC", "/custom/magic.mgc")

    load_lib()

    assert os.environ["MAGIC"] == "/custom/magic.mgc"
