# Instalacja Etapu 02

Pakiet instaluje audyt krzyżowy polskiego PDF-u i angielskiego źródła LaTeX.
Nie zmienia historii pierwszego commita i nie dodaje jeszcze kodu wykonawczego
eksperymentów.

W PowerShellu, w czystym repozytorium po Etapie 01:

```powershell
cd E:\BOHN\BOHN-Original

Expand-Archive .\BOHN_ORIGINAL_STAGE_02_LATEX_AUDIT_v1.zip -DestinationPath . -Force
Remove-Item .\BOHN_ORIGINAL_STAGE_02_LATEX_AUDIT_v1.zip

python .\tools\audit_latex_source.py
python .\tools\render_inventory.py
git status
```

Oczekiwane komunikaty:

```text
LATEX AUDIT PASS: chapters=17; tables=94; listings=74; verbatim=20; missing_assets=2
OK: 115 unique inventory rows; 94 tables; 24 code suites; 74 listings; 20 verbatim blocks
```

Po weryfikacji statusu zmiany należy zapisać w oddzielnym commicie Etapu 02.
