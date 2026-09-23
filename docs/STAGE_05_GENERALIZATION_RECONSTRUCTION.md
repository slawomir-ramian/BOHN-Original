# Etap 05 - adaptacyjny router i uogólnienie SO(2)

## Zakres i chronologia

Etap obejmuje pozycje 21--28 rejestru źródłowego:

```text
G-001 -> SO-001 -> SO-002 -> SO-003 -> SO-004 -> SO-005 -> SO-006 -> SO-007
```

Jest to ciągły fragment PDF-a po zakończonym rozdziale SBOHN. Następny blok
`SD-001`--`ASD-001` nie został przesunięty ani pominięty; stanowi zakres
Etapu 06.

## Poziomy materiału źródłowego

| ID | Materiał w monografii | Sposób wykonania |
|---|---|---|
| G-001 | pełny kod i pełny wydruk | bezpośrednie wykonanie kodu historycznego |
| SO-001 | pełny kod bez instrukcji drukowania oraz pełny wydruk | rekonstrukcja samego raportowania z zachowaniem obliczenia |
| SO-002 | wzór analityczny i pełny wydruk, bez listingu kodu | jawna rekonstrukcja numeryczna z opublikowanego wzoru |
| SO-003 | wzór z funkcją Beta i pełny wydruk, bez listingu kodu | jawna rekonstrukcja numeryczna i analityczna |
| SO-004 | definicja Fouriera i pełny wydruk, bez listingu kodu | jawna rekonstrukcja całkowania dyskretnego |
| SO-005--SO-007 | wspólny fragment ekstraktora cech i wyniki | jawna rekonstrukcja brakującego generatora i protokołu |

## Zasady

- zawartość `historical/` jest kopią materiału LaTeX i nie jest poprawiana,
- kod w `reconstruction/` nigdy nie jest nazywany kodem oryginalnym,
- raport rozróżnia zgodność liczbową, zgodność strukturalną i brak
  wystarczającego kodu do ścisłej reprodukcji,
- wszystkie surowe `stdout` i `stderr`, metadane środowiska oraz manifest
  SHA-256 są zapisywane w ZIP-ie pełnego przebiegu.

## Zamknięcie etapu

Pełny przebieg z 23 września 2026 r. zakończył się powodzeniem dla wszystkich
ośmiu jednostek. Szczegółowa interpretacja zgodności, różnic numerycznych i
granic materiału źródłowego znajduje się w
`docs/STAGE_05_LOCAL_ANALYSIS.md`.
