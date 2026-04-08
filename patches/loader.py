"""Replace python-magic's loader with our hermetic version."""
# ruff: noqa: INP001

import ctypes
import os
import sys
from pathlib import Path

PARENT = Path(__file__).parent


def load_lib() -> ctypes.CDLL:
    """Load the bundled libmagic library."""
    ext = ".dylib" if sys.platform == "darwin" else ".dll" if sys.platform == "win32" else ".so"

    bundled_lib = PARENT.absolute() / f"libmagic{ext}"
    bundled_mgc = PARENT.absolute() / "magic.mgc"

    try:
        cdll = ctypes.CDLL(str(bundled_lib))
    except OSError as e:
        raise ImportError(
            f"python-magic: failed to find libmagic.  Check your installation: \n{e}"
        ) from e

    if not os.getenv("MAGIC"):
        os.environ["MAGIC"] = str(bundled_mgc)

    return cdll
