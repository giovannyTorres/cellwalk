# cellwalk

**Reconstruct spreadsheet tables from where their headers actually live.**

A report has years spanning quarter columns, country labels at the left and separate tables on the same sheet. cellwalk associates selected cells with explicit headers and preserves physical and merged-anchor coordinates.

## Try it in two minutes

Requires Python 3.11+ with pandas 2.2+. Install the [published release](https://pypi.org/project/cellwalk/0.1.1/):

```sh
python -m pip install "cellwalk==0.1.1"
```

Copy this complete example into a Python session or save it as `demo.py` and run `python demo.py`:

```python
import pandas as pd

from cellwalk import CellGrid

raw = pd.DataFrame(
    [
        [None, 2024, None, 2025, None],
        [None, "Q1", "Q2", "Q1", "Q2"],
        ["Mexico", 10, 20, 30, 40],
        ["Chile", 15, 25, 35, 45],
    ],
    dtype=object,
)
result = (
    CellGrid.from_dataframe(raw)
    .data(rows=[2, 3], columns=[1, 2, 3, 4])
    .headers_above("year", row=0, span="right")
    .headers_above("quarter", row=1)
    .headers_left("country", column=0)
    .to_frame()
)
assert len(result) == 8
assert result["year"].tolist() == [2024, 2024, 2025, 2025] * 2
print(result[["country", "year", "quarter", "value", "row", "column"]])
```

The example reconstructs **2 quarterly observations**: Mexico / 2024 / Q1 / 10 and Mexico / 2024 / Q2 / 20.

## What you gain

Compose spatial header associations, explicit region boundaries and arbitrary coordinate maps. Every output value and header retains its physical and anchor positions.

| Existing approach | What this package adds | Tradeoff |
|---|---|---|
| Pandas indexing, `melt` and MultiIndex reshape known rectangles; openpyxl reads workbook cells and merged ranges. | Header-cell coordinates, original merged-anchor coordinates, bounds validation and composable mappings. | Grid snapshots and provenance use memory and time. A manual pandas recipe is shorter for some already understood rectangular layouts. |

[Run the side-by-side comparison](docs/comparison.md): both implementations are included and their shared outputs are asserted equal. [unpivotr](https://nacnudus.github.io/unpivotr/) inspires spatial header association. This package implements a focused subset; formatting, HTML and automatic partitioning remain outside its scope.

## Solve a real workflow problem

These small, synthetic operational fixtures make the workflows reproducible without external services or private records. Each recipe includes expected results and a failure or interpretation boundary.

| Recipe | Verified outcome |
|---|---|
| [Unpivot a layered quarterly report](docs/cookbook.md#quarterly-sales) | Associate each layer explicitly and verify both year values point to the original year header. |
| [Keep an adjacent report out of the result](docs/cookbook.md#adjacent-tables) | Restrict the grid to the intended rectangle, carry the row heading down and reconstruct only the two sales values. |
| [Preserve merged Excel header provenance](docs/cookbook.md#merged-workbook-headers) | Create a temporary workbook, propagate merged values on read, and verify physical columns [1,2] both retain anchor column 1. |

From a checkout, after installing the package:

```sh
python examples/comparison.py
python examples/cookbook.py
```

The workbook recipe needs `python -m pip install "cellwalk[xlsx]==0.1.1"`. Its XLSX fixture is created and removed locally.

## Measured performance, accuracy and usability

Recorded on Windows-11-10.0.26200-SP0, CPython 3.13.5, with five rotating timed rounds. At the largest measured input size (2,000; see workload definition):

| Compared operation | Baseline median ms | Package median ms | Package / baseline |
|---|---:|---:|---:|
| Package / manual recipe | 121.563 | 130.389 | 1.07x |

Ratio = package median / baseline median; above 1 means higher latency. The package performs the extra diagnostic or provenance work described above. These single-host synthetic results have no universal speed guarantee. Allocation measurements and the smaller scales are in the full table.

[Measured table](benchmarks/RESULTS.md) · [Raw repeated samples](benchmarks/latest.json) · [Reproduction instructions](benchmarks/README.md)

Accuracy means agreement on the stated fixture outputs: Values, associated labels and data-cell coordinates are compared exactly to an explicit pandas coordinate recipe; dtype equality is disabled. The cookbook additionally verifies merged-anchor coordinates. Code-size counts are an inspectable usability proxy; no developer-time study was performed.

## Scope and limits

- All coordinates are zero-based. Call within() before data() to bound a region.
- Header spans are opt-in. Blank data cells are omitted by default; include_blank=True retains them.
- The XLSX extra reads saved values. Formulas need cached results and are never calculated by cellwalk.
- The used grid is held in memory. A genuinely distant populated cell or merged range can still enlarge it.

## Documentation

- [Start here](docs/index.md): choose a workflow and find the relevant guide.
- [Comparison and alternatives](docs/comparison.md): full code, shared behavior and added outputs.
- [Cookbook](docs/cookbook.md): three complete problem-solving recipes.
- [API and behavioral contracts](docs/api.md): exact semantics and errors.
- [Benchmark methodology](benchmarks/README.md): inputs, correctness checks, environment and limits.
- [Research and upstream credit](RESEARCH.md): R inspiration, existing Python tools and scope decisions.

## Develop and validate

```sh
python -m pip install -e ".[dev]"
python scripts/check_docs.py
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy src
```

MIT licensed. Contributions should include a reproducing example and the expected behavior. See [CONTRIBUTING.md](CONTRIBUTING.md).
