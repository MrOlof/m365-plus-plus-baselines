<#
    fetch-displaynames.ps1 - Resolve friendly displayNames for the OIB baseline's
    settingDefinitionIds from Microsoft's settings catalog, via Graph $batch.

    Reads : tools/ids-to-resolve.json  (array of settingDefinitionId strings, from extract-ids.py)
    Writes: tools/resolved-names.json  ( { "<settingDefinitionId>": "<displayName>", ... } )
            -> then merge with: python tools/merge-definitions.py --names tools/resolved-names.json

    Read-only. Requires Microsoft.Graph.Authentication.
    Run:  .\tools\fetch-displaynames.ps1     (will prompt sign-in)
#>
[CmdletBinding()]
param(
    [string]$IdsFile = "$PSScriptRoot\ids-to-resolve.json",
    [string]$OutFile = "$PSScriptRoot\resolved-names.json"
)

$ErrorActionPreference = 'Stop'
Import-Module Microsoft.Graph.Authentication -ErrorAction Stop
Connect-MgGraph -Scopes 'DeviceManagementConfiguration.Read.All' -NoWelcome

$ids = Get-Content $IdsFile -Raw | ConvertFrom-Json
Write-Host "Resolving $($ids.Count) setting definitions..." -ForegroundColor Cyan

$map = [ordered]@{}
$batchSize = 20
for ($i = 0; $i -lt $ids.Count; $i += $batchSize) {
    $end = [Math]::Min($i + $batchSize, $ids.Count)
    $chunk = $ids[$i..($end - 1)]

    $requests = @()
    $n = 0
    foreach ($id in $chunk) {
        $n++
        $requests += @{
            id     = "$n"
            method = 'GET'
            # single-quoted key segment; $select trims the payload
            url    = "/deviceManagement/configurationSettings('$id')?`$select=id,displayName"
        }
    }
    $body = @{ requests = $requests } | ConvertTo-Json -Depth 6

    try {
        $resp = Invoke-MgGraphRequest -Method POST -Uri 'https://graph.microsoft.com/beta/$batch' -Body $body -ContentType 'application/json'
    } catch {
        Write-Host "  batch $i failed: $($_.Exception.Message)" -ForegroundColor Yellow
        continue
    }

    foreach ($r in $resp.responses) {
        if ($r.status -eq 200 -and $r.body) {
            $dn = $r.body.displayName
            $rid = $r.body.id
            if ($rid) { $map[$rid] = $dn }
        }
    }
    Write-Host ("  {0}/{1} resolved" -f $map.Count, $ids.Count)
}

$map | ConvertTo-Json -Depth 3 | Out-File $OutFile -Encoding utf8
Write-Host "Wrote $($map.Count) names to $OutFile" -ForegroundColor Green
$missing = $ids.Count - $map.Count
if ($missing -gt 0) { Write-Host "$missing IDs did not resolve (may be nested-only or deprecated); they will fall back to raw." -ForegroundColor DarkYellow }
