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
