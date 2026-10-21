"""Isolate separate blocks and map nonrectangular header positions explicitly."""

import pandas as pd

from cellwalk import CellGrid

raw = pd.DataFrame(
    [
        ["A", None, 2024, None, "unrelated"],
        [None, 10, 20, None, "other block"],
        ["B", 30, None, None, 999],
    ],
    dtype=object,
)
grid = CellGrid.from_dataframe(raw).within(0, 3, 0, 3)
result = (
    grid.data(rows=[1, 2], columns=[1, 2])
    .associate("group", {(1, 1): (0, 0), (1, 2): (0, 0), (2, 1): (2, 0)})
    .associate("year", {(1, 1): (0, 2), (1, 2): (0, 2), (2, 1): (0, 2)})
    .to_frame()
)
assert result["group"].tolist() == ["A", "A", "B"]
assert result["value"].tolist() == [10, 20, 30]
print(result[["group", "year", "value", "group_row", "group_column"]])
