# Instalacja i uruchomienie Etapu 12

Uruchom PowerShell w katalogu `E:\BOHN\BOHN-Original`.

Jeżeli nowa sesja blokuje skrypty, ustaw wyjątek tylko dla bieżącego procesu:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
```

Następnie wykonaj:

```powershell
.\SETUP_STAGE_12.ps1
.\RUN_STAGE_12_SMOKE.ps1
.\RUN_STAGE_12_FULL.ps1
```

Smoke nie pobiera Fashion-MNIST i sprawdza architektury na losowych tensorach.
Pełny bieg `SOTA-001` może pobrać zbiór Fashion-MNIST przy pierwszym
uruchomieniu. Wyniki są zapisywane w `reproduced/stage_12_runs/`, a pełny bieg
tworzy również ZIP w `artifacts/`.

Checkpointy w `reproduced/stage_12_checkpoint/` pozwalają ponownie wygenerować
raport bez kosztownego powtarzania poprawnie zakończonego programu. Aby celowo
wykonać eksperyment od nowa, usuń wyłącznie odpowiedni plik `SOTA-001.json` lub
`SOTA-002.json` z tego katalogu.

Historyczne pliki w `experiments/10_sota_and_scaling/*/historical/` nie są
modyfikowane. Czerwony kolor terminala jest zarezerwowany dla rzeczywistych
błędów PowerShella.
