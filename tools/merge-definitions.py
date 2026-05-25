#!/usr/bin/env python3
"""
merge-definitions.py - Merge a resolved names file ({settingDefinitionId: displayName})
into the repo's shared definitions.json. Strips any BOM. Writes clean UTF-8 (no BOM).

Usage:  python tools/merge-definitions.py --names tools/resolved-names.json
"""
import json, argparse
from pathlib import Path
from _common import REPO

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--names", required=True, help="JSON {id: displayName} from fetch-displaynames.ps1")
    args = ap.parse_args()

    defs_path = REPO / "definitions.json"
    existing = json.loads(defs_path.read_text(encoding="utf-8")) if defs_path.exists() else {}
    new = json.loads(Path(args.names).read_text(encoding="utf-8-sig"))  # tolerate PS BOM

    before = len(existing)
    existing.update(new)
    defs_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")  # no BOM
    print(f"definitions.json: {before} -> {len(existing)} (+{len(existing) - before})")

if __name__ == "__main__":
    main()
