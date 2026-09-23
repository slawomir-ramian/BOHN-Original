$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\docs\source\BOHN_EN_SOURCE.tex")) {
    throw "Uruchom skrypt w katalogu głównym E:\BOHN\BOHN-Original."
}

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    py -3 -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install -r requirements-stage04.txt
& .\.venv\Scripts\python.exe tools\extract_sbohn_chronology.py
& .\.venv\Scripts\python.exe tools\render_source_chronology.py

Write-Host "SETUP STAGE 04: PASS" -ForegroundColor Green
