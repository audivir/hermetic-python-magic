"""Tests ported from ahupp/python-magic's own test suite, covering the Magic API."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from hermetic import magic

FIXTURES = Path(__file__).parent / "fixtures"


def assert_values(
    magic_instance: magic.Magic,
    expected: dict[str, str | tuple[str, ...]],
    *,
    buf_equals_file: bool = True,
) -> None:
    for filename, expected_value in expected.items():
        path = FIXTURES / filename
        expected_values = (expected_value,) if isinstance(expected_value, str) else expected_value

        buf_value = magic_instance.from_buffer(path.read_bytes())
        file_value = magic_instance.from_file(str(path))

        if buf_equals_file:
            assert buf_value == file_value
        for value in (buf_value, file_value):
            assert value in expected_values


def test_version() -> None:
    # the vendored __init__.pyi leaves version() untyped.
    assert magic.version() > 0  # type: ignore[no-untyped-call]


def test_from_file_str_and_bytes() -> None:
    path = FIXTURES / "test.pdf"

    assert magic.from_file(str(path), mime=True) == "application/pdf"
    assert magic.from_file(str(path).encode(), mime=True) == "application/pdf"


def test_from_descriptor() -> None:
    with (FIXTURES / "test.pdf").open() as f:
        assert magic.from_descriptor(f.fileno(), mime=True) == "application/pdf"


def test_from_buffer_str_and_bytes() -> None:
    magic_instance = magic.Magic(mime=True)
    script = '#!/usr/bin/env python\nprint("foo")'

    assert magic_instance.from_buffer(script) in ("text/x-python", "text/x-script.python")
    assert magic_instance.from_buffer(script.encode()) in (
        "text/x-python",
        "text/x-script.python",
    )


def test_mime_types() -> None:
    magic_instance = magic.Magic(mime=True)
    assert_values(
        magic_instance,
        {
            "magic._pyc_": (
                "application/octet-stream",
                "text/x-bytecode.python",
                "application/x-bytecode.python",
            ),
            "test.pdf": "application/pdf",
            "test.gz": ("application/gzip", "application/x-gzip"),
            "test.snappy.parquet": (
                "application/octet-stream",
                "application/vnd.apache.parquet",
            ),
            "text.txt": "text/plain",
        },
    )


def test_mime_types_unicode_filename(tmp_path: Path) -> None:
    # proves buffer-vs-filename detection stays consistent for a non-ASCII path.
    dest = tmp_path / "\N{GREEK SMALL LETTER LAMDA}"
    shutil.copyfile(FIXTURES / "lambda", dest)

    magic_instance = magic.Magic(mime=True)
    assert magic_instance.from_file(str(dest)) == "text/plain"
    assert magic_instance.from_buffer(dest.read_bytes()) == "text/plain"


def test_descriptions(monkeypatch: pytest.MonkeyPatch) -> None:
    magic_instance = magic.Magic()
    monkeypatch.setenv("TZ", "UTC")  # to get last modified date of test.gz in UTC
    assert_values(
        magic_instance,
        {
            "magic._pyc_": "python 2.4 byte-compiled",
            "test.pdf": ("PDF document, version 1.2", "PDF document, version 1.2, 2 page(s)"),
            "text.txt": "ASCII text",
            "test.snappy.parquet": ("Apache Parquet file", "Apache Parquet"),
        },
        buf_equals_file=False,
    )


def test_extension() -> None:
    try:
        # the vendored __init__.pyi predates the extension kwarg.
        magic_instance = magic.Magic(extension=True)  # type: ignore[call-arg]
    except NotImplementedError:  # pragma: no cover
        pytest.skip("MAGIC_EXTENSION not supported in this version")

    assert_values(
        magic_instance,
        {
            "test.gz": tuple({"gz/tgz/tpz/zabw/svgz", "gz/tgz/tpz/zabw/svgz/adz/kmy/xcfgz", "???"}),
            "name_use.jpg": "jpeg/jpg/jpe/jfif",
        },
    )


def test_unicode_result_nonraw() -> None:
    magic_instance = magic.Magic(raw=False)
    result = magic_instance.from_file(str(FIXTURES / "pgpunicode"))
    # older/newer libmagic versions do not agree on whether this file is a PGP key.
    if "PGP" not in result:
        pytest.skip("Magic file does not identify this as a PGP key in this libmagic version.")
    assert result == "PGP\011Secret Sub-key -"  # pragma: no cover


def test_unicode_result_raw() -> None:
    magic_instance = magic.Magic(raw=True)
    result = magic_instance.from_file(str(FIXTURES / "pgpunicode"))
    if "PGP" not in result:
        pytest.skip("Magic file does not identify this as a PGP key in this libmagic version.")
    assert result.encode() == b"PGP\tSecret Sub-key -"  # pragma: no cover


def test_mime_encodings() -> None:
    magic_instance = magic.Magic(mime_encoding=True)
    assert_values(
        magic_instance,
        {
            "text-iso8859-1.txt": "iso-8859-1",
            "text.txt": "us-ascii",
        },
    )


def test_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    magic_instance = magic.Magic()
    with pytest.raises(FileNotFoundError):
        magic_instance.from_file("nonexistent")
    with pytest.raises(magic.MagicException):
        magic.Magic(magic_file="nonexistent")

    monkeypatch.setenv("MAGIC", "nonexistent")
    with pytest.raises(magic.MagicException):
        magic.Magic()


def test_keep_going() -> None:
    path = str(FIXTURES / "keep-going.jpg")

    magic_instance = magic.Magic(mime=True)
    assert magic_instance.from_file(path) == "image/jpeg"

    # this raises on "old" libmagic versions that do not support keep_going.
    magic_instance = magic.Magic(mime=True, keep_going=True)
    assert magic_instance.from_file(path) == "image/jpeg\\012- application/octet-stream"


def test_rethrow(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_passthrough(unused_cookie: object, unused_buf: bytes) -> None:
        raise magic.MagicException("passthrough")

    monkeypatch.setattr(magic, "magic_buffer", raise_passthrough)

    with pytest.raises(magic.MagicException):
        magic.from_buffer("hello", True)


def test_getparam() -> None:
    magic_instance = magic.Magic(mime=True)
    magic_instance.setparam(magic.MAGIC_PARAM_INDIR_MAX, 1)
    assert magic_instance.getparam(magic.MAGIC_PARAM_INDIR_MAX) == 1


def test_name_count() -> None:
    # regression test: a file that exercises many "name" rule chains used to overflow
    # libmagic's internal name-use counter and crash rather than returning a result.
    magic_instance = magic.Magic()
    result = magic_instance.from_buffer((FIXTURES / "name_use.jpg").read_bytes())
    assert "JPEG" in result


def test_pathlike() -> None:
    magic_instance = magic.Magic(mime=True)
    assert magic_instance.from_file(FIXTURES / "test.pdf") == "application/pdf"
