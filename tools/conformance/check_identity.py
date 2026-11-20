#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Check that every commit has the project identity as author and committer.

    check_identity.py [--root DIR]

Prints only a count and short commit hashes, never names or addresses: the log of a public repository is public.
"""
import argparse
import subprocess
import sys
from pathlib import Path

NAME = "Rubedyne"
EMAIL = "info@rubedyne.com"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    a = ap.parse_args(argv)
    r = subprocess.run(["git", "log", "--format=%h%x00%an%x00%ae%x00%cn%x00%ce"], cwd=str(a.root),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    if r.returncode != 0:
        print("FAIL identity: the git log cannot be read")
        return 1
    rows = [line.split("\0") for line in r.stdout.splitlines() if line]
    bad = [row[0] for row in rows if row[1:] != [NAME, EMAIL, NAME, EMAIL]]
    if bad:
        print(f"FAIL identity: {len(bad)} commit(s) without the project identity:")
        for sha in bad:
            print(sha)
        return 1
    print(f"PASS identity: {len(rows)} commits")
    return 0


if __name__ == "__main__":
    sys.exit(main())
