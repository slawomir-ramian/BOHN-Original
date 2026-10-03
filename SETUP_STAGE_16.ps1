$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONIOENCODING = "utf-8"

if (-not (Test-Path .\.venv\Scripts\python.exe)) {
    py -3 -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install -r requirements-stage16.txt
if ($LASTEXITCODE -ne 0) { throw "Stage 16 dependency installation failed." }

& .\.venv\Scripts\python.exe tools\register_stage_16_supplementary.py
if ($LASTEXITCODE -ne 0) { throw "Stage 16 registration failed." }

& .\.venv\Scripts\python.exe tools\verify_stage_16_protocol.py
if ($LASTEXITCODE -ne 0) { throw "Stage 16 protocol verification failed." }

& .\.venv\Scripts\python.exe -m unittest -v tests.test_stage_16
if ($LASTEXITCODE -ne 0) { throw "Stage 16 tests failed." }

Write-Host "SETUP STAGE 16: PASS" -ForegroundColor Green

