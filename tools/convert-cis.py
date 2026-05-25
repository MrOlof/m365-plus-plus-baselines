#!/usr/bin/env python3
"""
convert-cis.py - Convert a folder of single-policy Graph configurationPolicy exports
(e.g. Jan Mulder's IntuneBaselines CIS set - UTF-16, one recommendation per file) into
GRANULAR per-recommendation baseline files (like OIB), and upsert the manifest entry.

Granular (one file per recommendation) is deliberate: it preserves per-setting
provenance (a referenced setting traces to its exact recommendation file) and lets the
picker select all OR a subset. The extension tags each setting's _sourcePolicy from the
file's sourcePolicy at merge time.

Re-hosting a third party's MIT work - credit the author + keep their notice
(defaults to Jan Mulder / IntuneAdmin, MIT; author's interpretation of CIS, not CIS-affiliated).

Usage:
  python tools/convert-cis.py --src "<path>/CIS -  Intune for Windows 11 Benchmarks" \
    --id cis-windows11-v4 --name "CIS - Intune for Windows 11 (v4.0)" --version 4.0 --folder cis-windows11-v4
"""
import json, argparse
from pathlib import Path
from _common import REPO, slugify, load_manifest, upsert_baseline, save_manifest, settings_from_policy

def read_any(path: Path) -> dict:
    raw = path.read_bytes()
    if raw[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return json.loads(raw.decode('utf-16'))
    return json.loads(raw.decode('utf-8-sig'))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
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

    out_dir = REPO / args.folder
    out_dir.mkdir(parents=True, exist_ok=True)

    policies_index, total, seen = [], 0, {}
    for f in files:
        d = read_any(f)
        pol = d.get("policy", d)
        name = pol.get("name", f.stem)
        settings = settings_from_policy(pol)
        slug = slugify(name)
        if slug in seen:
            seen[slug] += 1
            slug = f"{slug}-{seen[slug]}"
        else:
            seen[slug] = 0
        (out_dir / f"{slug}.json").write_text(
            json.dumps({"sourcePolicy": name, "settingCount": len(settings), "settings": settings},
                       indent=2, ensure_ascii=False), encoding="utf-8")
        policies_index.append({"slug": slug, "sourcePolicy": name, "settingCount": len(settings),
                               "file": f"{args.folder}/{slug}.json"})
        total += len(settings)

    manifest = load_manifest()
    upsert_baseline(manifest, {
        "id": args.id, "name": args.name, "version": args.version,
        "credit": args.credit, "license": args.license, "source": args.source,
        "platform": args.platform, "policyCount": len(policies_index), "totalSettings": total,
        "policies": policies_index,
    })
    save_manifest(manifest)
    print(f"Converted {len(files)} recommendations -> {len(policies_index)} files / {total} settings -> {args.folder}/")

if __name__ == "__main__":
    main()
