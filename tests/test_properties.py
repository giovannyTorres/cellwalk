import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st

from cellwalk import CellGrid


@given(
    st.lists(
        st.lists(st.one_of(st.none(), st.integers(-(2**60), 2**60)), min_size=5, max_size=5),
        min_size=1,
        max_size=12,
    )
)
@settings(max_examples=75, derandomize=True, deadline=None)
def test_all_cells_roundtrip_without_coercion(rows):
    frame = pd.DataFrame(rows, dtype=object)
    grid = CellGrid.from_dataframe(frame)
    result = grid.data(rows=range(len(rows)), columns=range(5), include_blank=True).to_frame()
    for position, value in enumerate(result["value"]):
        row, column = divmod(position, 5)
        assert value == rows[row][column]
        assert result["source_row"].iloc[position] == row
        assert result["source_column"].iloc[position] == column


@given(st.integers(1, 15), st.integers(1, 10))
@settings(max_examples=50, derandomize=True, deadline=None)
def test_generated_dimension_table(nrows, ncols):
    table = [[None] + [f"header-{col}" for col in range(ncols)]]
    table += [[f"row-{row}"] + [row * ncols + col for col in range(ncols)] for row in range(nrows)]
    result = (
        CellGrid.from_dataframe(pd.DataFrame(table, dtype=object))
        .data(rows=range(1, nrows + 1), columns=range(1, ncols + 1))
        .headers_above("feature", row=0)
        .headers_left("entity", column=0)
        .to_frame()
    )
    assert len(result) == nrows * ncols
    for position, record in result.iterrows():
        row, col = divmod(position, ncols)
        assert record["entity"] == f"row-{row}"
        assert record["feature"] == f"header-{col}"
        assert record["value"] == row * ncols + col
