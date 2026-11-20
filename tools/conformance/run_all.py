#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Run every check of the repository and exit 0 only if all of them pass.

    run_all.py [--root DIR]

Everything is read from DIR (default: the repository this file sits in): the schemas, the vocabularies, the
examples, the reference checker and the conformance cases.
"""
from __future__ import annotations

import argparse
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parents[2]


class DuplicateKey(ValueError):
    pass


def _no_duplicates(pairs):
    seen = {}
    for k, v in pairs:
        if k in seen:
            raise DuplicateKey(f"duplicate key '{k}'")
        seen[k] = v
    return seen


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicates)


def _report(name: str, problems: list[str]) -> int:
    if problems:
        print(f"FAIL {name}: {problems[0]}")
        for p in problems[1:]:
            print(f"   {p}")
        return 1
    print(f"PASS {name}")
    return 0


def _rel(root: Path, p: Path) -> str:
    return p.relative_to(root).as_posix()


def check_duplicate_keys(root: Path) -> int:
    problems = []
    for folder in ("schema", "vocab", "examples", "tools/conformance"):
        for f in sorted((root / folder).rglob("*.json")):
            try:
                load_json(f)
            except DuplicateKey as e:
                problems.append(f"{e} in {_rel(root, f)}")
            except ValueError as e:
                problems.append(f"{_rel(root, f)} is not valid JSON ({e})")
    return _report("duplicate keys", problems)


def check_schemas(root: Path) -> int:
    from jsonschema import Draft202012Validator
    problems = []
    for f in sorted((root / "schema").glob("*.json")):
        try:
            Draft202012Validator.check_schema(json.loads(f.read_text(encoding="utf-8")))
        except Exception as e:  # SchemaError or unreadable file
            problems.append(f"{_rel(root, f)}: {str(e).splitlines()[0]}")
    return _report("schemas", problems)


def check_vocab_files(root: Path) -> int:
    from jsonschema import Draft202012Validator
    schema = json.loads((root / "schema" / "vocab.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    problems = []
    for f in sorted((root / "vocab").glob("*.json")):
        if f.name == "index.json":
            continue
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except ValueError as e:
            problems.append(f"{_rel(root, f)} is not valid JSON ({e})")
            continue
        for err in validator.iter_errors(doc):
            problems.append(f"{_rel(root, f)}: {err.message[:200]}")
    return _report("vocabularies", problems)


def check_vocab_index(root: Path) -> int:
    vocab = root / "vocab"
    problems = []
    try:
        index = json.loads((vocab / "index.json").read_text(encoding="utf-8"))
        entries = index["vocabularies"]
    except (OSError, ValueError, KeyError) as e:
        return _report("vocab index", [f"vocab/index.json cannot be read ({e})"])
    listed: dict[str, int] = {}
    for e in entries:
        listed[e["file"]] = listed.get(e["file"], 0) + 1
    for f in sorted(vocab.glob("*.json")):
        if f.name == "index.json":
            continue
        n = listed.get(f.name, 0)
        if n == 0:
            problems.append(f"{f.name} is not listed")
        elif n > 1:
            problems.append(f"{f.name} is listed {n} times")
    for name in listed:
        if not (vocab / name).is_file() and name != "index.json":
            problems.append(f"{name} is listed but does not exist")
    for e in entries:
        f = vocab / e["file"]
        if not f.is_file():
            continue
        have = len(json.loads(f.read_text(encoding="utf-8")).get("terms", []))
        if e.get("terms") != have:
            problems.append(f"{e['file']} lists {e.get('terms')} terms, the file has {have}")
    problems = [f"vocab index: {p}" for p in problems]
    if problems:
        print(f"FAIL {problems[0]}")
        for p in problems[1:]:
            print(f"   {p}")
        return 1
    print("PASS vocab index")
    return 0


def check_basis_enum(root: Path) -> int:
    schema = json.loads((root / "schema" / "dossier.schema.json").read_text(encoding="utf-8"))
    enum = set(schema["$defs"]["property"]["properties"]["basis"]["enum"])
    terms = {t["key"] for t in json.loads((root / "vocab" / "basis.json").read_text(encoding="utf-8"))["terms"]}
    if enum == terms:
        print("PASS basis enumeration")
        return 0
    print(f"FAIL basis enumeration differs: only in schema {sorted(enum - terms)}, "
          f"only in vocab/basis.json {sorted(terms - enum)}")
    return 1


def check_id_layout(root: Path) -> int:
    prefix = "https://rubedyne.com/schemas/material-dossier/1.0/"
    problems = []
    for f in sorted((root / "schema").glob("*.json")):
        try:
            sid = json.loads(f.read_text(encoding="utf-8")).get("$id")
        except ValueError:
            continue  # reported by the schema check
        if not isinstance(sid, str) or not sid.startswith(prefix):
            problems.append(f"{_rel(root, f)}: {sid}")
    try:
        index = json.loads((root / "vocab" / "index.json").read_text(encoding="utf-8"))
        base = index.get("base")
        if base != f"{prefix}vocab/{index.get('vocab_version')}/":
            problems.append(f"vocab/index.json: {base}")
    except (OSError, ValueError):
        pass  # reported by the vocab index check
    return _report("$id layout", problems)


def load_checker(root: Path):
    path = root / "tools" / "check_dossier.py"
    name = f"check_dossier_{abs(hash(str(path)))}"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def run_checker(root: Path, args: list[str]) -> tuple[int, str]:
    checker = load_checker(root)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            code = checker.main(["--vocab", str(root / "vocab"), "--schema", str(root / "schema"), *args])
    except (OSError, ValueError) as e:  # a schema or vocabulary file that cannot be read or parsed
        # that file is named by the schemas and vocabularies checks; here the run only has to go on
        code = 1
        buf.write(f"checker could not run ({type(e).__name__}: {e})\n")
    out = buf.getvalue()
    print(out, end="")
    return code, out


def check_examples(root: Path) -> int:
    files = sorted(p for p in (root / "examples").glob("*.json") if p.name != "index.json")
    code, out = run_checker(root, ["--sources", str(root / "examples" / "sources"), *map(str, files)])
    lines = [l for l in out.splitlines() if l[:1] != " "]
    bad = [l for l in lines if not l.startswith("OK   ")]
    problems = [f"{len(lines)} results for {len(files)} examples"] if len(lines) != len(files) else []
    problems += [l.split("  ")[0] for l in bad]
    if code != 0 and not problems:
        problems.append(f"checker exit status {code}")
    return _report("examples", problems)


def check_index(root: Path) -> int:
    code, out = run_checker(root, ["--index", str(root / "examples" / "index.json")])
    first = out.splitlines()[0] if out else ""
    problems = [] if code == 0 and first.startswith("OK   ") else [first or f"checker exit status {code}"]
    return _report("endpoint index", problems)


def check_conformance_cases(root: Path) -> int:
    r = subprocess.run([sys.executable, "-B", str(root / "tools" / "conformance" / "mutation_cases.py")],
                       cwd=root, capture_output=True, text=True)
    print(r.stdout, end="")
    print(r.stderr, end="", file=sys.stderr)
    problems = []
    if r.returncode != 0:
        problems.append(f"exit status {r.returncode}")
    if "49/49 expectations met" not in r.stdout:
        problems.append("the line '49/49 expectations met' is missing")
    return _report("conformance cases", problems)


def run(root: Path) -> int:
    root = Path(root).resolve()
    failed = 0
    print("## 1. schemas and vocabularies")
    for step in (check_schemas, check_vocab_files, check_duplicate_keys, check_vocab_index, check_basis_enum,
                 check_id_layout):
        failed += step(root)
    print("## 2. examples")
    failed += check_examples(root)
    print("## 3. endpoint index")
    failed += check_index(root)
    print("## 4. conformance cases")
    failed += check_conformance_cases(root)
    print(f"{'FAIL' if failed else 'PASS'}: {failed} failed check(s)")
    return failed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    a = ap.parse_args(argv)
    return 1 if run(a.root) else 0


if __name__ == "__main__":
    sys.exit(main())
