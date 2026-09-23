$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\docs\source\BOHN_EN_SOURCE.tex")) {
    throw "Uruchom skrypt w katalogu głównym E:\BOHN\BOHN-Original."
}

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    py -3 -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install -r requirements-stage05.txt
if ($LASTEXITCODE -ne 0) { throw "Instalacja zależności Etapu 05 nie powiodła się." }

& .\.venv\Scripts\python.exe tools\extract_stage_05.py
if ($LASTEXITCODE -ne 0) { throw "Ekstrakcja Etapu 05 nie powiodła się." }

& .\.venv\Scripts\python.exe tools\render_source_chronology.py
if ($LASTEXITCODE -ne 0) { throw "Kontrola chronologii nie powiodła się." }

Write-Host "SETUP STAGE 05: PASS" -ForegroundColor Green
