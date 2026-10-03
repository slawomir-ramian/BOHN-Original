$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONIOENCODING = "utf-8"

& .\.venv\Scripts\python.exe tools\verify_stage_16_protocol.py
if ($LASTEXITCODE -ne 0) { throw "Stage 16 protocol verification failed." }

& .\.venv\Scripts\python.exe -m unittest -v tests.test_stage_16
if ($LASTEXITCODE -ne 0) { throw "Stage 16 tests failed." }

& .\.venv\Scripts\python.exe tools\run_stage_16.py --smoke --threads 4
if ($LASTEXITCODE -ne 0) { throw "Stage 16 smoke execution failed." }

Write-Host "SMOKE STAGE 16: PASS" -ForegroundColor Green

