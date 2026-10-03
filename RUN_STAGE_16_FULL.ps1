$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONIOENCODING = "utf-8"

& .\.venv\Scripts\python.exe tools\verify_stage_16_protocol.py
if ($LASTEXITCODE -ne 0) { throw "Stage 16 protocol verification failed." }

& .\.venv\Scripts\python.exe -m unittest -v tests.test_stage_16
if ($LASTEXITCODE -ne 0) { throw "Stage 16 tests failed." }

Write-Host "Stage 16 runs direct and hierarchical high-resolution benchmarks with checkpoints in reproduced/."
& .\.venv\Scripts\python.exe tools\run_stage_16.py --threads 4
if ($LASTEXITCODE -ne 0) { throw "Stage 16 full execution failed." }

Write-Host "FULL STAGE 16: PASS" -ForegroundColor Green

