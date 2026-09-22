$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Najpierw uruchom .\SETUP_STAGE_03.ps1"
}

& .\.venv\Scripts\python.exe tools\extract_bohn_foundation.py
& .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_stage_03.py" -v
& .\.venv\Scripts\python.exe tools\run_stage_03.py --smoke

Write-Host "SMOKE STAGE 03: PASS" -ForegroundColor Green
