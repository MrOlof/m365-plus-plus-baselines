#!/usr/bin/env python3
"""
convert-oib.py - Convert an OpenIntuneBaseline IntuneManagement SettingsCatalog
export folder into this repo's baseline format, and upsert its manifest entry.

OIB is GPL-3.0 by SkipToTheEndpoint. This repo (and its OIB-derived output) is GPL-3.0.

Usage:
  python tools/convert-oib.py --src "<path-to>/OpenIntuneBaseline/WINDOWS/IntuneManagement/SettingsCatalog" --version 3.8
"""
import json, argparse
from pathlib import Path
from _common import REPO, slugify, load_manifest, upsert_baseline, save_manifest, settings_from_policy

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="OIB .../IntuneManagement/SettingsCatalog folder")
    ap.add_argument("--version", default="3.8")
    ap.add_argument("--folder", default="oib-windows", help="output subfolder + baseline id stem")
    args = ap.parse_args()

    src = Path(args.src)
    files = sorted(src.glob("*.json"))
    if not files:
        raise SystemExit(f"No JSON files in {src}")

    out_dir = REPO / args.folder
    out_dir.mkdir(parents=True, exist_ok=True)

    policies_index, total = [], 0
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8-sig"))
        pol = d.get("policy", d)
        name = pol.get("name", f.stem)
        settings = settings_from_policy(pol)
        sl = slugify(name)
        (out_dir / f"{sl}.json").write_text(
            json.dumps({"sourcePolicy": name, "settingCount": len(settings), "settings": settings},
                       indent=2, ensure_ascii=False), encoding="utf-8")
        policies_index.append({"slug": sl, "sourcePolicy": name, "settingCount": len(settings),
                               "file": f"{args.folder}/{sl}.json"})
        total += len(settings)

    manifest = load_manifest()
    upsert_baseline(manifest, {
        "id": f"{args.folder}-v{args.version}",
        "name": "OpenIntuneBaseline - Windows",
        "version": args.version,
        "credit": "SkipToTheEndpoint",
        "license": "GPL-3.0",
        "source": "https://github.com/SkipToTheEndpoint/OpenIntuneBaseline",
        "platform": "windows10",
        "policyCount": len(policies_index),
        "totalSettings": total,
        "policies": policies_index,
    })
    save_manifest(manifest)
    print(f"Converted {len(files)} policies, {total} settings -> {args.folder}/. Manifest upserted.")

if __name__ == "__main__":
    main()
