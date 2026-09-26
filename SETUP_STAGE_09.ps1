$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

if (-not (Test-Path ".\docs\source\BOHN_EN_SOURCE.tex")) {
    throw "Uruchom skrypt w katalogu glownym E:\BOHN\BOHN-Original."
}

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    py -3 -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install -r requirements-stage09.txt
if ($LASTEXITCODE -ne 0) { throw "Instalacja zaleznosci Etapu 09 nie powiodla sie." }

& .\.venv\Scripts\python.exe tools\extract_stage_09.py
if ($LASTEXITCODE -ne 0) { throw "Ekstrakcja Etapu 09 nie powiodla sie." }

& .\.venv\Scripts\python.exe tools\render_source_chronology.py
if ($LASTEXITCODE -ne 0) { throw "Kontrola chronologii nie powiodla sie." }

Write-Host "SETUP STAGE 09: PASS" -ForegroundColor Green
