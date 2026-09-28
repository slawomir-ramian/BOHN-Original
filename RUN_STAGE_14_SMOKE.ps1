$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONIOENCODING = "utf-8"
& .\.venv\Scripts\python.exe -m unittest -v tests.test_stage_14
if ($LASTEXITCODE -ne 0) { throw "Testy Etapu 14 nie powiodly sie." }
& .\.venv\Scripts\python.exe tools\run_stage_14.py --smoke
if ($LASTEXITCODE -ne 0) { throw "Smoke Etapu 14 nie powiodl sie." }
Write-Host "SMOKE STAGE 14: PASS" -ForegroundColor Green
