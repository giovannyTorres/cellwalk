"""Independent reconstruction checks using explicit spatial relationships."""

from __future__ import annotations

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from cellwalk import CellGrid


def _matrix():
    return pd.DataFrame(
        [
            [None, 2024, None, 2025, None],
            [None, "Q1", "Q2", "Q1", "Q2"],
            ["Mexico", 10, 20, 30, 40],
            ["Chile", 15, 25, 35, 45],
        ],
        index=[7, 7, 1, 1],
        dtype=object,
    )


def test_explicit_multidimensional_reconstruction_preserves_coordinates():
    source = _matrix()
    original = source.copy(deep=True)
    grid = CellGrid.from_dataframe(source)
    selected = grid.data(rows=[2, 3], columns=[1, 2, 3, 4])
    result = (
        selected.headers_above("year", row=0, span="right")
        .headers_above("quarter", row=1)
        .headers_left("country", column=0)
        .to_frame()
    )
    actual = {
        (row.country, row.year, row.quarter): row.value for row in result.itertuples(index=False)
    }
    assert actual == {
        (country, year, quarter): value
        for country, numbers in [("Mexico", [10, 20, 30, 40]), ("Chile", [15, 25, 35, 45])]
        for year, quarter, value in zip(
            [2024, 2024, 2025, 2025], ["Q1", "Q2", "Q1", "Q2"], numbers, strict=True
        )
    }
    assert set(zip(result["row"], result["column"], strict=True)) == {
        (row, column) for row in [2, 3] for column in [1, 2, 3, 4]
    }
    assert result.loc[result["column"] == 2, "year_column"].tolist() == [1, 1]
    assert result.loc[result["column"] == 4, "year_column"].tolist() == [3, 3]
    assert_frame_equal(source, original)
    assert "year" not in selected.to_frame()


def test_navigation_skips_blanks_only_when_requested():
    grid = CellGrid.from_dataframe(
        pd.DataFrame([["north", None, "east"], [None, None, None], ["south", None, "target"]])
    )
    assert grid.above(2, 0).value == "north"
    assert grid.above(2, 0, skip_blank=False).row == 1
    assert grid.left(2, 2).value == "south"
    assert grid.left(2, 2, skip_blank=False).column == 1
    assert grid.below(0, 0).value == "south"
    assert grid.right(0, 0).value == "east"
    assert grid.above(0, 0) is None
    assert grid.below(2, 0) is None
    assert grid.left(0, 0) is None
    assert grid.right(0, 2) is None


def test_navigation_respects_explicit_region():
    grid = CellGrid.from_dataframe(
        pd.DataFrame([["outside", None, None], [None, None, None], [None, None, "target"]])
    )
    restricted = grid.within(1, 3, 1, 3)
    assert restricted.above(2, 2) is None
    assert restricted.left(2, 2) is None
    assert restricted.above(2, 2, skip_blank=False).row == 1
    with pytest.raises(ValueError):
        restricted.above(0, 0)


def test_span_cannot_reach_outside_region_to_find_header():
    grid = CellGrid.from_dataframe(pd.DataFrame([[2024, None, None], [1, 2, 3]], dtype=object))
    restricted = grid.within(0, 2, 1, 3).data(rows=[1], columns=[1, 2])
    with pytest.raises(ValueError):
        restricted.headers_above("year", row=0, span="right")


def test_arbitrary_mapping_reconstructs_nonrectangular_headers():
    source = pd.DataFrame([["A", None, "B"], [None, 10, None], [None, None, 20]], dtype=object)
    result = (
        CellGrid.from_dataframe(source)
        .data(rows=[1, 2], columns=[1, 2])
        .associate("group", mapping={(1, 1): (0, 0), (2, 2): (0, 2)})
        .to_frame()
    )
    assert result["value"].tolist() == [10, 20]
    assert result["group"].tolist() == ["A", "B"]
    assert result["group_row"].tolist() == [0, 0]
    assert result["group_column"].tolist() == [0, 2]


def test_exact_large_integer_and_boolean_data_values():
    large = 2**53 + 1
    grid = CellGrid.from_dataframe(
        pd.DataFrame([["header", None], [large, None], [False, 1]], dtype=object)
    )
    result = grid.data(rows=[1, 2], columns=[0, 1], include_blank=True).to_frame()
    assert int(result["value"].iloc[0]) == large
    assert result["value"].iloc[2] is False


def test_exact_large_integer_is_not_rounded_by_missing_output_values():
    large = 2**53 + 1
    source = pd.DataFrame([[large, None]], dtype=object)
    result = (
        CellGrid.from_dataframe(source)
        .data(rows=[0], columns=[0, 1], include_blank=True)
        .to_frame()
    )
    assert int(result["value"].iloc[0]) == large


def test_object_tuple_and_false_cells_are_data_while_nulls_are_skipped():
    source = pd.DataFrame([[("a", 1), False, pd.NaT]], dtype=object)
    result = CellGrid.from_dataframe(source).data(rows=[0], columns=[0, 1, 2]).to_frame()
    assert result["value"].tolist() == [("a", 1), False]
    assert result["column"].tolist() == [0, 1]


def test_grid_snapshots_input_and_returns_independent_output_frames():
    source = pd.DataFrame([["header"], [10]], dtype=object)
    grid = CellGrid.from_dataframe(source).data(rows=[1], columns=[0])
    source.iloc[1, 0] = 999
    output = grid.to_frame()
    output.loc[:, "value"] = -1
    assert grid.to_frame()["value"].tolist() == [10]


def test_explicit_data_coordinate_order_is_retained():
    result = CellGrid.from_dataframe(_matrix()).data(rows=[3, 2], columns=[4, 1]).to_frame()
    assert list(zip(result["row"], result["column"], strict=True)) == [
        (3, 4),
        (3, 1),
        (2, 4),
        (2, 1),
    ]
    assert result["value"].tolist() == [45, 15, 40, 10]


def test_empty_region_keeps_output_schema_and_rejects_cell_access():
    empty = CellGrid.from_dataframe(_matrix()).within(1, 1, 2, 2).data(rows=[], columns=[])
    result = empty.to_frame()
    assert result.empty
    assert result.columns.tolist() == ["row", "column", "source_row", "source_column", "value"]
    with pytest.raises(ValueError):
        empty.cell(1, 2)


@pytest.mark.parametrize("bounds", [(-1, 2, 0, 2), (0, 5, 0, 2), (2, 1, 0, 2), (0, 2, 2, 1)])
def test_invalid_regions_rejected(bounds):
    with pytest.raises(ValueError):
        CellGrid.from_dataframe(_matrix()).within(*bounds)


def test_restricted_region_cannot_be_widened_by_nested_within():
    restricted = CellGrid.from_dataframe(_matrix()).within(1, 4, 1, 5)
    with pytest.raises(ValueError):
        restricted.within(0, 4, 0, 5)


def test_generated_header_metadata_names_cannot_collide():
    grid = CellGrid.from_dataframe(pd.DataFrame([["header"], [1]])).data(rows=[1], columns=[0])
    first = grid.headers_above("label", row=0)
    with pytest.raises(ValueError):
        first.headers_above("label_source", row=0)


@pytest.mark.parametrize("name", ["row", "column", "value", "source_row", "source_column"])
def test_header_names_cannot_overwrite_provenance(name):
    grid = CellGrid.from_dataframe(pd.DataFrame([["header"], [1]])).data(rows=[1], columns=[0])
    with pytest.raises(ValueError):
        grid.headers_above(name, row=0)


def test_explicit_missing_header_policy_is_structured():
    grid = CellGrid.from_dataframe(pd.DataFrame([[None, None], [1, 2]], dtype=object)).data(
        rows=[1], columns=[0, 1]
    )
    result = grid.headers_above("label", row=0, missing="none").to_frame()
    assert result["label"].isna().all()
    assert result["label_row"].isna().all()


def test_xlsx_merged_headers_keep_anchor_provenance_and_formulas_unexecuted(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Data"
    sheet.append([None, 2024, None])
    sheet.merge_cells("B1:C1")
    sheet.append([None, "Q1", "Q2"])
    sheet.append(["Mexico", 10, 20])
    sheet["A5"] = "=1+1"
    path = tmp_path / "merged.xlsx"
    workbook.save(path)
    grid = CellGrid.from_xlsx(path, sheet="Data", merged="propagate")
    result = grid.data(rows=[2], columns=[1, 2]).headers_above("year", row=0).to_frame()
    assert result["year"].tolist() == [2024, 2024]
    assert result["year_column"].tolist() == [1, 2]
    assert result["year_source_column"].tolist() == [1, 1]
    assert result["year_source_row"].tolist() == [0, 0]
    formula = grid.data(rows=[4], columns=[0], include_blank=True).to_frame()
    assert pd.isna(formula["value"].iloc[0])
