$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONIOENCODING = "utf-8"

& .\.venv\Scripts\python.exe tools\finalize_stage_16_docs.py
if ($LASTEXITCODE -ne 0) { throw "Stage 16 documentation finalization failed." }

& .\.venv\Scripts\python.exe tools\verify_stage_16_protocol.py
if ($LASTEXITCODE -ne 0) { throw "Stage 16 protocol verification failed." }

& .\.venv\Scripts\python.exe -m unittest -v tests.test_stage_16
if ($LASTEXITCODE -ne 0) { throw "Stage 16 tests failed." }

& .\.venv\Scripts\python.exe tools\validate_stage_16_closeout.py
if ($LASTEXITCODE -ne 0) { throw "Stage 16 closeout validation failed." }

Write-Host "STAGE 16 CLOSEOUT: PASS" -ForegroundColor Green
Write-Host "No git add, commit, merge or push was executed."

