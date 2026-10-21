# cellwalk

Reconstruct irregular spreadsheet tables by associating data cells with explicit
spatial headers. Retain physical coordinates and merged-cell anchor provenance
for data values and every associated header.

```python
import pandas as pd
from cellwalk import CellGrid

raw = pd.DataFrame([[None, 2024, None], [None, "Q1", "Q2"], ["Mexico", 10, 20]], dtype=object)
base = CellGrid.from_dataframe(raw).data(rows=[2], columns=[1, 2])
headers = base.headers_above("year", row=0, span="right").headers_above("quarter", row=1)
result = headers.headers_left("country", column=0).to_frame()
print(result[["country", "year", "quarter", "value"]])
```

## Install

Python 3.11+ and Pandas 2.2+ are required. Install from a checkout until the
initial PyPI release has been verified:

```bash
python -m pip install .
# After the first verified PyPI release:
python -m pip install cellwalk
# Optional XLSX reader:
python -m pip install "cellwalk[xlsx]"
```

There is no dependency on R or sibling projects, runtime service, or telemetry.

## Coordinates, bounds and navigation

All coordinates are **zero-based positions**. DataFrame index and column labels
are ignored as geometry, so duplicate labels are supported. `Cell` exposes
`row`, `column`, `value`, `source_row`, and `source_column`. For a DataFrame cell,
the source anchor equals its physical coordinate. Grid operations return new
grids and do not modify inputs or previous selections.

| API | Behavior |
|---|---|
| `CellGrid.from_dataframe(frame)` | Snapshot cell scalars without whole-array coercion |
| `grid.cell(row, column)` | Fetch a cell inside current bounds |
| `grid.within(row_start, row_stop, column_start, column_stop)` | Restrict navigation to a half-open subrectangle |
| `grid.above/below/left/right(row, column, skip_blank=True)` | Find nearest cell in that direction; return `None` at the boundary |
| `grid.data(rows=[...], columns=[...], include_blank=False)` | Select explicit Cartesian-product target positions |
| `grid.headers_above(name, row=..., span="none", missing="raise")` | Attach a fixed header row |
| `grid.headers_left(name, column=..., span="none", missing="raise")` | Attach a fixed header column |
| `grid.associate(name, mapping, missing="raise")` | Map selected data coordinates to arbitrary header coordinates |
| `grid.to_frame()` | Materialize records with all value and coordinate provenance |

Bounds use excluded stops, like Python slicing, and can only narrow an existing
region. Navigation and spans cannot cross them. `within()` clears targets and
associations; call it before `data()`. Data selection follows the supplied row
order, then column order, and clears old associations when repeated. Use
separate grids for adjacent tables. Empty selections return an empty output
with the expected schema.

Structural blanks are scalar missing values or empty/whitespace-only strings.
Zero and False are values. Blank data cells are omitted by default;
`include_blank=True` preserves them. `skip_blank=False` navigation returns the
immediate physical neighbor, even if blank.

## Explicit header rules

`headers_above` requires the specified row to be above every target. By default,
the header comes from the exact target column. `span="right"` explicitly fills a
blank heading from the nearest nonblank header at its left on that same row,
stopping at the region boundary. This supports year spans above quarterly
headings without guessing header levels. Add another named association for each
level.

`headers_left` similarly requires a column left of every target. Its opt-in
`span="down"` carries a nonblank heading from above within that column. Default
`span="none"` never infers a span. Missing/blank headers raise `GridError`;
`missing="none"` retains targets with an unassigned header and null header
coordinates.

For nonrectangular layouts, use an explicit mapping:

```python
selected = CellGrid.from_dataframe(raw).data(rows=[2], columns=[1, 2])
mapped = selected.associate("year", {(2, 1): (0, 1), (2, 2): (0, 1)})
```

Mappings may choose headers in any direction but must refer to selected data
cells and headers inside bounds. No result values are hardcoded; the mapping
specifies source relationships. See [examples/nonrectangular.py](examples/nonrectangular.py).

## Output and provenance

`to_frame()` always includes `row`, `column`, `source_row`, `source_column`, and
`value`. Each header named `year`, for example, adds `year`, `year_row`,
`year_column`, `year_source_row`, and `year_source_column`. The first coordinates
identify the associated physical cell; source coordinates identify its value's
anchor. Header names colliding with these metadata fields or another generated
field raise an error. Object-backed columns avoid rounding large integers or
coercing original mixed scalars when another record is missing. Cast to desired
analysis dtypes explicitly after reconstruction.

## Optional XLSX reading and merged cells

```python
grid = CellGrid.from_xlsx("report.xlsx", sheet="Data", merged="propagate")
```

`sheet` is a worksheet name or zero-based index. `merged="blank"`, the default,
keeps nonanchor merged children empty. `merged="propagate"` supplies the anchor
value to every child. Both retain each physical coordinate and the original
anchor's source coordinates. A subsequently selected propagated header therefore
retains its child location and anchor location separately.

The adapter uses openpyxl with `data_only=True`, `keep_vba=False`, and
`keep_links=False`. It reads cached formula values; it never evaluates formulas,
executes macros or follows workbook links. A formula without a saved cached
value appears as missing. Existing Excel numeric precision limits still apply;
the library cannot recover precision already lost in the workbook. Workbooks
are closed after reading, and source files are never saved or modified.

## Use cases, alternatives and limitations

Use cellwalk for layered period/country reports, grouped row headings, sparse
header geometry, adjacent tables with explicit regions, and merged headings
whose anchor provenance matters. [unpivotr](https://github.com/nacnudus/unpivotr)
inspired its spatial approach. Pandas melt/MultiIndex, Polars unpivot and
openpyxl already solve reshaping and cell access. cellwalk combines them into
explicit header association and provenance; see [RESEARCH.md](RESEARCH.md).

Version 0.1.0 does not infer table boundaries, recognize formatting/OCR/HTML,
guess header meaning, or provide a Polars backend. It stores the whole grid in
memory, including the worksheet's used dimensions, so heavily formatted large
workbooks may require preprocessing. Header spans continue within the selected
region until another nonblank header; choose bounds or explicit mappings when
blank gaps have a different meaning. Mutable objects inside DataFrame cells
remain caller-owned; avoid modifying them after creating a grid.

## Validation and benchmark

```bash
python -m pip install -e ".[dev]"
python -m pytest --cov=cellwalk --cov-report=term-missing
python -m ruff check .
python -m mypy src
python examples/quickstart.py
python examples/nonrectangular.py
python benchmarks/benchmark.py --rows 2000 --repeat 5
```

Tests cover all directions, boundaries, multi-level and nonrectangular headers,
missing cells, duplicate labels, exact large integer round trips, generated
dimensions, and temporary XLSX merged/formula fixtures. The benchmark compares
equivalent values and data coordinates with a manual Pandas coordinate recipe,
then times repeated runs and separately measures traced Python memory.
[Raw results](benchmarks/results.json) and [methodology](benchmarks/README.md)
include environment, spread and the cost of additional provenance. No speed
advantage is claimed.

See [CONTRIBUTING.md](CONTRIBUTING.md). Original code is MIT licensed; upstream
inspiration does not imply affiliation. Proposed 0.2.0 work: selection by
explicit cell predicates, indexed navigation for large sparse grids and a
streaming XLSX region reader.
