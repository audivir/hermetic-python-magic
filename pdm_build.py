"""Build standalone magic."""

from __future__ import annotations

import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from _typeshed import StrPath
    from pdm.backend.hooks.base import Context

logger = logging.getLogger(__name__)

PARENT = Path(__file__).parent

# FILE VERSION 5.47
FILE_COMMIT = "7d20612996567ecedec7f5c58f7bf15c2cf42c19"
# PYTHON-MAGIC VERSION 0.4.27
PYTHON_MAGIC_COMMIT = "b443195104d89363b93a547584c1a12fce3b57ec"


def run_sh(cmd: Sequence[str], cwd: StrPath, env: Mapping[str, str]) -> None:
    """Execute command."""
    if sys.platform == "win32":
        subprocess.check_call(["bash", "-c", shlex.join(cmd)], cwd=cwd, env=env)  # noqa: S603,S607
    else:
        subprocess.check_call(cmd, cwd=cwd, env=env)  # noqa: S603


def pdm_build_initialize(context: Context) -> None:
    """Initialize PDM build by downloading source and building libmagic."""
    if context.target == "sdist":
        return

    env = os.environ.copy()
    root: Path = context.root

    file_src = root / "file"
    pm_src = root / "python-magic"
    patches = root / "patches"

    # clone source
    run_sh(["git", "clone", "https://github.com/file/file"], cwd=root, env=env)
    run_sh(["git", "reset", "--hard", FILE_COMMIT], cwd=file_src, env=env)
    run_sh(["git", "clone", "https://github.com/ahupp/python-magic"], cwd=root, env=env)
    run_sh(["git", "reset", "--hard", PYTHON_MAGIC_COMMIT], cwd=pm_src, env=env)

    hermetic = root / "hermetic"
    hermetic.mkdir(parents=True)
    target_dir = hermetic / "magic"

    shutil.copytree(pm_src / "magic", target_dir)

    # manual fixes
    for f in target_dir.iterdir():
        if f.suffix in {".py", ".pyi"}:
            content = f.read_text()

            # replace `from magic import(...)`
            content = re.sub(
                r"^([>\s]+)from\s+magic\s+import([\s(])",
                r"\1from hermetic.magic import\2",
                content,
                flags=re.MULTILINE,
            )

            # replace `import magic[,\s]`
            content = re.sub(
                r"^([>\s]+)import\s+magic([,\s])",
                r"\1import hermetic.magic as magic\2",
                content,
                flags=re.MULTILINE,
            )

            f.write_text(content)

    # copy patches
    for f in patches.iterdir():
        target_path = target_dir / f.relative_to(patches)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(f, target_path)

    # build libmagic
    env["CFLAGS"] = env.get("CFLAGS", "") + " -fPIC"

    # link gnurx on MSYS2
    if sys.platform == "win32":
        env["LDFLAGS"] = env.get("LDFLAGS", "") + " -lgnurx"

    run_sh(["autoreconf", "-f", "-i"], cwd=file_src, env=env)
    run_sh(["./configure", "--enable-shared", "--disable-static"], cwd=file_src, env=env)
    run_sh(["make", "clean"], cwd=file_src, env=env)
    run_sh(["make"], cwd=file_src, env=env)

    ext = ".dylib" if sys.platform == "darwin" else ".dll" if sys.platform == "win32" else ".so"
    libs_dir = file_src / "src" / ".libs"
    found_lib: Path | None = None

    for f in libs_dir.glob(f"*magic*{ext}*"):
        if f.is_symlink():
            continue  # skip links
        found_lib = f
        break

    if not found_lib:
        raise RuntimeError(f"Failed to find built *magic*{ext}* in {libs_dir}")

    # copy built libraries
    dest_lib = target_dir / f"libmagic{ext}"
    shutil.copyfile(found_lib, dest_lib)
    dest_lib.chmod(0o755)

    mgc_path = file_src / "magic" / "magic.mgc"
    shutil.copyfile(mgc_path, target_dir / "magic.mgc")
