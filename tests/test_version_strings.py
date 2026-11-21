# SPDX-License-Identifier: Apache-2.0
"""Test that every file names the same draft tag as the top entry of the CHANGELOG."""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFT = re.compile(r"\bv?1\.0\.0-draft\.(\d+)\b")
HEADING = re.compile(r"^### 1\.0 — public draft (\d+), ")
# The CI build runs with a placeholder version, which is not a tag.
PLACEHOLDERS = {(".github/workflows/conformance.yml", "0")}


# Left out when there is no git checkout to list the files (an export or a source archive).
SKIP_DIRS = {".git", ".venv", "__pycache__", "dist", ".pytest_cache"}


def tracked_files():
    """The files git tracks; without a git checkout, every file of the tree but SKIP_DIRS."""
    if (ROOT / ".git").exists():
        try:
            r = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True)
        except OSError:
            r = None
        if r is not None and r.returncode == 0:
            return sorted(n for n in r.stdout.decode("utf-8").split("\0") if n)
    return sorted(p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*")
                  if p.is_file() and not SKIP_DIRS.intersection(p.relative_to(ROOT).parts))


def top_entry():
    lines = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("### "))
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("#")), len(lines))
    return lines[start], "\n".join(lines[start + 1:end])


def current_draft():
    heading, body = top_entry()
    m = HEADING.match(heading)
    assert m, f"the top CHANGELOG entry is not a public draft: {heading!r}"
    tags = set(DRAFT.findall(body))
    assert tags == {m.group(1)}, f"the top CHANGELOG entry names {sorted(tags)}, its heading draft {m.group(1)}"
    return m.group(1)


def test_every_file_names_the_tag_of_the_top_changelog_entry():
    draft = current_draft()
    wrong = []
    for name in tracked_files():
        if name == "CHANGELOG.md":
            continue
        path = ROOT / name
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(text.splitlines(), 1):
            for m in DRAFT.finditer(line):
                if m.group(1) != draft and (name, m.group(1)) not in PLACEHOLDERS:
                    wrong.append(f"{name}:{number}: {m.group(0)}")
    assert not wrong, f"expected draft {draft}:\n" + "\n".join(wrong)
