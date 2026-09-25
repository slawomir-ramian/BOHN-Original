$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Najpierw uruchom .\SETUP_STAGE_06.ps1"
}

& .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_stage_06*.py" -v
if ($LASTEXITCODE -ne 0) { throw "Testy closeoutu ASD-001R nie powiodly sie." }

& .\.venv\Scripts\python.exe tools\validate_asd_001r_closeout.py
if ($LASTEXITCODE -ne 0) { throw "Walidacja closeoutu ASD-001R nie powiodla sie." }

Write-Host "STAGE 06 ASD-001R CLOSEOUT: PASS" -ForegroundColor Green
