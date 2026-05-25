#!/usr/bin/env python3
"""
extract-ids.py - Find settingDefinitionIds used by the baselines that are NOT yet in
definitions.json (the friendly-name map). Writes ids-to-resolve.json for fetch-displaynames.ps1.

Run after adding/updating baselines, before resolving names.
Usage:  python tools/extract-ids.py
"""
import json, glob
from pathlib import Path
from _common import REPO

def walk(o, ids):
    if isinstance(o, dict):
        v = o.get("settingDefinitionId")
        if isinstance(v, str):
            ids.add(v)
        for x in o.values():
            walk(x, ids)
    elif isinstance(o, list):
        for x in o:
            walk(x, ids)

def main():
    defs_path = REPO / "definitions.json"
    have = set(json.loads(defs_path.read_text(encoding="utf-8")).keys()) if defs_path.exists() else set()

    ids = set()
    # every per-policy file in any baseline folder (folders that contain manifest-referenced files)
    for f in glob.glob(str(REPO / "*" / "*.json")):
        if Path(f).name in ("manifest.json", "definitions.json"):
            continue
        try:
            walk(json.loads(Path(f).read_text(encoding="utf-8")), ids)
        except Exception:
            pass

    new = sorted(ids - have)
    out = REPO / "tools" / "ids-to-resolve.json"
    out.write_text(json.dumps(new, indent=0), encoding="utf-8")
    print(f"total unique IDs: {len(ids)} | already named: {len(ids & have)} | NEW to resolve: {len(new)}")
    print(f"wrote {out}")

if __name__ == "__main__":
    main()
