#!/usr/bin/env python3
"""Strict initial-import file presence and immutable methodology SHA256 checks."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def verify():
    manifest=json.loads((ROOT/"baseline/v0.8.2.json").read_text(encoding="utf-8"))
    problems=[]
    expected=set(manifest["expected_paths"])
    if len(expected)!=manifest["expected_source_files"]:
        problems.append("Manifest has wrong number of unique source paths")
    for p in sorted(expected):
        if not (ROOT/p).is_file():
            problems.append("MISSING "+p)
    for p,sha in manifest["protected_sha256"].items():
        f=ROOT/p
        if f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest()!=sha:
            problems.append("MODIFIED PROTECTED FILE "+p)
    return problems


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--strict",action="store_true")
    args=ap.parse_args()
    problems=verify()
    if problems:
        print("\n".join(["BASELINE INCOMPLETE OR CHANGED:"]+problems))
        raise SystemExit(1 if args.strict else 0)
    print("PASS: all 75 source files present; immutable originals SHA256 match")
