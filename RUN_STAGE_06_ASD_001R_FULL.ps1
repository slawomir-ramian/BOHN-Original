$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Najpierw uruchom .\SETUP_STAGE_06.ps1"
}

& .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_stage_06_asd_001r.py" -v
if ($LASTEXITCODE -ne 0) { throw "Testy ASD-001R nie powiodly sie." }

& .\.venv\Scripts\python.exe tools\run_asd_001r_full.py --workers 2
if ($LASTEXITCODE -ne 0) { throw "Wykonanie ASD-001R FULL nie powiodlo sie." }

Write-Host "STAGE 06 ASD-001R FULL EXECUTION: PASS" -ForegroundColor Green
