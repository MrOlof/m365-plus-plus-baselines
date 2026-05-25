<#
    fetch-value-labels.ps1 - Resolve friendly VALUE labels for baseline settings.

    For each settingDefinitionId in definitions.json, fetch its FULL definition from
    Microsoft's settings catalog and extract the choice options (itemId -> displayName).
    Simple settings (string/int) have no options and are skipped (the raw value IS the value).

    Reads : ../definitions.json   (keys = all baseline settingDefinitionIds)
    Writes: ../value-labels.json   ( { "<settingDefinitionId>": { "<itemId>": "<label>" }, ... } )

    Read-only. Requires Microsoft.Graph.Authentication.
    Run:  .\tools\fetch-value-labels.ps1     (will prompt sign-in)
#>
[CmdletBinding()]
param(
    [string]$DefsFile = "$PSScriptRoot\..\definitions.json",
    [string]$OutFile  = "$PSScriptRoot\..\value-labels.json"
)

$ErrorActionPreference = 'Stop'
Import-Module Microsoft.Graph.Authentication -ErrorAction Stop
Connect-MgGraph -Scopes 'DeviceManagementConfiguration.Read.All' -NoWelcome

$ids = (Get-Content $DefsFile -Raw | ConvertFrom-Json).PSObject.Properties.Name
Write-Host "Fetching full definitions for $($ids.Count) settings..." -ForegroundColor Cyan

$map = [ordered]@{}
$withOptions = 0
$batchSize = 20
for ($i = 0; $i -lt $ids.Count; $i += $batchSize) {
    $end = [Math]::Min($i + $batchSize, $ids.Count)
    $chunk = $ids[$i..($end - 1)]

    $requests = @()
    $n = 0
    foreach ($id in $chunk) {
        $n++
        $requests += @{ id = "$n"; method = 'GET'; url = "/deviceManagement/configurationSettings('$id')" }
    }
    $body = @{ requests = $requests } | ConvertTo-Json -Depth 6

    try {
        $resp = Invoke-MgGraphRequest -Method POST -Uri 'https://graph.microsoft.com/beta/$batch' -Body $body -ContentType 'application/json'
    } catch {
        Write-Host "  batch $i failed: $($_.Exception.Message)" -ForegroundColor Yellow
        continue
    }

    foreach ($r in $resp.responses) {
        if ($r.status -ne 200 -or -not $r.body) { continue }
        $def = $r.body
        $opts = $def.options
        if ($opts) {
            $inner = [ordered]@{}
            foreach ($o in $opts) {
                if ($o.itemId) { $inner[[string]$o.itemId] = [string]$o.displayName }
            }
            if ($inner.Count -gt 0) {
                $map[[string]$def.id] = $inner
                $withOptions++
            }
        }
    }
    Write-Host ("  processed {0}/{1} | {2} with options" -f $end, $ids.Count, $withOptions)
}

$map | ConvertTo-Json -Depth 4 | Out-File $OutFile -Encoding utf8
Write-Host "Wrote value labels for $withOptions choice settings to $OutFile" -ForegroundColor Green
