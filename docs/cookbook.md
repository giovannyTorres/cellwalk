# Cookbook: cellwalk

Three common operational problems, with complete Python code and asserted outcomes. The records are **synthetic fixtures modeled on real workflows**, not measurements from a business or real customer data.

Install `python -m pip install "cellwalk==0.1.1"`. From a checkout, run all three with `python examples/cookbook.py`.

For the workbook recipe install `python -m pip install "cellwalk[xlsx]==0.1.1"`. openpyxl creates a temporary fixture; no workbook download is required.

<a id="quarterly-sales"></a>
## Unpivot a layered quarterly report

**Problem.** One year heading spans Q1 and Q2 while the country is stored in a left-hand column.

**Expected result.** Associate each layer explicitly and verify both year values point to the original year header.

Copy the complete block into a fresh Python file and run it:

```python
from pathlib import Path
from tempfile import TemporaryDirectory
import pandas as pd
from cellwalk import CellGrid


def quarterly_sales():
    raw = pd.DataFrame([[None, 2024, None], [None, "Q1", "Q2"], ["Mexico", 10, 20]], dtype=object)
    result = (
        CellGrid.from_dataframe(raw)
        .data(rows=[2], columns=[1, 2])
        .headers_above("year", row=0, span="right")
        .headers_above("quarter", row=1)
        .headers_left("country", column=0)
        .to_frame()
    )
    assert result["value"].tolist() == [10, 20]
    assert result["year_source_column"].tolist() == [1, 1]
    return result[["country", "year", "quarter", "value"]]


print(quarterly_sales())
```

**Apply it to your data.** A blank header child is a span only when you request span="right".

<a id="adjacent-tables"></a>
## Keep an adjacent report out of the result

**Problem.** A second block shares the worksheet but must not leak headers or values into the selected sales table.

**Expected result.** Restrict the grid to the intended rectangle, carry the row heading down and reconstruct only the two sales values.

Copy the complete block into a fresh Python file and run it:

```python
from pathlib import Path
from tempfile import TemporaryDirectory
import pandas as pd
from cellwalk import CellGrid


def adjacent_tables():
    raw = pd.DataFrame(
        [
            ["country", "sales", None, "unrelated"],
            ["MX", 10, None, 999],
            [None, 20, None, "other table"],
        ],
        dtype=object,
    )
    result = (
        CellGrid.from_dataframe(raw)
        .within(0, 3, 0, 2)
        .data(rows=[1, 2], columns=[1])
        .headers_above("metric", row=0)
        .headers_left("country", column=0, span="down")
        .to_frame()
    )
    assert result["country"].tolist() == ["MX", "MX"]
    assert result["value"].tolist() == [10, 20]
    assert result["column"].tolist() == [1, 1]
    return result[["country", "metric", "value"]]


print(adjacent_tables())
```

**Apply it to your data.** within() clears previous selections and associations; apply it before selecting data.

<a id="merged-workbook-headers"></a>
## Preserve merged Excel header provenance

**Problem.** An XLSX year heading is physically merged across two quarter columns.

**Expected result.** Create a temporary workbook, propagate merged values on read, and verify physical columns [1,2] both retain anchor column 1.

Copy the complete block into a fresh Python file and run it:

```python
from pathlib import Path
from tempfile import TemporaryDirectory
import pandas as pd
from cellwalk import CellGrid


def merged_workbook_headers():
    from openpyxl import Workbook

    with TemporaryDirectory() as directory:
        path = Path(directory) / "sales.xlsx"
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Sales"
        sheet.append([None, 2024, None])
        sheet.merge_cells("B1:C1")
        sheet.append([None, "Q1", "Q2"])
        sheet.append(["Mexico", 10, 20])
        workbook.save(path)
        workbook.close()
        result = (
            CellGrid.from_xlsx(path, sheet="Sales", merged="propagate")
            .data(rows=[2], columns=[1, 2])
            .headers_above("year", row=0)
            .headers_above("quarter", row=1)
            .to_frame()
        )
        assert result["year_column"].tolist() == [1, 2]
        assert result["year_source_column"].tolist() == [1, 1]
        return result[["year", "quarter", "value", "year_column", "year_source_column"]]


print(merged_workbook_headers())
```

**Apply it to your data.** Install the xlsx extra. The recipe is local and self-contained, and the temporary workbook is removed afterwards.

[API details and error policies](api.md) · [Comparison with primitives](comparison.md) · [Benchmark evidence](../benchmarks/RESULTS.md)
