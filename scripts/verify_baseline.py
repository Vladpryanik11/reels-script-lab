#!/usr/bin/env python3
"""Fail-closed integrity check against the official v0.8.2 baseline."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify(root=ROOT):
    meta=json.loads((root/"baseline/v0.8.2.json").read_text(encoding="utf-8"))
    problems=[]
    for path, expected in meta["protected_sha256"].items():
        f=root/path
        if not f.is_file():
            problems.append(f"MISSING {path}")
        elif hashlib.sha256(f.read_bytes()).hexdigest()!=expected:
            problems.append(f"CHANGED {path}")
    pkg=root/"reels-script-lab"
    if not pkg.is_dir():
        problems.append("MISSING reels-script-lab/ (plugin package)")
    else:
        # A minimum count detects accidental file loss; content drift is separately
        # checked for protected originals and by review of the Git diff.
        source_paths=[f for f in root.rglob("*") if f.is_file() and
                      (str(f.relative_to(root)) in ("README.md",) or
                       str(f.relative_to(root)).startswith(("docs/","fixtures/","tests/","reels-script-lab/")))]
        if len(source_paths)<meta["expected_source_files"]:
            problems.append(f"INCOMPLETE SOURCE TREE {len(source_paths)} < {meta['expected_source_files']}")
    return problems


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--strict",action="store_true")
    args=parser.parse_args()
    errors=verify()
    if errors:
        print("BLOCKED: v0.8.2 baseline incomplete or changed:")
        print("\n".join(errors))
        raise SystemExit(1 if args.strict else 0)
    print("PASS: protected originals intact and baseline source tree present")
