$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Brak środowiska Etapu 05. Uruchom najpierw SETUP_STAGE_05.ps1."
}

$runDirectory = ".\reproduced\stage_05_runs\20260923T052427Z"
if (-not (Test-Path "$runDirectory\results.json")) {
    throw "Brak pełnego wyniku Etapu 05: $runDirectory"
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
    "G-001"  = "EXACT_MATCH"
    "SO-001" = "CLOSE_MATCH"
    "SO-002" = "FORMULA_MATCH"
    "SO-003" = "FORMULA_MATCH"
    "SO-004" = "FORMULA_MATCH"
    "SO-005" = "PARTIAL_RECONSTRUCTION"
    "SO-006" = "PARTIAL_RECONSTRUCTION"
    "SO-007" = "CLOSE_MATCH"
}

$rows = Import-Csv .\inventory\experiments.csv
foreach ($id in $expected.Keys) {
    $row = $rows | Where-Object { $_.id -eq $id }
    if (($null -eq $row) -or ($row.reproduction_status -ne $expected[$id])) {
        throw "Nieprawidłowy status $id"
    }
}

$chronology = @(
    "G-001", "SO-001", "SO-002", "SO-003",
    "SO-004", "SO-005", "SO-006", "SO-007"
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
    throw "Nie wszystkie jednostki Etapu 05 mają status PASS."
}

Write-Host "STAGE 05 CLOSEOUT: PASS" -ForegroundColor Green
