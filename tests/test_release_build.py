# SPDX-License-Identifier: Apache-2.0
"""Tests for tools/release/build.py: each one builds from a copy of the repository without version control."""
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
IGNORE = shutil.ignore_patterns(".git", ".venv", "__pycache__", ".pytest_cache", "*.pyc")
VERSION = "1.0.0-draft.3"
TOP = f"material-dossier-{VERSION}"
ID_PREFIX = "https://rubedyne.com/"


@pytest.fixture
def copy(tmp_path):
    dst = tmp_path / "repo"
    shutil.copytree(ROOT, dst, ignore=IGNORE)
    return dst


def build(repo, out, version=VERSION):
    return subprocess.run(
        [sys.executable, "-B", str(repo / "tools" / "release" / "build.py"), "--version", version, str(out)],
        capture_output=True, text=True, cwd=repo)


def built(repo, tmp_path, name="out"):
    out = tmp_path / name
    r = build(repo, out)
    assert r.returncode == 0, r.stdout + r.stderr
    return out


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_two_builds_are_byte_identical(copy, tmp_path):
    a = built(copy, tmp_path, "a")
    b = built(copy, tmp_path, "b")
    assert (a / f"{TOP}.zip").read_bytes() == (b / f"{TOP}.zip").read_bytes()
    assert (a / "SHA256SUMS.txt").read_bytes() == (b / "SHA256SUMS.txt").read_bytes()


def test_zip_names_are_exactly_the_list(copy, tmp_path):
    out = built(copy, tmp_path)
    patterns = ["SPEC.md", "README.md", "CHANGELOG.md", "LICENSE.md", "LICENSE-*.txt", "requirements.txt",
                "guides/*", "schema/*.json", "vocab/*.json", "examples/*.json", "examples/sources/*.txt",
                "tools/check_dossier.py", "tools/conformance/*.py", "tools/conformance/*.json",
                "tools/conformance/*.md"]
    expected = {f"{TOP}/{p.relative_to(copy).as_posix()}"
                for pat in patterns for p in copy.glob(pat) if p.is_file()}
    with zipfile.ZipFile(out / f"{TOP}.zip") as z:
        names = z.namelist()
    assert len(names) == len(set(names))
    assert set(names) == expected
    assert names == sorted(names)
    assert f"{TOP}/requirements.txt" in names
    for bad in ("tests/", ".github/", "tools/release/", "README.hu.md", "DESIGN-NOTES.md", "CONTRIBUTING.md",
                ".gitignore", ".gitattributes", "requirements-dev.txt"):
        assert not any(n.startswith(f"{TOP}/{bad}") for n in names), bad


def test_zip_entries_are_normalised(copy, tmp_path):
    out = built(copy, tmp_path)
    with zipfile.ZipFile(out / f"{TOP}.zip") as z:
        for i in z.infolist():
            assert i.date_time == (1980, 1, 1, 0, 0, 0)
            assert i.external_attr == 0o644 << 16
            assert i.compress_type == zipfile.ZIP_STORED
            rel = i.filename[len(TOP) + 1:]
            assert z.read(i) == (copy / rel).read_bytes()


def test_stray_cache_file_is_left_out(copy, tmp_path):
    cache = copy / "tools" / "conformance" / "__pycache__"
    cache.mkdir()
    (cache / "x.pyc").write_bytes(b"junk")
    (copy / "tools" / "conformance" / "y.pyc").write_bytes(b"junk")
    out = built(copy, tmp_path)
    with zipfile.ZipFile(out / f"{TOP}.zip") as z:
        assert not [n for n in z.namelist() if "pyc" in n or "__pycache__" in n]


def test_schema_paths_equal_their_ids(copy, tmp_path):
    out = built(copy, tmp_path)
    files = sorted(out.glob("schemas/material-dossier/1.0/*.schema.json"))
    assert [f.name for f in files] == sorted(p.name for p in (copy / "schema").glob("*.json"))
    for f in files:
        assert ID_PREFIX + f.relative_to(out).as_posix() == json.loads(f.read_text(encoding="utf-8"))["$id"]
        assert f.read_bytes() == (copy / "schema" / f.name).read_bytes()


def test_vocab_files_under_the_index_base(copy, tmp_path):
    out = built(copy, tmp_path)
    base = json.loads((copy / "vocab" / "index.json").read_text(encoding="utf-8"))["base"]
    assert base == "https://rubedyne.com/schemas/material-dossier/1.0/vocab/1.0/"
    src = sorted((copy / "vocab").glob("*.json"))
    assert "index.json" in [p.name for p in src]
    for p in src:
        target = out / (base[len(ID_PREFIX):] + p.name)
        assert target.read_bytes() == p.read_bytes()
    assert len(list((out / "schemas/material-dossier/1.0/vocab/1.0").iterdir())) == len(src)


def test_sha256sums_cover_every_file(copy, tmp_path):
    out = built(copy, tmp_path)
    lines = (out / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    listed = {}
    for line in lines:
        digest, rel = line.split("  ", 1)
        listed[rel] = digest
        assert digest == sha(out / rel)
    assert [l.split("  ", 1)[1] for l in lines] == sorted(listed)
    every = {p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()} - {"SHA256SUMS.txt"}
    assert set(listed) == every
    assert f"{TOP}.zip" in listed


def test_bad_version_and_non_empty_out_exit_2(copy, tmp_path):
    for v in ("1.1.0", "v1.0.0", "1.0.0-draft", "1.0.0-draft.x", "1.0.0 "):
        r = build(copy, tmp_path / "o", v)
        assert r.returncode == 2, v
        assert not (tmp_path / "o").exists()
    full = tmp_path / "full"
    full.mkdir()
    (full / "f.txt").write_text("x")
    assert build(copy, full).returncode == 2
    empty = tmp_path / "empty"
    empty.mkdir()
    assert build(copy, empty, "1.0.0").returncode == 0


def test_dirty_git_work_tree_exits_2(copy, tmp_path):
    def git(*a):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *a], cwd=copy,
                       check=True, capture_output=True)
    git("init", "-q")
    git("add", ".")
    git("commit", "-q", "-m", "init")
    out = tmp_path / "ok"
    assert build(copy, out).returncode == 0
    assert (out / f"{TOP}.zip").exists()
    (copy / "README.md").write_text("changed\n")
    assert build(copy, tmp_path / "dirty").returncode == 2
