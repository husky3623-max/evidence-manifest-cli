# Evidence Manifest CLI
A small, offline-first command-line tool for creating and verifying SHA-256 manifests for local evidence folders.
It is designed for people who need a reproducible integrity record without uploading their files or exposing file contents to a third-party service.
## Privacy model
- Runs locally and has no network code.
- Reads file bytes only to calculate SHA-256 hashes.
- Never stores file contents in the manifest.
- Uses relative paths, never absolute paths.
- Supports `--path-mode hashed` when filenames are sensitive.
- Excludes `.git` and the output manifest by default.
Hashes prove that bytes have not changed since a manifest was created. They do not prove who created a file, when an event happened, or whether the contents are true.
## Quick start
Requires Python 3.10 or newer and has no runtime dependencies.
```powershell
python -m evidence_manifest create C:\path\to\folder --output manifest.json
python -m evidence_manifest verify C:\path\to\folder --manifest manifest.json
```
To avoid recording filenames:
```powershell
python -m evidence_manifest create C:\path\to\folder --path-mode hashed
```
## Manifest format
Each entry records a relative path (or deterministic path identifier), byte size, UTC modification time, and SHA-256 digest. Files with identical content are also reported in duplicate groups.
The format is versioned. JSON output is sorted and indented to make reviews and diffs straightforward.
## Development
```powershell
python -m unittest discover -s tests -v
```
See [CONTRIBUTING.md](CONTRIBUTING.md) before proposing a change and [SECURITY.md](SECURITY.md) for private vulnerability reporting guidance.
## Status
This is an early-stage project. The command and manifest format may evolve before version 1.0. Real-world feedback and narrowly scoped contributions are welcome.
## License
MIT
