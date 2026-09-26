$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Najpierw uruchom .\SETUP_STAGE_07R.ps1"
}

& .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_stage_07r.py" -v
if ($LASTEXITCODE -ne 0) { throw "Testy Etapu 07R nie powiodly sie." }

& .\.venv\Scripts\python.exe tools\run_stage_07r.py --mode full
if ($LASTEXITCODE -ne 0) { throw "Pelny przebieg Etapu 07R nie powiodl sie." }

Write-Host "STAGE 07R FULL EXECUTION: PASS" -ForegroundColor Green
