# Instalacja Etapu 05

Etap obejmuje kolejnych osiem jednostek w oryginalnej kolejności PDF-a:

```text
G-001, SO-001, SO-002, SO-003, SO-004, SO-005, SO-006, SO-007
```

`G-001` ma pełny wykonywalny listing. `SO-001` ma pełny, lecz niemy listing,
`SO-002`--`SO-004` mają opublikowane wzory i wyniki bez kodu, a
`SO-005`--`SO-007` współdzielą fragment funkcji cech bez kompletnego generatora
danych. Pakiet zachowuje te różnice i nie przedstawia rekonstrukcji jako kodu
historycznego.

## Instalacja

```powershell
cd E:\BOHN\BOHN-Original
Expand-Archive -Path .\BOHN-Original-Stage-05.zip -DestinationPath . -Force
Remove-Item .\BOHN-Original-Stage-05.zip
.\SETUP_STAGE_05.ps1
```

## Test szybki

```powershell
.\RUN_STAGE_05_SMOKE.ps1
```

Smoke wykonuje testy integralności oraz `G-001`, `SO-001` i `SO-007`. Nie tworzy
ZIP-a wynikowego.

## Pełny przebieg

```powershell
.\RUN_STAGE_05_FULL.ps1
```

Pełny przebieg wykonuje wszystkie osiem jednostek i automatycznie tworzy
kompletny ZIP w `artifacts\`. Nie wykonuj commita przed analizą ZIP-a i
zamknięciem etapu.
