# Etap 15 — RMIG-FBOHN i Meta-FBOHN

## Zakres

Etap zamyka chronologię monografii pozycjami 109–115:

1. `RF-001` — RMIG-FBOHN v1,
2. `RF-002` — test poza przestrzenią reprezentacji,
3. `MF-001` — globalne skalowanie cech,
4. `MF-002` — skalowanie orbitowe,
5. `MF-003` — Learned Orbit Mixing,
6. `MF-004` — Symbolic Orbit Composer,
7. `MF-005` — Symbolic Library Discovery.

Wszystkie jednostki współdzielą kompletny listing 71. Źródło historyczne jest
kopiowane bajtowo i kontrolowane SHA-256. Wrapper wykonawczy importuje jego
funkcje i dodaje checkpoint po każdej komórce `seed × noise`; nie zmienia kodu
algorytmicznego ani parametrów publikacji.

## Pełny kontrakt

- 6000 próbek,
- 10 seedów,
- poziomy szumu: 0.0, 0.1, 0.3 i 0.5,
- populacja 80, 30 generacji, 8 elit,
- 12 cech mieszanych w v3,
- 16 cech symbolicznych w v4/v5,
- dla v5: 12 odkryć biblioteki i rozmiar biblioteki 32.

## Interpretacja

`MF-001` i `MF-002` są ważnymi wynikami negatywnymi: dodatnie przeskalowanie
cech nie zmienia modelu po standaryzacji. Wersje v3–v5 testują silniejsze,
niebanalne operacje: mieszanie orbit, kompozycję symboliczną i agregację
stabilnych symboli do biblioteki. Wyniki lokalne będą porównywane osobno z
wartościami źródłowymi, bez nadpisywania raportu z monografii.
