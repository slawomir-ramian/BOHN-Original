# Closeout Etapu 15

Pakiet closeoutu zapisuje pełny bieg `20260928T185044Z`, aktualizuje statusy
ostatnich siedmiu jednostek i potwierdza ukończenie **115/115** pozycji.

```powershell
cd E:\BOHN\BOHN-Original
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\APPLY_STAGE_15_CLOSEOUT.ps1
git status
```

Walidator zachowuje `MF-005` jako `NUMERIC_DIFFERENCE`: średnie i główny
mechanizm zostały potwierdzone, ale zamiast deklarowanych 40/40 zwycięstw nad
FBOHN uzyskano 39/40. Jedyna przegrana wynosi 0,0556 pp.

Po wyniku `STAGE 15 CLOSEOUT: PASS` wykonaj commit poleceniami podanymi w
rozmowie. Nie dodawaj katalogu `reproduced/stage_15_checkpoint/`.
