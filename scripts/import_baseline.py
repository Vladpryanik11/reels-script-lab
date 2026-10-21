#!/usr/bin/env python3
"""Safely import exactly the v0.8.2 workspace ZIP; never silently overwrite files."""
import hashlib
import json
import pathlib
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = json.loads((ROOT / "baseline/v0.8.2.json").read_text(encoding="utf-8"))
PREFIX = "reels-script-lab-universal-v0.8.2/"


def import_zip(archive_path):
    source = pathlib.Path(archive_path)
    if hashlib.sha256(source.read_bytes()).hexdigest() != SPEC["archive_sha256"]:
        raise ValueError("Source archive SHA256 mismatch")
    with zipfile.ZipFile(source) as archive:
        members = [m for m in archive.infolist() if not m.is_dir()]
        if len(members) != 75:
            raise ValueError(f"Expected 75 source files, got {len(members)}")
        expected = set(SPEC["expected_paths"])
        received = {}
        for member in members:
            if not member.filename.startswith(PREFIX):
                raise ValueError("Unexpected archive path prefix")
            raw = member.filename[len(PREFIX):]
            rel = pathlib.PurePosixPath(raw)
            if not raw or rel.is_absolute() or ".." in rel.parts:
                raise ValueError("Invalid ZIP entry path")
            if raw == "README.md":
                rel = pathlib.PurePosixPath("docs/history/v0.8.2-workspace-README.md")
            path = str(rel)
            if path not in expected or path in received:
                raise ValueError(f"Unexpected/duplicate entry: {path}")
            content = archive.read(member)
            existing = ROOT.joinpath(*rel.parts)
            if existing.exists() and existing.read_bytes() != content:
                raise ValueError(f"Refusing overwrite of divergent file: {path}")
            received[path] = (existing, content)
        if set(received) != expected:
            raise ValueError("Missing original paths: " + repr(sorted(expected-set(received))))
        # All possible failures checked before any writes.
        todo = [(file, data) for file, data in received.values() if not file.exists()]
        for file, data in todo:
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(data)
    return len(todo)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/import_baseline.py PATH_TO_v0.8.2.zip")
    try:
        n = import_zip(sys.argv[1])
    except (ValueError, OSError, zipfile.BadZipFile) as exc:
        sys.exit("BLOCKED: " + str(exc))
    print(f"IMPORTED {n} files; no existing sources changed")
