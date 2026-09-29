# Przygotowanie BOHN-Original do publikacji na GitHubie

Ten pakiet nie tworzy zdalnego repozytorium i niczego nie wysyła do Internetu.
Dodaje rozdzielone licencje, cytowanie, angielski opis i lokalny audyt
bezpieczeństwa. Uwzględnia następującą decyzję autora:

- preprint opublikowany w Zenodo pozostaje na CC BY 4.0;
- nowy kod repozytorium: PolyForm Noncommercial 1.0.0;
- nowa dokumentacja i wyniki: CC BY-NC 4.0;
- wykorzystanie komercyjne nowego kodu wymaga osobnej pisemnej zgody.

## Instalacja paczki

Umieść pobrany ZIP w `E:\BOHN\BOHN-Original`, a następnie wykonaj:

```powershell
cd E:\BOHN\BOHN-Original

Expand-Archive `
  -Path .\BOHN-Original-GitHub-Prep-01.zip `
  -DestinationPath . `
  -Force

Remove-Item .\BOHN-Original-GitHub-Prep-01.zip
```

## Audyt

```powershell
cd E:\BOHN\BOHN-Original
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\PREPARE_GITHUB_PUBLICATION.ps1
git status
```

Po wykonaniu wklej:

1. końcowe podsumowanie skryptu,
2. zawartość `docs/GITHUB_PUBLICATION_AUDIT.md`,
3. wynik `git status`.

Nie wykonuj jeszcze `git add`, `git commit`, `git remote add` ani `git push`.
