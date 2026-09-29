# BOHN-Original

Historical reconstruction and reproducibility archive of the BOHN/SBOHN
development described in Sławomir Ramian's 2026 monograph.

[Polska wersja README](README.md)

## Scope

The repository contains an audited inventory of **115 experimental units** in
their original PDF chronology. It separates:

- historical source printed in the monograph,
- explicit compatibility layers and reconstructions,
- reference results reported in the publication,
- locally reproduced results,
- tests, provenance records and SHA-256 manifests.

All 115 units have been processed. A completed unit is not automatically
treated as confirmation: exact matches, close numerical matches, conclusion
matches, audited-only results, partial reproductions and divergences remain
explicitly distinguished.

## Repository map

- `docs/` — policies, source audit and stage analyses,
- `docs/source/` — canonical PDF and auxiliary LaTeX source,
- `inventory/` — the canonical experiment and chronology registers,
- `experiments/` — historical sources, provenance and unit runners,
- `src/bohn_original/` — reusable local adapters and reconstructed modules,
- `tests/` — structural and reproduction-contract tests,
- `reproduced/` — selected complete local runs and their manifests,
- `tools/` — extraction, execution and validation utilities.

## Reproduction

The repository was reconstructed stage by stage on Windows using PowerShell
and Python virtual environments. Each stage provides setup, smoke and full-run
scripts. Start with the Polish instructions in the corresponding
`INSTALL_STAGE_*.md` file.

Some full protocols are computationally expensive. Stored reports and
manifests allow the completed reference runs to be audited without repeating
every long computation.

## Scientific status

The archive supports the central usefulness of relational and symmetry-aware
BOHN representations while retaining negative results and non-reproduced
stronger claims. See `docs/STAGE_*_LOCAL_ANALYSIS.md` for stage-specific
interpretations. The final RMIG/Meta-FBOHN stage is classified as
`NEAR_COMPLETE_REPRODUCTION`.

## Citation

GitHub-compatible citation metadata is provided in `CITATION.cff`. Related
archive DOI: https://doi.org/10.5281/zenodo.19897230

## License

Source code, tests and executable scripts are licensed under the PolyForm
Noncommercial License 1.0.0. Commercial use requires separate written
permission from the author.

The preprint previously published in Zenodo remains under CC BY 4.0. New
repository documentation, analyses and reproduced results are licensed under
CC BY-NC 4.0 unless a file states otherwise. See `LICENSE`,
`LICENSE-DOCUMENTATION.md` and `COMMERCIAL-LICENSE.md`.
