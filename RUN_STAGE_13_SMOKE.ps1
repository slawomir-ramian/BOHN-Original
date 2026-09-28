$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONIOENCODING = "utf-8"
& .\.venv\Scripts\python.exe -m unittest -v tests.test_stage_13
if ($LASTEXITCODE -ne 0) { throw "Testy Etapu 13 nie powiodly sie." }
& .\.venv\Scripts\python.exe tools\run_stage_13.py --smoke
if ($LASTEXITCODE -ne 0) { throw "Sonda Etapu 13 nie powiodla sie." }
Write-Host "SMOKE STAGE 13: PASS" -ForegroundColor Green
