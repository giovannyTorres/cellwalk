# Comparison: cellwalk and the underlying primitives

A report has years spanning quarter columns, country labels at the left and separate tables on the same sheet. cellwalk associates selected cells with explicit headers and preserves physical and merged-anchor coordinates.

## What is compared

| Dimension | Scope |
|---|---|
| Existing tools | Pandas indexing, `melt` and MultiIndex reshape known rectangles; openpyxl reads workbook cells and merged ranges. |
| Shared result checked | Same reconstructed values, headers and data-cell positions for a fixed quarterly layout. Comparison tolerates dtype representation differences. |
| Additional package behavior | Header-cell coordinates, original merged-anchor coordinates, bounds validation and composable mappings. |
| Cost / when a manual recipe fits | Grid snapshots and provenance use memory and time. A manual pandas recipe is shorter for some already understood rectangular layouts. |

[unpivotr](https://nacnudus.github.io/unpivotr/) inspires spatial header association. This package implements a focused subset; formatting, HTML and automatic partitioning remain outside its scope. The comparison below measures a Python workflow; it makes no claim of feature parity or numerical parity with an R package.

## Full executable example

Save this as `comparison.py` after installing the release, or run `python examples/comparison.py` from this repository. The assertions verify the stated shared result.

```python
"""Same values and data positions; cellwalk additionally tracks header anchors."""

import pandas as pd
from pandas.testing import assert_frame_equal

from cellwalk import CellGrid


def baseline(raw):
    years = raw.iloc[0, 1:].ffill().tolist()
    quarters = raw.iloc[1, 1:].tolist()
    records = [
        (r, c, raw.iat[r, c], years[c - 1], quarters[c - 1], raw.iat[r, 0])
        for r in range(2, len(raw))
        for c in range(1, raw.shape[1])
    ]
    return pd.DataFrame(
        records, columns=["row", "column", "value", "year", "quarter", "country"], dtype=object
    )


def library(raw):
    return (
        CellGrid.from_dataframe(raw)
        .data(rows=range(2, len(raw)), columns=range(1, raw.shape[1]))
        .headers_above("year", row=0, span="right")
        .headers_above("quarter", row=1)
        .headers_left("country", column=0)
        .to_frame()
    )


if __name__ == "__main__":
    raw = pd.DataFrame([[None, 2024, None], [None, "Q1", "Q2"], ["Mexico", 10, 20]], dtype=object)
    columns = ["row", "column", "value", "year", "quarter", "country"]
    assert_frame_equal(baseline(raw), library(raw)[columns], check_dtype=False)
    assert library(raw)["year_source_column"].tolist() == [1, 1]
    print("Both return two quarterly observations; both year values come from column 1.")
```

## How to choose

Use the package when you need its named diagnostics, explicit policies or provenance repeatedly. Keep the underlying pandas/Python recipe when that smaller shared result meets the job. Review each recipe's data assumptions before applying it to another dtype or layout.

Grid snapshots and provenance use memory and time. A manual pandas recipe is shorter for some already understood rectangular layouts.

## Evidence and boundaries

Values, associated labels and data-cell coordinates are compared exactly to an explicit pandas coordinate recipe; dtype equality is disabled. The cookbook additionally verifies merged-anchor coordinates.

This dense fixed-layout workload excludes sparse XLSX ingestion and arbitrary maps. The package returns more coordinate fields than the baseline, so output construction differs in scope. Timing differences do not establish statistical accuracy or developer productivity. The benchmark checks exact fixture outputs and separately reports code-size counts as a limited usability proxy.

[Actual measured results](../benchmarks/RESULTS.md) · [Reproduce the benchmark](../benchmarks/README.md) · [Recipes](cookbook.md) · [API contracts](api.md)

## Sources and alternatives

- [pandas API documentation](https://pandas.pydata.org/docs/reference/index.html) documents the underlying grouping, masking and reshaping primitives.
- [unpivotr spatial workflows](https://nacnudus.github.io/unpivotr/)
- [openpyxl documentation](https://openpyxl.readthedocs.io/en/stable/)

Upstream references credit problem ideas and existing tools. This repository contains its own implementation and claims no upstream affiliation.
