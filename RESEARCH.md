# Research and scope decision

Reviewed 2026-10-21. This code is an original Python implementation, not a
translation or copy of unpivotr.

| Capability | R implementation | Python alternatives | Gap | Proposed solution |
|---|---|---|---|---|
| Spatial header association | [unpivotr](https://github.com/nacnudus/unpivotr) associates cells by geometry, including layered headers | Pandas indexing and manual coordinate tables; openpyxl cell access | The primitives exist; repeated association and provenance bookkeeping remains manual | Explicit data targets, fixed header rows/columns and arbitrary coordinate mappings |
| Multiple header layers | [unpivotr documentation](https://nacnudus.github.io/unpivotr/) describes behead/enhead workflows | Pandas MultiIndex, [melt](https://pandas.pydata.org/docs/reference/api/pandas.melt.html), [Polars unpivot](https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.unpivot.html) | Rectangular reshaping is already solved; raw cells may need association before reshaping | Compose independent year/quarter/country associations before to_frame |
| Header spans and regions | unpivotr proximity and table partitioning workflows | Explicit fill/selection in Pandas or openpyxl merged ranges | Guessing spans can leak context across adjacent tables | Opt-in right/down spans constrained to an explicit navigation rectangle |
| XLSX ingestion | R workflows can combine unpivotr with tidyxl | [openpyxl](https://openpyxl.readthedocs.io/en/stable/) already reads cells and merged ranges | File reading is solved; anchor provenance needs preservation during propagation | Optional openpyxl adapter retaining physical and anchor coordinates |
| Mixed values | unpivotr delays coercion | Object-backed Pandas columns and cell iteration | Whole-array coercion can change large integers when nulls occur | Read scalars positionally and construct object-backed output |

## Evidence and design

The API deliberately selects source coordinates rather than guessing numeric
data or automatically detecting table boundaries. The quarterly example
reconstructs a two-level spanned header into eight records; a separate example
uses nonrectangular explicit mappings inside a restricted region. Generated
tests construct arbitrary dimensions and values, then independently check every
output record and coordinate. XLSX tests create workbooks locally and verify
merged anchors, default blank children, opt-in propagation and cached-formula
behavior.

This is a focused subset of unpivotr's spatial ideas. It does not implement
format-based header inference, HTML extraction, formatting, comment semantics,
sentinel interpretation or automatic small-table partitioning. Pandas and
openpyxl can already implement every operation manually; the value is a
composable typed spatial API with source coordinates.

## Licensing

[unpivotr DESCRIPTION](https://github.com/nacnudus/unpivotr/blob/master/DESCRIPTION)
declares MIT + license file. openpyxl's official documentation identifies its
MIT/Expat license. Pandas uses BSD-3-Clause; Polars uses MIT. Only public behavior
and problem descriptions informed this design; no upstream source was reused.
cellwalk's original code uses MIT.

## Naming

On 2026-10-21, `https://pypi.org/pypi/cellwalk/json` returned HTTP 404. PEP 503
normalization leaves `cellwalk` unchanged. GitHub's public repository search
`cellwalk in:name` returned 14 substring matches and no exact `cellwalk` name.
They include CellWalkR, a single-cell biology R package, and CellWalker projects
for microscopy, Go spreadsheet-cell traversal and VBA formatting. The project
description explicitly identifies irregular-table reconstruction and claims no
affiliation. This is a collision review, not a reservation or legal trademark
clearance. Recheck PyPI immediately before publication; a missing page does not
guarantee registration.
