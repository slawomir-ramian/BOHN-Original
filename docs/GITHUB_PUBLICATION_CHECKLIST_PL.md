# Lista kontrolna publikacji BOHN-Original na GitHubie

## Etap A — audyt lokalny

- [ ] `git status` jest znany i nie zawiera przypadkowych plików.
- [ ] Nie wykryto tokenów, haseł, kluczy prywatnych ani danych uwierzytelniających.
- [ ] Autor zaakceptował adresy e-mail zapisane w historii commitów.
- [ ] Żaden plik nie przekracza 100 MiB.
- [ ] Historyczne ścieżki absolutne są opisane jako materiał źródłowy lub warstwa zgodności.
- [ ] `LICENSE`, `LICENSE-DOCUMENTATION.md`, `COMMERCIAL-LICENSE.md` i
      `CITATION.cff` są obecne.
- [ ] Testy closeoutu Etapu 15 nadal przechodzą.

## Etap B — utworzenie repozytorium

- [ ] Konto GitHub jest dostępne i zabezpieczone uwierzytelnianiem dwuskładnikowym.
- [ ] Utworzono puste prywatne repozytorium `BOHN-Original`.
- [ ] Przy tworzeniu nie dodano zdalnego README, `.gitignore` ani licencji.
- [ ] Lokalny katalog podłączono jako `origin`.
- [ ] Pierwszy `push` gałęzi `main` zakończył się bez błędów.

## Etap C — kontrola po publikacji

- [ ] Strona główna pokazuje polski README oraz odnośnik do wersji angielskiej.
- [ ] Pliki licencyjne oraz `CITATION.cff` są widoczne i poprawne.
- [ ] PDF i wybrane wyniki można pobrać.
- [ ] Nie opublikowano cache, środowiska `.venv`, ZIP-ów instalacyjnych ani danych uwierzytelniających.
- [ ] Włączono prywatne zgłaszanie podatności w zakładce Security.
- [ ] Po końcowej kontroli widoczność zmieniono na publiczną.
- [ ] Utworzono oznaczone wydanie `v1.0.0` dopiero po kontroli publicznego
      widoku repozytorium.

## Zasada

Nie wykonujemy `push --force`, nie przepisujemy zakończonej historii i nie
zmieniamy widoczności na publiczną, dopóki raport audytu nie zostanie wspólnie
oceniony.
