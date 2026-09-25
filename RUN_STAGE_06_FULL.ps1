$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Najpierw uruchom .\SETUP_STAGE_06.ps1"
}

& .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_stage_06.py" -v
if ($LASTEXITCODE -ne 0) { throw "Testy Etapu 06 nie powiodły się." }

& .\.venv\Scripts\python.exe tools\run_stage_06.py
if ($LASTEXITCODE -ne 0) { throw "Pełny przebieg Etapu 06 nie powiódł się." }

Write-Host "FULL STAGE 06: PASS" -ForegroundColor Green
