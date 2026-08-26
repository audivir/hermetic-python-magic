"""Tests ported from ahupp/python-magic's own test suite, covering the detect_from_* API."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from hermetic import magic

if TYPE_CHECKING:
    from hermetic.magic.compat import FileMagic

FIXTURE = Path(__file__).parent / "fixtures" / "test.pdf"
EXPECTED_MIME_TYPE = "application/pdf"
EXPECTED_ENCODING = "us-ascii"
EXPECTED_NAME = ("PDF document, version 1.2", "PDF document, version 1.2, 2 page(s)")


def assert_result(result: FileMagic) -> None:
    assert result.mime_type == EXPECTED_MIME_TYPE
    assert result.encoding == EXPECTED_ENCODING
    assert result.name in EXPECTED_NAME


def test_detect_from_filename() -> None:
    # detect_from_filename is injected at runtime by magic._add_compat and is not
    # declared in the vendored __init__.pyi.
    with pytest.warns(PendingDeprecationWarning):
        result = magic.detect_from_filename(str(FIXTURE))  # type: ignore[attr-defined]
    assert_result(result)


def test_detect_from_fobj() -> None:
    with FIXTURE.open() as fobj, pytest.warns(PendingDeprecationWarning):
        result = magic.detect_from_fobj(fobj)  # type: ignore[attr-defined]
    assert_result(result)


def test_detect_from_content() -> None:
    # differs from upstream by reading in binary mode: text mode hits a known bug in the
    # python3+libmagic bindings.
    with pytest.warns(PendingDeprecationWarning):
        result = magic.detect_from_content(FIXTURE.read_bytes()[:4096])  # type: ignore[attr-defined]
    assert_result(result)
