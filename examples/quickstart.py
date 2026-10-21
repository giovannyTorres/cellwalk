"""Reconstruct a two-level quarterly table with explicit header spans."""

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
