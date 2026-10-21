#!/usr/bin/env python3
"""Safe importer for the immutable v0.8.2 workspace archive; uses only stdlib."""
import hashlib
import json
import pathlib
import sys
import zipfile

REPO = pathlib.Path(__file__).resolve().parents[1]
META = json.loads((REPO / "baseline/v0.8.2.json").read_text(encoding="utf-8"))
ARCHIVE_PREFIX = "reels-script-lab-universal-v0.8.2/"


def import_zip(path: pathlib.Path) -> int:
    if hashlib.sha256(path.read_bytes()).hexdigest() != META["archive_sha256"]:
        raise ValueError("Wrong input ZIP SHA256: refusing to import")
    with zipfile.ZipFile(path) as archive:
        members = [m for m in archive.infolist() if not m.is_dir()]
        if len(members) != META["expected_source_files"]:
            raise ValueError(f"Expected {META['expected_source_files']} source files; found {len(members)}")
        pending = []
        for member in members:
            if not member.filename.startswith(ARCHIVE_PREFIX):
                raise ValueError("Unexpected ZIP prefix")
            relative = pathlib.PurePosixPath(member.filename[len(ARCHIVE_PREFIX):])
            if not relative.parts or ".." in relative.parts or relative.is_absolute():
                raise ValueError("Unsafe ZIP path")
            target = REPO.joinpath(*relative.parts)
            content = archive.read(member)
            if target.exists():
                if target.read_bytes() != content:
                    raise ValueError(f"Existing file differs; refusing overwrite: {relative}")
            else:
                pending.append((target, content))
        for target, content in pending:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
    return len(pending)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/import_baseline.py /path/to/workspace-v0.8.2.zip")
    try:
        count = import_zip(pathlib.Path(sys.argv[1]))
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        sys.exit(f"Import BLOCKED: {exc}")
    print(f"Imported {count} source files, without overwriting existing files")
