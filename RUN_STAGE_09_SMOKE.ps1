$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Najpierw uruchom .\SETUP_STAGE_09.ps1"
}

& .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_stage_09.py" -v
if ($LASTEXITCODE -ne 0) { throw "Testy Etapu 09 nie powiodly sie." }

& .\.venv\Scripts\python.exe tools\run_stage_09.py --smoke
if ($LASTEXITCODE -ne 0) { throw "Smoke Etapu 09 nie powiodl sie." }

Write-Host "SMOKE STAGE 09: PASS" -ForegroundColor Green
