$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONIOENCODING = "utf-8"

& .\.venv\Scripts\python.exe -m unittest -v tests.test_stage_12
if ($LASTEXITCODE -ne 0) { throw "Testy Etapu 12 nie powiodly sie." }

Write-Host "Etap 12 uruchamia dwa pelne historyczne listingi. SOTA-001 moze pobrac Fashion-MNIST." 
& .\.venv\Scripts\python.exe tools\run_stage_12.py
if ($LASTEXITCODE -ne 0) { throw "Pelne wykonanie Etapu 12 nie powiodlo sie." }

Write-Host "FULL STAGE 12: PASS" -ForegroundColor Green
