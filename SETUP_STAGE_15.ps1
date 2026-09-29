$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONIOENCODING = "utf-8"
if (-not (Test-Path ".\.venv\Scripts\python.exe")) { py -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install -r requirements-stage15.txt
if ($LASTEXITCODE -ne 0) { throw "Instalacja zaleznosci Etapu 15 nie powiodla sie." }
& .\.venv\Scripts\python.exe tools\extract_stage_15.py
if ($LASTEXITCODE -ne 0) { throw "Ekstrakcja Etapu 15 nie powiodla sie." }
& .\.venv\Scripts\python.exe tools\render_source_chronology.py --check
if ($LASTEXITCODE -ne 0) { throw "Kontrola chronologii nie powiodla sie." }
Write-Host "SETUP STAGE 15: PASS" -ForegroundColor Green
