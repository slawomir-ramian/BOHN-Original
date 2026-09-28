$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONIOENCODING = "utf-8"
& .\.venv\Scripts\python.exe -m unittest -v tests.test_stage_13
if ($LASTEXITCODE -ne 0) { throw "Testy Etapu 13 nie powiodly sie." }
Write-Host "Etap 13: piec pozycji SYS jest audytem; jeden wspolny program wykonuje piec eksperymentow CPU."
& .\.venv\Scripts\python.exe tools\run_stage_13.py
if ($LASTEXITCODE -ne 0) { throw "Pelne wykonanie Etapu 13 nie powiodlo sie." }
Write-Host "FULL STAGE 13: PASS" -ForegroundColor Green
