# Baseline tooling

Reproducible pipeline that builds this repo's baseline registry (`manifest.json`,
the per-baseline policy folders, and the shared `definitions.json` name map).
All paths are repo-relative — run from the repo root with Python 3 + (for names)
PowerShell with the `Microsoft.Graph.Authentication` module.

## What's here
- `_common.py` — shared helpers (slugify, manifest upsert, settings extraction).
- `convert-oib.py` — OpenIntuneBaseline IntuneManagement export folder -> `oib-windows/` + manifest entry.
- `add-baseline.py` — a single-policy M365++ export (Microsoft baseline or your own) -> a baseline folder + manifest entry.
- `extract-ids.py` — find settingDefinitionIds used by the baselines but NOT yet in `definitions.json` -> `tools/ids-to-resolve.json`.
- `fetch-displaynames.ps1` — resolve those IDs to friendly names via Graph `$batch` -> `tools/resolved-names.json`.
- `merge-definitions.py` — merge a resolved-names file into the shared `definitions.json` (strips BOM).

`ids-to-resolve.json` / `resolved-names.json` are transient (gitignored).

## Add or update a baseline

### A. OpenIntuneBaseline (when OIB versions up)
1. Clone/download OIB somewhere (NOT committed here — it's GPL upstream):
   `git clone https://github.com/SkipToTheEndpoint/OpenIntuneBaseline`
2. `python tools/convert-oib.py --src "<OIB>/WINDOWS/IntuneManagement/SettingsCatalog" --version <X.Y>`

### B. A Microsoft Security Baseline (or your own single policy)
1. Deploy the baseline profile at **default values**, export it from the M365++ extension.
2. `python tools/add-baseline.py --export "<export>.json" --id ms-windows-25h2 \
      --name "Security Baseline for Windows 10 and later - 25H2" --version 25H2 \
      --folder ms-windows-25h2 --policy-name "Security Baseline for Windows 10 and later - 25H2"`
   (override `--credit/--license/--source` for a self-authored baseline.)

### Then, for ALL baselines — resolve friendly names
3. `python tools/extract-ids.py`            # writes tools/ids-to-resolve.json (only the NEW ids)
4. `.\tools\fetch-displaynames.ps1`         # Graph sign-in; writes tools/resolved-names.json
5. `python tools/merge-definitions.py --names tools/resolved-names.json`
6. `git add -A && git commit -m "..." && git push`

The extension fetches `manifest.json` + the selected policy files + `definitions.json`
at runtime. Adding a baseline is pure data here — no extension change. `definitions.json`
is shared and cumulative, so a new baseline only costs the names of its genuinely-new IDs.

## Licensing
- `oib-windows/*` is derived from OpenIntuneBaseline (SkipToTheEndpoint), GPL-3.0 — this repo is GPL-3.0.
- Microsoft baselines are pristine deploy-at-defaults snapshots, credited to Microsoft.
- Do NOT add CIS content (SecureSuite Terms of Use + trademark). Users bring their own, or author an original baseline.
