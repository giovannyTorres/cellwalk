"""Three spreadsheet reconstruction problems using local synthetic fixtures."""

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


if __name__ == "__main__":
    for recipe in (quarterly_sales, adjacent_tables, merged_workbook_headers):
        print(recipe.__name__, recipe(), sep="\n")
