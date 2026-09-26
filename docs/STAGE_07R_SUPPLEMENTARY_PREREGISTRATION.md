# Etap 07R — zamrożony protokół rekonstrukcji uzupełniających

## Status epistemiczny

Etap 07R obejmuje pięć równoległych eksperymentów uzupełniających do jednostek
rozdziału 5, dla których monografia podała opis i wyniki, lecz nie pełny kod.
Eksperymenty mają sufiks `R`, pozostają poza chronologią 115 jednostek PDF-a
i nie zastępują źródłowych rekordów `NARRATIVE_ONLY`.

Znajomość opublikowanych tabel oznacza, że nie jest to niezależna replikacja
ślepa. Przed pełnym przebiegiem zamrożono jednak jeden wspólny protokół,
parametry i kryteria strukturalne. Nie wolno dostrajać kodu po zobaczeniu
pełnych wyników potwierdzających.

## Wspólny kontrakt danych

Rekonstrukcje permutacyjne i kompresyjne używają `load_digits`, normalizacji
do `[0,1]` oraz etykiety zależnej od asymetrii względem odbicia poziomego i
obrotu o 180 stopni, zgodnie z pełnymi kodami `AR-001`--`AR-004`.

W rekonstrukcjach kompresji przyjmujemy jawny, minimalny kontrakt reprezentacji:
dwa bloki asymetrii prawdziwych transformacji, łącznie 128 cech. Nie twierdzimy,
że jest to nieopublikowana implementacja „pełnego SBOHN-AR”. Kontrakt izoluje
pytanie o kompresję od pytania o autonomiczne odkrycie transformacji.

## Pięć eksperymentów

### PL-002R

Ewolucja pary permutacji z populacją 40, 25 generacjami i 8 elitami. Kryterium
podstawowe: najlepsza para końcowa przewyższa baseline oraz nie jest gorsza od
najlepszej pary w populacji początkowej. Wyniki true-flip, true-rot180 i true-pair
są kontrolami, nie danymi wejściowymi ewolucji.

### PL-003R

Jedna zagnieżdżona biblioteka 99 losowych permutacji; oceniane prefiksy
`K = 1,2,5,10,20,50,99`. Kryterium: `K=99` przewyższa `K=1` i baseline,
a nachylenie dokładności względem `log(K)` jest dodatnie.

### HD-003R

Kod wysokowymiarowy z Etapu 07 zostaje uzupełniony o jawne skalowanie wag
sygnału przez `1/d`. Test: `d = 63,255,1023,4095`, `n=2000`, 10 seedów.
Kryterium: SBOHN wygrywa w każdym seedzie i każdym wymiarze, a średni gain
maleje wraz z wymiarem.

### CMP-001R

Porównanie PCA-48 z autoenkoderem rekonstrukcyjnym `128→96→48→96→128`.
Klasyfikator logistyczny jest dopasowywany do obu reprezentacji 48D. Kryterium:
dokładność PCA-48 jest wyższa niż dokładność AE-48.

### CMP-002R

Nadzorowana sieć `128→32→k→32→1`, `k=2,4,8,16`, porównana z PCA o tym samym
wymiarze na 10 seedach. Kryterium: średni SRL przewyższa średnie PCA dla każdego
`k`, a SRL-2 osiąga co najmniej 90% dokładności pełnej reprezentacji.

## Pilot i zamrożenie

Pilot używa oddzielnych seedów 101, 102 i 707 oraz zmniejszonych budżetów.
Potwierdził wykonalność wszystkich pięciu kontraktów bez ostrzeżeń o zbieżności.
Pełny przebieg jest chroniony plikiem `STAGE_07R_PROTOCOL_LOCK.json`, który
zawiera SHA-256 kodu obliczeniowego, runnera jednostki i konfiguracji.

## Dozwolone wnioski

Po spełnieniu kryteriów wolno stwierdzić, że główne tezy strukturalne pięciu
tabel zostały odtworzone w jawnych rekonstrukcjach uzupełniających. Nie wolno
stwierdzać odzyskania oryginalnego kodu ani `EXACT_MATCH` historycznego.
