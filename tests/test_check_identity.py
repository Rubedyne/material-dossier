# SPDX-License-Identifier: Apache-2.0
"""Tests for tools/conformance/check_identity.py: each one builds a small repository with chosen identities."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "conformance" / "check_identity.py"
OK = ("Rubedyne", "info@rubedyne.com")
ENV = dict(os.environ, GIT_CONFIG_GLOBAL="/dev/null", GIT_CONFIG_SYSTEM="/dev/null")


def commit(repo, n, author=OK, committer=OK):
    (repo / "f").write_text(str(n))
    subprocess.run(["git", "add", "f"], cwd=repo, check=True, env=ENV)
    env = dict(ENV, GIT_AUTHOR_NAME=author[0], GIT_AUTHOR_EMAIL=author[1],
               GIT_COMMITTER_NAME=committer[0], GIT_COMMITTER_EMAIL=committer[1])
    subprocess.run(["git", "commit", "-q", "-m", f"c{n}"], cwd=repo, check=True, env=env)
    out = subprocess.run(["git", "log", "-1", "--format=%h"], cwd=repo, check=True, env=ENV,
                         capture_output=True, text=True)
    return out.stdout.strip()


def make(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, env=ENV)
    return repo


def check(repo):
    return subprocess.run([sys.executable, "-B", str(SCRIPT), "--root", str(repo)],
                          capture_output=True, text=True, env=ENV)


def test_all_project_identity_passes(tmp_path):
    repo = make(tmp_path)
    commit(repo, 1)
    commit(repo, 2)
    r = check(repo)
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.strip() == "PASS identity: 2 commits"


def test_author_name_containing_the_name_fails(tmp_path):
    repo = make(tmp_path)
    commit(repo, 1)
    sha = commit(repo, 2, author=("Xavier Rubedyne", OK[1]))
    r = check(repo)
    assert r.returncode == 1
    assert "FAIL identity: 1 commit(s) without the project identity:" in r.stdout.splitlines()
    assert sha in r.stdout.splitlines()


def test_committer_email_with_a_suffix_fails(tmp_path):
    repo = make(tmp_path)
    sha = commit(repo, 1, committer=(OK[0], "info@rubedyne.com.evil"))
    r = check(repo)
    assert r.returncode == 1
    assert sha in r.stdout.splitlines()


def test_output_never_shows_foreign_names_or_addresses(tmp_path):
    repo = make(tmp_path)
    commit(repo, 1, author=("Zoltan Foreign", "zf@foreign.example"))
    r = check(repo)
    assert r.returncode == 1
    assert "Zoltan" not in r.stdout + r.stderr
    assert "foreign.example" not in r.stdout + r.stderr
