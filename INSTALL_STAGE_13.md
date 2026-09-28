# Instalacja i uruchomienie Etapu 13

W PowerShell, w katalogu `E:\BOHN\BOHN-Original`, wykonaj:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\SETUP_STAGE_13.ps1
.\RUN_STAGE_13_SMOKE.ps1
```

Po poprawnym smoke uruchom pełny bieg:

```powershell
.\RUN_STAGE_13_FULL.ps1
```

Pierwszy pełny bieg może pobrać MNIST, FashionMNIST, KMNIST i CIFAR-10.
Wspólny program CPU trenuje wiele modeli i może działać długo; komunikaty
`nadal dziala` są heartbeatami, a nie błędami. Limit bezpieczeństwa wynosi
12 godzin.

Wynik jest zapisywany w `reproduced/stage_13_runs/`, a ZIP w `artifacts/`.
Checkpoint `reproduced/stage_13_checkpoint/` pozwala ponownie wygenerować
raport bez powtarzania ukończonej baterii.

Czerwony kolor terminala jest zarezerwowany dla rzeczywistych błędów.
