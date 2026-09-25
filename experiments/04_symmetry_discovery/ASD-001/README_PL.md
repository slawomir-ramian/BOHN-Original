# ASD-001

Pozycja Etapu 06: **5/5**; chronologia monografii: **33/115**.

Pełny kod historyczny: `historical/source_from_monograph.py`, listing 45
(wiersze 11224--11358), wyodrębniony bez zmian. Wynik: dokładna tabela 4.2 (wiersze 1939--1958); TXT jest transkrypcją.

Pełny tryb wykonuje `HISTORICAL_SOURCE`. Smoke jest osobną sondą techniczną.

Po lokalnym ujawnieniu niespójności między generatorem etykiet a tabelą 4.2
zaprojektowano oddzielny, jawny eksperyment `ASD-001R`. Znajduje się w
`reconstruction/` i nie zastępuje ani nie poprawia powyższego kodu
historycznego. Szczegóły: `docs/STAGE_06_ASD_001R_DESIGN.md`.
