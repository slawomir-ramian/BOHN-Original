# Polityka chronologii źródłowej

## Zasada nadrzędna

Repozytorium BOHN-Original zachowuje kolejność rozwoju przedstawioną w PDF-ie.
Identyfikator jednostki jest stabilnym adresem, lecz nie służy do ustalania jej
położenia historycznego.

Podstawowym rejestrem jest `inventory/source_chronology.csv`. Jego kolumna
`source_order` odpowiada kolejności w audytowanym indeksie PDF/LaTeX.

## Dlaczego S-010 i S-011 występują przed S-007

`S-010` i `S-011` zostały wydzielone jako osobne jednostki dopiero podczas
audytu źródła. W monografii znajdują się w sekcji 3.4.3, przed sekcjami 3.5 i
3.6 zawierającymi `S-007`--`S-009`. Dlatego poprawna kolejność brzmi:

```text
S-001 -> S-002 -> S-003 -> S-004 -> S-005 -> S-006
      -> S-010 -> S-011 -> S-007 -> S-008 -> S-009
```

Nie wolno przestawiać tej sekwencji tylko po to, aby numery ID rosły.

## Kolejność wykonawcza

Jeśli przyszły kod będzie wymagał innej kolejności zależności technicznych,
zostanie ona zapisana osobno jako `execution_order`. Nie zastąpi ona
`source_order` i nie zmieni narracji historycznej.
