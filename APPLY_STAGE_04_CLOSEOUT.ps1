$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Brak środowiska Etapu 04. Uruchom najpierw SETUP_STAGE_04.ps1."
}

$runDirectory = ".\reproduced\stage_04_runs\20260922T221033Z"
if (-not (Test-Path "$runDirectory\results.json")) {
    throw "Brak pełnego wyniku Etapu 04: $runDirectory"
}

& .\.venv\Scripts\python.exe tools\render_inventory.py
if ($LASTEXITCODE -ne 0) {
    throw "Nie udało się zweryfikować i odtworzyć indeksu."
}

& .\.venv\Scripts\python.exe tools\render_source_chronology.py
if ($LASTEXITCODE -ne 0) {
    throw "Nie udało się zweryfikować chronologii źródłowej."
}

$expected = [ordered]@{
    "S-001" = "NONDETERMINISTIC"
    "S-002" = "REPORTED_SUPERSET_MATCH"
    "S-003" = "REPORTED_SUPERSET_MATCH"
    "S-004" = "SOURCE_BUG_PRESERVED"
    "S-005" = "CLOSE_MATCH"
    "S-006" = "EXACT_MATCH"
    "S-010" = "CONTRACT_MATCH"
    "S-011" = "EXACT_MATCH"
    "S-007" = "EXACT_MATCH"
    "S-008" = "CLOSE_MATCH"
    "S-009" = "EXACT_MATCH"
}

$rows = Import-Csv .\inventory\experiments.csv
foreach ($id in $expected.Keys) {
    $row = $rows | Where-Object { $_.id -eq $id }
    if (($null -eq $row) -or ($row.reproduction_status -ne $expected[$id])) {
        throw "Nieprawidłowy status $id"
    }
}

$chronology = @(
    "S-001", "S-002", "S-003", "S-004", "S-005", "S-006",
    "S-010", "S-011", "S-007", "S-008", "S-009"
)
$run = Get-Content "$runDirectory\results.json" -Raw | ConvertFrom-Json
$actualChronology = @($run.source_chronology)
if (($actualChronology.Count -ne $chronology.Count) -or
    ((Compare-Object $chronology $actualChronology -SyncWindow 0).Count -ne 0)) {
    throw "Pełny wynik nie zachowuje chronologii PDF-a."
}

$failed = @($run.experiments.PSObject.Properties | Where-Object {
    $_.Value.execution_status -ne "PASS"
})
if ($failed.Count -ne 0) {
    throw "Nie wszystkie jednostki Etapu 04 mają status PASS."
}

Write-Host "STAGE 04 CLOSEOUT: PASS" -ForegroundColor Green
