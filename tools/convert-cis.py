#!/usr/bin/env python3
"""
convert-cis.py - Merge a folder of single-policy Graph configurationPolicy exports
(e.g. Jan Mulder's IntuneBaselines CIS set, which are UTF-16 and one recommendation
per file) into ONE baseline in this repo, and upsert its manifest entry.

Each file's policy name becomes the per-setting _sourcePolicy (provenance). Duplicate
settingDefinitionIds across files are kept; the comparison engine flattens nested
parents (e.g. ASR rules) into distinct leaves and notes any true self-overlap.

This baseline is re-hosting a third party's MIT-licensed work — credit the author and
keep their license notice (see --credit/--license/--source; defaults to Jan Mulder/MIT).

Usage:
  python tools/convert-cis.py --src "<path>/CIS -  Intune for Windows 11 Benchmarks" \
    --id cis-windows11-v4 --name "CIS - Intune for Windows 11 (v4.0)" --version 4.0 \
    --folder cis-windows11-v4
"""
import json, argparse
from pathlib import Path
from _common import REPO, slugify, load_manifest, upsert_baseline, save_manifest

def read_any(path: Path) -> dict:
    raw = path.read_bytes()
    if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return json.loads(raw.decode('utf-16'))
    return json.loads(raw.decode('utf-8-sig'))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="folder of single-policy JSON exports")
    ap.add_argument("--id", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--folder", required=True)
    ap.add_argument("--platform", default="windows10")
    ap.add_argument("--credit", default="Jan Mulder (IntuneAdmin)")
    ap.add_argument("--license", default="MIT (author's interpretation of CIS Benchmark; not affiliated with CIS)")
    ap.add_argument("--source", default="https://github.com/IntuneAdmin/IntuneBaselines")
    args = ap.parse_args()

    files = sorted(Path(args.src).glob("*.json"))
    if not files:
        raise SystemExit(f"No JSON files in {args.src}")

    merged_settings, dup = [], 0
    seen = set()
    for f in files:
        d = read_any(f)
        pol = d.get("policy", d)
        src_name = pol.get("name", f.stem)
        for s in pol.get("settings", []):
            si = s.get("settingInstance")
            if not si:
                continue
            sid = si.get("settingDefinitionId")
            if sid in seen:
                dup += 1
            seen.add(sid)
            merged_settings.append({"settingDefinitionId": sid, "settingInstance": si, "_sourcePolicy": src_name})

    slug = slugify(args.name)
    out_dir = REPO / args.folder
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{slug}.json").write_text(
        json.dumps({"sourcePolicy": args.name, "settingCount": len(merged_settings), "settings": merged_settings},
                   indent=2, ensure_ascii=False), encoding="utf-8")

    manifest = load_manifest()
    upsert_baseline(manifest, {
        "id": args.id, "name": args.name, "version": args.version,
        "credit": args.credit, "license": args.license, "source": args.source,
        "platform": args.platform, "policyCount": 1, "totalSettings": len(merged_settings),
        "policies": [{"slug": slug, "sourcePolicy": args.name, "settingCount": len(merged_settings),
                      "file": f"{args.folder}/{slug}.json"}],
    })
    save_manifest(manifest)
    print(f"Merged {len(files)} files -> {len(merged_settings)} settings ({dup} duplicate IDs kept) -> {args.folder}/{slug}.json")

if __name__ == "__main__":
    main()
