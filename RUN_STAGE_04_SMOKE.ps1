$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Najpierw uruchom .\SETUP_STAGE_04.ps1"
}

& .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_stage_04.py" -v
& .\.venv\Scripts\python.exe tools\run_stage_04.py --smoke

Write-Host "SMOKE STAGE 04: PASS" -ForegroundColor Green
