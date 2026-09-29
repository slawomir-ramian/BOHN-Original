$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONIOENCODING = "utf-8"
& .\.venv\Scripts\python.exe -m unittest -v tests.test_stage_15
if ($LASTEXITCODE -ne 0) { throw "Testy Etapu 15 nie powiodly sie." }
& .\.venv\Scripts\python.exe tools\run_stage_15.py --smoke
if ($LASTEXITCODE -ne 0) { throw "Smoke Etapu 15 nie powiodl sie." }
Write-Host "SMOKE STAGE 15: PASS" -ForegroundColor Green
