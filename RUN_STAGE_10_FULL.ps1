$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Najpierw uruchom .\SETUP_STAGE_10.ps1"
}

& .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_stage_10.py" -v
if ($LASTEXITCODE -ne 0) { throw "Testy Etapu 10 nie powiodły się." }

Write-Host "Pelny Etap 10 ma 180 komorek. Checkpoint umozliwia bezpieczne wznowienie tego samego protokolu." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe tools\run_stage_10.py
if ($LASTEXITCODE -ne 0) { throw "Pełny przebieg Etapu 10 nie powiódł się." }

Write-Host "FULL STAGE 10: PASS" -ForegroundColor Green
