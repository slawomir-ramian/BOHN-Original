$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONIOENCODING = "utf-8"
if (-not (Test-Path ".\.venv\Scripts\python.exe")) { py -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install -r requirements-stage14.txt
if ($LASTEXITCODE -ne 0) { throw "Instalacja zaleznosci Etapu 14 nie powiodla sie." }
& .\.venv\Scripts\python.exe -c "import torch, torchvision; print('TORCH:', torch.__version__, '| TORCHVISION:', torchvision.__version__)"
if ($LASTEXITCODE -ne 0) { throw "Import PyTorch lub torchvision nie powiodl sie." }
& .\.venv\Scripts\python.exe tools\extract_stage_14.py
if ($LASTEXITCODE -ne 0) { throw "Ekstrakcja Etapu 14 nie powiodla sie." }
& .\.venv\Scripts\python.exe tools\render_source_chronology.py --check
if ($LASTEXITCODE -ne 0) { throw "Kontrola chronologii nie powiodla sie." }
Write-Host "SETUP STAGE 14: PASS" -ForegroundColor Green
