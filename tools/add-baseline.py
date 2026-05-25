#!/usr/bin/env python3
"""
add-baseline.py - Add a single-policy baseline (a Microsoft Security Baseline export,
or your own authored policy) from an M365++ export JSON, and upsert its manifest entry.

For Microsoft baselines: deploy the baseline profile at DEFAULT values, export it from
the extension, and pass it here. Label honestly with the real version.

Usage:
  python tools/add-baseline.py --export "<path>/Kosta test__xxxx.json" \
    --id ms-windows-25h2 --name "Security Baseline for Windows 10 and later - 25H2" \
    --version 25H2 --folder ms-windows-25h2 --policy-name "Security Baseline for Windows 10 and later - 25H2"
  # credit/license/source default to Microsoft; override for your own baseline.
"""
import json, argparse
from pathlib import Path
from _common import REPO, slugify, load_manifest, upsert_baseline, save_manifest, settings_from_policy

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", required=True, help="M365++ export JSON (single policy)")
    ap.add_argument("--id", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--folder", required=True)
    ap.add_argument("--policy-name", required=True)
    ap.add_argument("--platform", default="windows10")
    ap.add_argument("--credit", default="Microsoft")
    ap.add_argument("--license", default="Microsoft product content (Security Baseline, deployed at default values)")
    ap.add_argument("--source", default="https://learn.microsoft.com/mem/intune/protect/security-baselines")
    args = ap.parse_args()

    d = json.loads(Path(args.export).read_text(encoding="utf-8-sig"))
    pol = d.get("policy", d)
    settings = settings_from_policy(pol)
    sl = slugify(args.policy_name)

    out_dir = REPO / args.folder
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{sl}.json").write_text(
        json.dumps({"sourcePolicy": args.policy_name, "settingCount": len(settings), "settings": settings},
                   indent=2, ensure_ascii=False), encoding="utf-8")

    manifest = load_manifest()
    upsert_baseline(manifest, {
        "id": args.id, "name": args.name, "version": args.version,
        "credit": args.credit, "license": args.license, "source": args.source,
        "platform": args.platform, "policyCount": 1, "totalSettings": len(settings),
        "policies": [{"slug": sl, "sourcePolicy": args.policy_name, "settingCount": len(settings),
                      "file": f"{args.folder}/{sl}.json"}],
    })
    save_manifest(manifest)
    print(f"Added '{args.name}': {len(settings)} settings -> {args.folder}/{sl}.json. Manifest upserted.")

if __name__ == "__main__":
    main()
