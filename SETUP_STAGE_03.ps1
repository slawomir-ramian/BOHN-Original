$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\docs\source\BOHN_EN_SOURCE.tex")) {
    throw "Uruchom skrypt w katalogu głównym E:\BOHN\BOHN-Original."
}

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    py -3 -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements-stage03.txt
& .\.venv\Scripts\python.exe tools\extract_bohn_foundation.py

Write-Host "SETUP STAGE 03: PASS" -ForegroundColor Green
