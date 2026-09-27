$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Najpierw uruchom .\SETUP_STAGE_11.ps1"
}

& .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_stage_11.py" -v
if ($LASTEXITCODE -ne 0) { throw "Testy Etapu 11 nie powiodły się." }

Write-Host "Etap 11 uruchamia dwie jawne rekonstrukcje wspólnych fragmentów kodu. Wyniki są zapisywane w checkpointach." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe tools\run_stage_11.py
if ($LASTEXITCODE -ne 0) { throw "Pełny przebieg Etapu 11 nie powiódł się." }

Write-Host "FULL STAGE 11: PASS" -ForegroundColor Green
