#!/usr/bin/env python3
"""Reusable host-side primitives for structural build evidence."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Any, Iterable, Sequence


def resolve_executable(value: str) -> str:
    resolved = shutil.which(value)
    if resolved is None:
        raise RuntimeError(f"required executable is unavailable: {value}")
    return resolved


def decode_json_stream(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    decoder = json.JSONDecoder()
    records: list[dict[str, Any]] = []
    offset = 0
    while offset < len(text):
        while offset < len(text) and text[offset].isspace():
            offset += 1
        if offset == len(text):
            break
        value, offset = decoder.raw_decode(text, offset)
        if isinstance(value, dict):
            records.append(value)
        elif isinstance(value, list):
            records.extend(item for item in value if isinstance(item, dict))
    return records


def action_name(label: str) -> str:
    if "//:" not in label:
        return label
    return label.rsplit("//:", 1)[1]


def mnemonic_records(
    records: Iterable[dict[str, Any]],
    mnemonic: str,
) -> list[dict[str, Any]]:
    return [record for record in records if record.get("mnemonic") == mnemonic]


def command_output(command: Sequence[str], workspace: Path) -> str:
    completed = subprocess.run(
        command,
        cwd=workspace,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    output = completed.stdout.strip()
    if completed.returncode != 0:
        diagnostic = completed.stderr.strip() or output
        raise RuntimeError(f"command failed ({completed.returncode}): {diagnostic}")
    if not output:
        raise RuntimeError(f"command produced no output: {' '.join(command)}")
    return output.splitlines()[-1]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def remove_tree(path: Path) -> None:
    if not path.exists():
        return
    for root, directories, _files in os.walk(
        path,
        topdown=True,
        followlinks=False,
    ):
        root_path = Path(root)
        root_path.chmod(
            root_path.stat(follow_symlinks=False).st_mode
            | stat.S_IRUSR
            | stat.S_IWUSR
            | stat.S_IXUSR
        )
        directories[:] = [
            directory
            for directory in directories
            if not (root_path / directory).is_symlink()
        ]
    shutil.rmtree(path)
