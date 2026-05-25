# m365-plus-plus-baselines

Pre-converted Intune **Settings Catalog** baselines, served as read-only reference
data for the [M365++ extension](https://github.com/MrOlof/m365-plus-plus)'s policy
comparison feature. The extension fetches these files at runtime to compare a
tenant's policies against a baseline — nothing here is deployed to any tenant.

## Attribution

The `oib-windows` baseline is **derived from [OpenIntuneBaseline](https://github.com/SkipToTheEndpoint/OpenIntuneBaseline)
by SkipToTheEndpoint (James Robinson)**, licensed under **GPL-3.0**.

This repository's OpenIntuneBaseline-derived content is therefore also licensed
under **GPL-3.0** (see `LICENSE`). Full credit for the baseline content and its
curation belongs to the OpenIntuneBaseline project. This repo only reformats the
published Settings Catalog exports into a flat structure for runtime consumption.

Upstream source: https://github.com/SkipToTheEndpoint/OpenIntuneBaseline

The `cis-windows11-v4` baseline is **derived from [IntuneBaselines](https://github.com/IntuneAdmin/IntuneBaselines)
by Jan Mulder (IntuneAdmin)**, an author's interpretation of the CIS Benchmark for
Intune, licensed **MIT**. Re-hosted here under MIT with the notice below; full credit
for the curation belongs to Jan Mulder. Not affiliated with or endorsed by CIS.

```
MIT License — Copyright (c) 2025 Jan Mulder
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction... (full text: https://github.com/IntuneAdmin/IntuneBaselines/blob/main/LICENSE)
```

The `ms-windows-25h2` and `ms-edge-139` baselines are pristine deploy-at-defaults
snapshots of Microsoft Security Baselines, credited to Microsoft.

## Structure

```
manifest.json              # index of available baselines + their policies
oib-windows/<slug>.json    # one file per source policy
```

### manifest.json

```jsonc
{ "baselines": [ {
  "id": "oib-windows-v3.8",
  "name": "OpenIntuneBaseline - Windows",
  "version": "3.8",
  "credit": "SkipToTheEndpoint",
  "license": "GPL-3.0",
  "source": "https://github.com/SkipToTheEndpoint/OpenIntuneBaseline",
  "platform": "windows10",
  "policyCount": 62,
  "totalSettings": 784,
  "policies": [
    { "slug": "...", "sourcePolicy": "Win - OIB - SC - ...", "settingCount": 27, "file": "oib-windows/<slug>.json" }
  ]
} ] }
```

### per-policy file

```jsonc
{
  "sourcePolicy": "Win - OIB - SC - Defender Antivirus - D - Additional Configuration - v3.8",
  "settingCount": 9,
  "settings": [
    {
      "settingDefinitionId": "device_vendor_msft_defender_configuration_...",
      "settingInstance": { /* raw Graph deviceManagementConfigurationSettingInstance, @odata.type intact */ }
    }
  ]
}
```

`settingInstance` is the unmodified Graph setting instance (the comparison engine
relies on its `@odata.type`). `settingDefinitions` are intentionally not included —
friendly display names resolve from the live Microsoft setting catalog at compare time.

## Updating

When OpenIntuneBaseline publishes a new version, re-run the conversion script
against the upstream `WINDOWS/IntuneManagement/SettingsCatalog` folder and replace
`manifest.json` + `oib-windows/`.

## Disclaimer

Not affiliated with or endorsed by Microsoft. Intune is a trademark of Microsoft
Corporation. Baseline content originates from the OpenIntuneBaseline project; see
Attribution above.
