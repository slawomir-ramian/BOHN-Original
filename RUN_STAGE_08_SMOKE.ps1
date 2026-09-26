$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Najpierw uruchom .\SETUP_STAGE_08.ps1"
}

& .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_stage_08.py" -v
if ($LASTEXITCODE -ne 0) { throw "Testy Etapu 08 nie powiodly sie." }

& .\.venv\Scripts\python.exe tools\run_stage_08.py --smoke
if ($LASTEXITCODE -ne 0) { throw "Smoke Etapu 08 nie powiodl sie." }

Write-Host "SMOKE STAGE 08: PASS" -ForegroundColor Green
