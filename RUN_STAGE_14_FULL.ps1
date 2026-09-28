$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONIOENCODING = "utf-8"
& .\.venv\Scripts\python.exe -m unittest -v tests.test_stage_14
if ($LASTEXITCODE -ne 0) { throw "Testy Etapu 14 nie powiodly sie." }
Write-Host "Etap 14: szesc pozycji jest audytem; trzy pelne programy sa wykonywane z checkpointami."
& .\.venv\Scripts\python.exe tools\run_stage_14.py
if ($LASTEXITCODE -ne 0) { throw "Pelne wykonanie Etapu 14 nie powiodlo sie." }
Write-Host "FULL STAGE 14: PASS" -ForegroundColor Green
