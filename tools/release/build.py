#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build a release: the distribution ZIP, the files served under each schema's $id, and SHA256SUMS.txt.

    build.py --version VERSION OUT_DIR

VERSION is 1.0.0 or 1.0.0-draft.N. OUT_DIR must not exist or must be empty. The inputs are the files that git
tracks (the work tree must be clean); outside a git work tree, for example in an exported archive, every file
below the repository folder is used except caches. The output does not depend on the time, the machine or the
zlib build: the same input gives the same bytes.

Exit status: 0 built, 2 refused (bad arguments, dirty work tree, inconsistent $id layout).
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
VERSION_RE = re.compile(r"^1\.0\.0(-draft\.\d+)?\Z")
ID_PREFIX = "https://rubedyne.com/"
SCHEMA_DIR = "schemas/material-dossier/1.0/"

# (folder, file-name pattern): a file is in the ZIP when its folder equals and its name matches.
INCLUDE = [
    ("", "SPEC.md"), ("", "README.md"), ("", "CHANGELOG.md"), ("", "LICENSE.md"), ("", "LICENSE-*.txt"),
    ("", "requirements.txt"),
    ("guides", "*"),
    ("schema", "*.json"),
    ("vocab", "*.json"),
    ("examples", "*.json"),
    ("examples/sources", "*.txt"),
    ("tools", "check_dossier.py"),
    ("tools/conformance", "*.py"), ("tools/conformance", "*.json"), ("tools/conformance", "*.md"),
]
ZIP_TIME = (1980, 1, 1, 0, 0, 0)


class Refused(Exception):
    pass


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)


def in_git_work_tree(root: Path) -> bool:
    try:
        r = _git(root, "rev-parse", "--show-toplevel")
    except OSError:
        return False
    return r.returncode == 0 and Path(r.stdout.strip()).resolve() == root.resolve()


def source_files(root: Path) -> list[str]:
    """Repository-relative POSIX paths of every candidate file."""
    if in_git_work_tree(root):
        status = _git(root, "status", "--porcelain")
        if status.returncode != 0 or status.stdout.strip():
            raise Refused("the git work tree is not clean")
        r = _git(root, "ls-files", "-z")
        if r.returncode != 0:
            raise Refused("git ls-files failed")
        return sorted(n for n in r.stdout.split("\0") if n and (root / n).is_file())
    names = []
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if "__pycache__" in rel.parts or p.suffix == ".pyc" or not p.is_file():
            continue
        names.append(rel.as_posix())
    return sorted(names)


def included(name: str) -> bool:
    path = PurePosixPath(name)
    folder = "" if str(path.parent) == "." else path.parent.as_posix()
    return any(folder == d and fnmatch.fnmatchcase(path.name, pat) for d, pat in INCLUDE)


def write_zip(root: Path, names: list[str], target: Path, top: str) -> None:
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED) as z:
        for name in sorted(names):
            info = zipfile.ZipInfo(f"{top}/{name}", date_time=ZIP_TIME)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = 0o644 << 16
            z.writestr(info, (root / name).read_bytes())


def write_id_files(root: Path, out: Path) -> list[Path]:
    written = []
    for f in sorted((root / "schema").glob("*.json")):
        doc = json.loads(f.read_text(encoding="utf-8"))
        rel = SCHEMA_DIR + f.name
        if doc.get("$id") != ID_PREFIX + rel:
            raise Refused(f"schema/{f.name}: $id {doc.get('$id')!r} is not {ID_PREFIX + rel}")
        written.append(_copy(f, out / rel))
    index = json.loads((root / "vocab" / "index.json").read_text(encoding="utf-8"))
    base = index.get("base", "")
    expected = f"{ID_PREFIX}{SCHEMA_DIR}vocab/{index.get('vocab_version')}/"
    if base != expected:
        raise Refused(f"vocab/index.json: base {base!r} is not {expected}")
    for f in sorted((root / "vocab").glob("*.json")):
        written.append(_copy(f, out / base[len(ID_PREFIX):] / f.name))
    return written


def _copy(src: Path, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
    return dst


def build(root: Path, version: str, out: Path) -> None:
    if not VERSION_RE.match(version):
        raise Refused(f"version {version!r} does not match 1.0.0 or 1.0.0-draft.N")
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise Refused(f"{out} exists and is not an empty folder")
    names = [n for n in source_files(root) if included(n)]
    if not names:
        raise Refused("no files to release")
    out.mkdir(parents=True, exist_ok=True)
    top = f"material-dossier-{version}"
    zip_path = out / f"{top}.zip"
    write_zip(root, names, zip_path, top)
    files = [zip_path] + write_id_files(root, out)
    lines = sorted((f.relative_to(out).as_posix(), hashlib.sha256(f.read_bytes()).hexdigest()) for f in files)
    (out / "SHA256SUMS.txt").write_text("".join(f"{h}  {p}\n" for p, h in lines), encoding="utf-8", newline="\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", required=True)
    ap.add_argument("out_dir", type=Path, metavar="OUT_DIR")
    a = ap.parse_args(argv)
    try:
        build(ROOT, a.version, a.out_dir)
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    print(f"built {a.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
