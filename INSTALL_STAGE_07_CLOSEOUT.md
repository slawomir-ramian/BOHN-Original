# Closeout Etapu 07 i 07R

Nakładka zapisuje wybrany pełny wynik Etapu 07, pełny wynik rekonstrukcji 07R,
dwie analizy metodologiczne oraz aktualizuje rejestry. Nie zmienia kodu
historycznego ani zamrożonego protokołu `STAGE_07R_V1`.

Po rozpakowaniu uruchom:

```powershell
.\APPLY_STAGE_07_CLOSEOUT.ps1
git status
```

Oczekiwany komunikat końcowy:

```text
STAGE 07/07R CLOSEOUT: PASS
```

Commit wykonaj dopiero po walidacji i sprawdzeniu `git status`.
