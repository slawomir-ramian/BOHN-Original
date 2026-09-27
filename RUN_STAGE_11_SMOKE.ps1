$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Najpierw uruchom .\SETUP_STAGE_11.ps1"
}

& .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_stage_11.py" -v
if ($LASTEXITCODE -ne 0) { throw "Testy Etapu 11 nie powiodły się." }

& .\.venv\Scripts\python.exe tools\run_stage_11.py --smoke
if ($LASTEXITCODE -ne 0) { throw "Smoke Etapu 11 nie powiódł się." }

Write-Host "SMOKE STAGE 11: PASS" -ForegroundColor Green
