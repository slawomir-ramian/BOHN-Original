$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

if (-not (Test-Path ".\docs\source\BOHN_EN_SOURCE.tex")) {
    throw "Uruchom skrypt w katalogu głównym E:\BOHN\BOHN-Original."
}

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    py -3 -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install -r requirements-stage10.txt
if ($LASTEXITCODE -ne 0) { throw "Instalacja zależności Etapu 10 nie powiodła się." }

& .\.venv\Scripts\python.exe tools\extract_stage_10.py
if ($LASTEXITCODE -ne 0) { throw "Ekstrakcja Etapu 10 nie powiodła się." }

& .\.venv\Scripts\python.exe tools\render_source_chronology.py
if ($LASTEXITCODE -ne 0) { throw "Kontrola chronologii nie powiodła się." }

Write-Host "SETUP STAGE 10: PASS" -ForegroundColor Green
