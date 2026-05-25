"""Shared helpers for the baseline tooling. Repo root is the parent of tools/."""
import json, re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

def slugify(s: str) -> str:
    s = re.sub(r'^win - oib - ', '', s.lower().strip())
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')

def load_manifest() -> dict:
    p = REPO / "manifest.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"baselines": []}

def upsert_baseline(manifest: dict, entry: dict) -> None:
    """Replace an existing baseline with the same id, else append. Idempotent re-runs."""
    bls = manifest.setdefault("baselines", [])
    for i, b in enumerate(bls):
        if b.get("id") == entry["id"]:
            bls[i] = entry
            return
    bls.append(entry)

def save_manifest(manifest: dict) -> None:
    (REPO / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

def settings_from_policy(policy: dict) -> list:
    """Extract [{settingDefinitionId, settingInstance}] from a Graph configurationPolicy."""
    out = []
    for s in policy.get("settings", []):
        si = s.get("settingInstance")
        if not si:
            continue
        out.append({"settingDefinitionId": si.get("settingDefinitionId"), "settingInstance": si})
    return out
