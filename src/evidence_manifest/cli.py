from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Sequence
from .core import create_manifest, verify_manifest, write_manifest
def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="evidence-manifest",
        description="Create and verify offline SHA-256 evidence manifests.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create", help="Create a manifest")
    create.add_argument("root", type=Path)
    create.add_argument("--output", type=Path, default=Path("manifest.json"))
    create.add_argument(
        "--path-mode", choices=("relative", "hashed"), default="relative"
    )
    verify = subparsers.add_parser("verify", help="Verify a folder")
    verify.add_argument("root", type=Path)
    verify.add_argument("--manifest", type=Path, default=Path("manifest.json"))
    return parser
def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "create":
            output = args.output
            if not output.is_absolute():
                output = args.root / output
            manifest = create_manifest(
                args.root, output_path=output, path_mode=args.path_mode
            )
            write_manifest(manifest, output)
            print(
                json.dumps(
                    {"ok": True, "output": str(output), "files": manifest["file_count"]}
                )
            )
            return 0
        manifest_path = args.manifest
        if not manifest_path.is_absolute():
            manifest_path = args.root / manifest_path
        result = verify_manifest(args.root, manifest_path)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result["ok"] else 1
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 2
