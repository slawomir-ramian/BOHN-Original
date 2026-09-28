# Etap 13 — analiza lokalnego wykonania

## Wynik ogólny

Pełny bieg `20260928T051822Z` zakończył wspólny historyczny listing 64 kodem 0
w czasie 454,35 s. Pięć pozycji `SYS-001`--`SYS-005` pozostaje audytem
opublikowanych tabel: listingi 62--63 zawierają klasy, ale nie publikują pętli
eksperymentalnych. Pięć pozycji `CPU-001`--`CPU-005` wykonano faktycznie.

Wnioski centralne zachowano dla **3 z 5** eksperymentów CPU. `CPU-001` i
`CPU-003` pozostają jawnie oznaczone jako `NUMERIC_DIFFERENCE`. Cały Etap 13 ma
zatem ocenę **PARTIAL_REPRODUCTION**, mimo że techniczne wykonanie wszystkich
jednostek zakończyło się `PASS`.

Po zamknięciu etapu wykonano **99 ze 115** jednostek źródłowego PDF-a;
**16** pozostaje `NOT_RUN`.

## CPU-001 — Shallow vs Deep Encoder

| Domena | Shallow publ. | Shallow lokalnie | Deep publ. | Deep lokalnie | Lokalny zwycięzca |
|---|---:|---:|---:|---:|---|
| MNIST | 92,6% | 92,3% | 93,6% | 93,2% | Deep |
| Fashion | 79,1% | 82,3% | 82,4% | 80,7% | Shallow |
| CIFAR-10 | 31,9% | 32,7% | 34,0% | 33,4% | Deep |

Największa różnica od tabeli to 3,2 pp. Przewaga głębokiego enkodera została
odtworzona na MNIST i CIFAR-10, lecz nie na Fashion-MNIST. Teza o przewadze we
wszystkich trzech domenach nie została potwierdzona.

## CPU-002 — MoE Multi-Domain Routing

Dokładności są bliskie publikacji: MNIST 92,1%, Fashion 81,0%, a Mixed 86,5%
(wartość Mixed jest dokładna). W obu domenach router skierował jednak 100%
próbek do eksperta E1, podczas gdy tabela raportuje rozkład na czterech
ekspertów. Maksymalna różnica surowego udziału routingu wynosi 83,4 pp.

Główny negatywny wniosek **„specjalizacja: NIE”** pozostaje zachowany, ale
lokalny mechanizm jest silniejszym przypadkiem expert collapse niż rozkład
opublikowany. Dlatego `CONCLUSION_MATCH` nie oznacza zgodności geometrii
routingu.

## CPU-003 — Cross-Domain Meta-Generator

| Domena | Delta publikacji | Delta lokalna | Ocena |
|---|---:|---:|---|
| MNIST (widziana) | +79,0 pp | +0,6 pp | niepotwierdzona |
| Fashion (widziana) | +32,5 pp | +37,4 pp | potwierdzona |
| KMNIST (niewidziana) | +3,1 pp | -2,3 pp | zgodna jakościowo: brak przewagi |
| CIFAR-10 (niewidziana) | +0,7 pp | -1,2 pp | zgodna jakościowo: brak przewagi |

Eksperyment odtwarza dużą przewagę na Fashion oraz brak transferu na domeny
niewidziane, ale nie odtwarza kluczowej przewagi na widzianym MNIST. Całościowa
teza dwóch skutecznych domen widzianych nie została potwierdzona.

## CPU-004 — Partial Unfreeze

Zachowano centralny kompromis: silniejsze odmrażanie poprawia nowe zadanie
Fashion, ale obniża retencję starego zadania MNIST. Dla 1000 przykładów
`Frozen` daje 40,1% Fashion i 93,6% MNIST, a `+Last2` daje odpowiednio 66,6%
i 48,8%. Surowe wartości różnią się od tabeli nawet o 55,4 pp, dlatego wynik
jest zgodnością wniosku, a nie bliską reprodukcją liczbową.

## CPU-005 — Few-Shot Scaling

Zachowano niski pułap jakości: wszystkie wyniki pozostają poniżej 50%, a wynik
dla 5000 przykładów (35,8%) jest wyższy niż dla 10 przykładów (18,1%). Krzywa
pozostaje niemonotoniczna. Maksymalna różnica względem tabeli wynosi 17,2 pp.

## Granice źródłowe i integralność

Historyczny listing 64 pozostał niezmieniony. Kopia wykonawcza otrzymała tylko
dwie jawne poprawki zgodności: przekierowanie `/tmp/data` do lokalnego cache i
uzupełnienie brakującego w publikacji `import gc`. Manifest SHA-256 pełnego
biegu został zweryfikowany. Pierwsze nieudane uruchomienie było wyłącznie
przerwanym pobraniem CIFAR-10; udany bieg użył archiwum o poprawnym MD5.

## Wniosek merytoryczny

Etap 13 nie obala ogólnej idei BOHN/SBOHN, ale ogranicza dwie szczegółowe tezy
tego rozdziału: uniwersalną przewagę głębokiego enkodera oraz niezawodną
przewagę meta-generatora na każdej domenie widzianej. Jednocześnie odtwarza
brak specjalizacji routera, kompromis adaptacja--zapominanie i niski,
niemonotoniczny pułap few-shot. Repozytorium powinno prezentować ten etap jako
częściową reprodukcję, a nie pełne potwierdzenie wszystkich tabel.
