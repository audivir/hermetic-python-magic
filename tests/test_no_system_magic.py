"""Proves plain python-magic cannot load libmagic once CI has removed the system copy."""

from __future__ import annotations

import os
import subprocess
import sys

import pytest


@pytest.mark.skipif(
    not os.environ.get("CI"), reason="only meaningful after CI removes system libmagic"
)
def test_plain_python_magic_fails_without_system_libmagic() -> None:  # pragma: no cover
    result = subprocess.run(
        [sys.executable, "-c", "import magic"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0, f"plain python-magic unexpectedly imported: {result.stdout}"
    assert "failed to find libmagic" in result.stderr
