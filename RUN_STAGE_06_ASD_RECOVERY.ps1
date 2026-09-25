$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    throw "Najpierw uruchom .\SETUP_STAGE_06.ps1"
}

& .\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_stage_06.py" -v
if ($LASTEXITCODE -ne 0) { throw "Testy Etapu 06 nie powiodły się." }

& .\.venv\Scripts\python.exe tools\run_asd_001_recovery.py --workers 2
if ($LASTEXITCODE -ne 0) { throw "Odzyskiwanie ASD-001 nie powiodło się." }

Write-Host "STAGE 06 ASD RECOVERY: PASS" -ForegroundColor Green
