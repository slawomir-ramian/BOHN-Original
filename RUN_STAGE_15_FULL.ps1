$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONIOENCODING = "utf-8"
& .\.venv\Scripts\python.exe -m unittest -v tests.test_stage_15
if ($LASTEXITCODE -ne 0) { throw "Testy Etapu 15 nie powiodly sie." }
Write-Host "Etap 15 wykonuje pelny suite: 10 seedow, 4 poziomy szumu i checkpointy komorek. Meta-FBOHN v5 moze trwac wiele godzin."
& .\.venv\Scripts\python.exe tools\run_stage_15.py
if ($LASTEXITCODE -ne 0) { throw "Pelne wykonanie Etapu 15 nie powiodlo sie." }
Write-Host "FULL STAGE 15: PASS" -ForegroundColor Green
