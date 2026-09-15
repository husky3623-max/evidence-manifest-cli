from __future__ import annotations
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Literal
PathMode = Literal["relative", "hashed"]
FORMAT_VERSION = 1
DEFAULT_EXCLUDED_DIRS = {".git", "__pycache__"}
def _utc_iso(timestamp: float) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )
def _sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()
def _path_identifier(relative_path: str) -> str:
    return hashlib.sha256(relative_path.encode("utf-8")).hexdigest()
def _iter_files(root: Path, excluded_relative_paths: set[str]) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in DEFAULT_EXCLUDED_DIRS for part in relative.parts):
            continue
        normalized = relative.as_posix()
        if path.is_file() and normalized not in excluded_relative_paths:
            yield path
def create_manifest(
    root: Path,
    *,
    output_path: Path | None = None,
    path_mode: PathMode = "relative",
) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")
    if path_mode not in {"relative", "hashed"}:
        raise ValueError(f"Unsupported path mode: {path_mode}")
    excluded: set[str] = set()
    if output_path is not None:
        resolved_output = output_path.resolve()
        try:
            excluded.add(resolved_output.relative_to(root).as_posix())
        except ValueError:
            pass
    entries: list[dict[str, Any]] = []
    paths_by_digest: dict[str, list[str]] = defaultdict(list)
    for path in _iter_files(root, excluded):
        relative = path.relative_to(root).as_posix()
        identifier = relative if path_mode == "relative" else _path_identifier(relative)
        digest = _sha256_file(path)
        stat = path.stat()
        entry = {
            "path" if path_mode == "relative" else "path_id": identifier,
            "size_bytes": stat.st_size,
            "modified_at_utc": _utc_iso(stat.st_mtime),
            "sha256": digest,
        }
        entries.append(entry)
        paths_by_digest[digest].append(identifier)
    duplicates = [
        {"sha256": digest, "files": identifiers}
        for digest, identifiers in sorted(paths_by_digest.items())
        if len(identifiers) > 1
    ]
    return {
        "format_version": FORMAT_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        ),
        "hash_algorithm": "sha256",
        "path_mode": path_mode,
        "file_count": len(entries),
        "entries": entries,
        "duplicate_groups": duplicates,
    }
def write_manifest(manifest: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
def load_manifest(manifest_path: Path) -> dict[str, Any]:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if data.get("format_version") != FORMAT_VERSION:
        raise ValueError("Unsupported manifest format version")
    if data.get("hash_algorithm") != "sha256":
        raise ValueError("Unsupported hash algorithm")
    if data.get("path_mode") not in {"relative", "hashed"}:
        raise ValueError("Unsupported path mode")
    return data
def verify_manifest(root: Path, manifest_path: Path) -> dict[str, Any]:
    root = root.resolve()
    manifest_path = manifest_path.resolve()
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")
    manifest = load_manifest(manifest_path)
    path_mode: PathMode = manifest["path_mode"]
    excluded: set[str] = set()
    try:
        excluded.add(manifest_path.relative_to(root).as_posix())
    except ValueError:
        pass
    current: dict[str, Path] = {}
    for path in _iter_files(root, excluded):
        relative = path.relative_to(root).as_posix()
        identifier = relative if path_mode == "relative" else _path_identifier(relative)
        current[identifier] = path
    key = "path" if path_mode == "relative" else "path_id"
    expected = {entry[key]: entry for entry in manifest["entries"]}
    missing = sorted(set(expected) - set(current))
    unexpected = sorted(set(current) - set(expected))
    modified: list[str] = []
    for identifier in sorted(set(expected) & set(current)):
        entry = expected[identifier]
        path = current[identifier]
        if path.stat().st_size != entry["size_bytes"] or _sha256_file(path) != entry["sha256"]:
            modified.append(identifier)
    return {
        "ok": not missing and not unexpected and not modified,
        "missing": missing,
        "unexpected": unexpected,
        "modified": modified,
        "checked_files": len(expected),
        "path_mode": path_mode,
    }
