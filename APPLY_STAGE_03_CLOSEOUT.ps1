$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Brak środowiska Etapu 03. Uruchom najpierw SETUP_STAGE_03.ps1."
}

& .\.venv\Scripts\python.exe tools\render_inventory.py

$expected = @{
    "B-001" = "EXACT_MATCH"
    "B-002" = "EXACT_MATCH"
    "B-003" = "EXACT_MATCH"
    "B-004" = "CLOSE_MATCH"
    "B-005" = "DIVERGENT"
    "B-006" = "PARTIAL"
    "B-007" = "DIVERGENT"
    "B-008" = "DIVERGENT"
    "B-009" = "CLOSE_MATCH"
}

$rows = Import-Csv .\inventory\experiments.csv
foreach ($id in $expected.Keys) {
    $row = $rows | Where-Object { $_.id -eq $id }
    if (($null -eq $row) -or ($row.reproduction_status -ne $expected[$id])) {
        throw "Nieprawidłowy status $id"
    }
}

Write-Host "STAGE 03 CLOSEOUT: PASS" -ForegroundColor Green
