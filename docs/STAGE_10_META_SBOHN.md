# Etap 10 — Meta-SBOHN

## Zakres

Etap obejmuje pozycje 73--82 audytowanej chronologii PDF-a, czyli cały
rozdział 8: `MS-001`--`MS-010`.

## Granica materiału źródłowego

| Jednostki | Dostępny materiał | Tryb |
|---|---|---|
| `MS-001`--`MS-004` | opis i tabele wyników | `AUDITED_REPORTED_RESULT` |
| `MS-005`--`MS-008` | opis, wyniki i fragment inicjalizacji populacji | `AUDITED_REPORTED_RESULT` |
| `MS-009`, `MS-010` | pełny wspólny program v5/v6 | wykonanie historyczne |

Fragment listingu curriculum nie zawiera generatora danych, ewolucji,
protokołu wieloseedowego ani kodu raportowania. Dlatego nie jest przedstawiany
jako kompletny program historyczny.

## Protokół pełnego wykonania

Program v5/v6 zachowuje parametry źródłowe:

- 20 seedów;
- zadania `easy`, `medium`, `hard`;
- tryby `accuracy_only`, `fixed_geometry`, `annealed_geometry`;
- populacja 60, 25 generacji i 6 elit.

Daje to 180 niezależnych komórek oraz 270 000 ocen permutacji. Wykonawca nie
zmienia funkcji historycznych; wywołuje `run_one` dla każdej komórki osobno,
co umożliwia checkpoint i równoległość bez mieszania stanu losowego.

## Kryteria porównania

`MS-009` sprawdza, czy stała regularyzacja zachowuje korzyść na trudnym
zadaniu bez materialnej straty na zadaniu średnim. `MS-010` sprawdza, czy
annealing zwiększa zgodność z prawdziwą geometrią na wszystkich trzech
zadaniach oraz zwiększa częstość wejścia do geometrycznych basinów dla zadań
średniego i trudnego.

Różnica numeryczna nie jest błędem programu. Raport osobno zapisuje wykonanie
techniczne, zgodność liczb i zachowanie wniosku naukowego.
