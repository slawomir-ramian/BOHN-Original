$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Najpierw uruchom .\SETUP_STAGE_05.ps1"
}

& .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_stage_05.py" -v
if ($LASTEXITCODE -ne 0) { throw "Testy Etapu 05 nie powiodły się." }

& .\.venv\Scripts\python.exe tools\run_stage_05.py --smoke
if ($LASTEXITCODE -ne 0) { throw "Smoke Etapu 05 nie powiódł się." }

Write-Host "SMOKE STAGE 05: PASS" -ForegroundColor Green
