# SPDX-License-Identifier: Apache-2.0
"""Tests for tools/conformance/run_all.py: each one breaks a copy of the repository in one place."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
IGNORE = shutil.ignore_patterns(".git", ".venv", "__pycache__", ".pytest_cache")


@pytest.fixture
def copy(tmp_path):
    dst = tmp_path / "repo"
    shutil.copytree(ROOT, dst, ignore=IGNORE)
    return dst


def run(repo):
    return subprocess.run(
        [sys.executable, "-B", str(repo / "tools" / "conformance" / "run_all.py"), "--root", str(repo)],
        capture_output=True, text=True, cwd=repo)


def assert_fail(repo, line):
    r = run(repo)
    assert r.returncode == 1, r.stdout + r.stderr
    assert line in r.stdout.splitlines() or any(l.startswith(line) for l in r.stdout.splitlines()), r.stdout


def edit(path, fn):
    path.write_text(fn(path.read_text(encoding="utf-8")), encoding="utf-8")


def test_clean_tree_passes(copy):
    r = run(copy)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "51/51 expectations met" in r.stdout
    assert "OK   06-extracted-silver-chloride-tio2.json" in r.stdout


def test_duplicate_key_fails(copy):
    edit(copy / "vocab" / "regions.json", lambda t: t.replace("{", '{"vocab": "regions",', 1))
    assert_fail(copy, "FAIL duplicate keys: duplicate key 'vocab' in vocab/regions.json")


def test_duplicate_key_in_conformance_data_fails(copy):
    edit(copy / "tools" / "conformance" / "rule6_vectors.json", lambda t: t.replace("{", '{"title": "x",', 1))
    r = run(copy)
    assert r.returncode == 1, r.stdout + r.stderr
    line = "FAIL duplicate keys: duplicate key 'title' in tools/conformance/rule6_vectors.json"
    assert line in r.stdout.splitlines(), r.stdout


def test_basis_enum_mismatch_fails(copy):
    p = copy / "schema" / "dossier.schema.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    enum = d["$defs"]["property"]["properties"]["basis"]["enum"]
    enum.remove("declared")
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")
    assert_fail(copy, "FAIL basis enumeration differs")


def _index(copy, fn):
    p = copy / "vocab" / "index.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    fn(d["vocabularies"])
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")


def test_index_term_count_fails(copy):
    def bump(v):
        next(e for e in v if e["file"] == "basis.json")["terms"] = 8
    _index(copy, bump)
    assert_fail(copy, "FAIL vocab index: basis.json lists 8 terms, the file has 7")


def test_unlisted_vocab_file_fails(copy):
    _index(copy, lambda v: v.remove(next(e for e in v if e["file"] == "regions.json")))
    assert_fail(copy, "FAIL vocab index: regions.json is not listed")


def test_broken_example_fails(copy):
    p = copy / "examples" / "02-rheology-modifier.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    next(x for x in d["properties"] if "unit" in x)["unit"] = "parsec"
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    assert_fail(copy, "FAIL examples")


def test_changed_indexed_example_fails(copy):
    p = copy / "examples" / "01-humectant-active.json"
    t = p.read_text(encoding="utf-8")
    assert t.endswith("\n")
    p.write_text(t[:-1] + " \n", encoding="utf-8")
    assert_fail(copy, "FAIL endpoint index")


def test_broken_conformance_case_fails(copy):
    p = copy / "tools" / "conformance" / "rule6_vectors.json"
    t = p.read_text(encoding="utf-8")
    d = json.loads(t)
    vec = d if isinstance(d, list) else next(v for v in d.values() if isinstance(v, list))
    first = vec[0]
    first["expect"] = (not first["expect"]) if isinstance(first["expect"], bool) else "x" + str(first["expect"])
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
    assert_fail(copy, "FAIL conformance cases")


def test_id_layout_fails(copy):
    edit(copy / "vocab" / "index.json",
         lambda t: t.replace("https://rubedyne.com/schemas/material-dossier/1.0/vocab/1.0/", "https://example.com/x/"))
    assert_fail(copy, "FAIL $id layout: vocab/index.json: https://example.com/x/")


def test_malformed_schema_fails_cleanly(copy):
    (copy / "schema" / "index.schema.json").write_text("{", encoding="utf-8")
    r = run(copy)
    assert r.returncode == 1, r.stdout + r.stderr
    assert any(l.startswith("FAIL schemas: schema/index.schema.json:") for l in r.stdout.splitlines()), r.stdout
    assert "Traceback" not in r.stdout and "Traceback" not in r.stderr
