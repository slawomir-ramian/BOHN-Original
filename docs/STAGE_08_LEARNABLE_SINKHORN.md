# Etap 08 — Learnable SBOHN i Log-Domain Sinkhorn

## Zakres

Etap zachowuje pozycje 46–56 oryginalnej chronologii PDF-a:

`LS-001`, `LS-002`, `LS-003`, `LS-004`, `LS-005`, `LS-006`, `LD-001`, `LD-002`, `LD-003`, `LD-004`, `LD-005`.

## Granica opublikowanego kodu

Audyt LaTeX wykazał ważną różnicę pomiędzy przypisaniem listingu a jego rzeczywistą zawartością:

- listing 53 zawiera kompletny pięciokrokowy pipeline `LS-001`;
- ten sam listing jest przypisany w inwentarzu również do `LS-002`–`LS-006`, ale nie zawiera kodu wykonującego opisane tam eksperymenty zaawansowane;
- listing 54 zawiera kod testów A–C, czyli `LD-001`–`LD-003`;
- listing 55 zawiera kod testów D–E, czyli `LD-004`–`LD-005`.

Dlatego `LS-002`–`LS-006` pozostają oryginalnymi pozycjami źródłowymi, ale są wykonywane w trybie `AUDITED_REPORTED_RESULT`. Nie przedstawiamy wspólnego listingu 53 jako kodu, który odtwarza ich tabele.

## Zasady reprodukcji

1. Historyczne listingi są zachowane bez zmian i kontrolowane skrótami SHA-256.
2. Ścieżki `/tmp/...` zapisane w kodzie publikacyjnym są przekierowywane przez zewnętrzny wrapper do katalogu wynikowego. Listing nie jest modyfikowany.
3. Wspólne programy dla `LD-001`–`LD-003` oraz `LD-004`–`LD-005` są uruchamiane tylko raz, a każda pozycja otrzymuje osobną klasyfikację wyniku.
4. Różnica numeryczna nie jest błędem technicznym. Raport oddziela status wykonania od zgodności wniosku naukowego.
5. Pełny przebieg automatycznie tworzy ZIP wynikowy w katalogu `artifacts`.
