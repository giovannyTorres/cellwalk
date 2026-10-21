import builtins
from decimal import Decimal

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from cellwalk import Cell, CellGrid, GridError


def test_explicit_target_order_blanks_and_snapshot():
    frame = pd.DataFrame(
        [["a", 0, False], [None, " ", Decimal("1.23")]],
        dtype=object,
        index=["same", "same"],
        columns=["same", "same", "same"],
    )
    before = frame.copy(deep=True)
    grid = CellGrid.from_dataframe(frame)
    assert grid.cell(0, 0) == Cell(0, 0, "a", 0, 0)
    result = grid.data(rows=[1, 0], columns=[2, 1, 0]).to_frame()
    assert result["value"].tolist() == [Decimal("1.23"), False, 0, "a"]
    assert result[["row", "column"]].values.tolist() == [[1, 2], [0, 2], [0, 1], [0, 0]]
    all_cells = grid.data(rows=[0, 1], columns=[0, 1, 2], include_blank=True).to_frame()
    assert len(all_cells) == 6
    frame.iat[0, 0] = "changed"
    assert grid.cell(0, 0).value == "a"
    assert_frame_equal(
        before,
        pd.DataFrame(
            [["a", 0, False], [None, " ", Decimal("1.23")]],
            dtype=object,
            index=["same", "same"],
            columns=["same"] * 3,
        ),
    )


def test_empty_grid_and_selection():
    grid = CellGrid.from_dataframe(pd.DataFrame(columns=["a", "b"]))
    assert grid.to_frame().columns.tolist() == [
        "row",
        "column",
        "source_row",
        "source_column",
        "value",
    ]
    assert grid.data(rows=[], columns=[0]).to_frame().empty
    assert grid.within(0, 0, 0, 2).to_frame().empty
    with pytest.raises(GridError):
        grid.cell(0, 0)


def test_nearest_navigation_all_boundaries():
    grid = CellGrid.from_dataframe(
        pd.DataFrame([["a", None, "b"], [None, "center", None], ["c", None, "d"]])
    )
    assert grid.above(2, 0).value == "a"
    assert grid.below(0, 2).value == "d"
    assert grid.left(0, 2).value == "a"
    assert grid.right(2, 0).value == "d"
    assert grid.above(0, 0) is None
    assert grid.below(2, 0) is None
    assert grid.left(0, 0) is None
    assert grid.right(0, 2) is None
    assert pd.isna(grid.right(0, 0, skip_blank=False).value)
    with pytest.raises(GridError):
        grid.left(-1, 0)


def test_header_down_span_and_missing_policy():
    frame = pd.DataFrame([["G1", 1], [None, 2], ["G2", 3], [None, 4]])
    grid = CellGrid.from_dataframe(frame).data(rows=[0, 1, 2, 3], columns=[1])
    result = grid.headers_left("group", column=0, span="down").to_frame()
    assert result["group"].tolist() == ["G1", "G1", "G2", "G2"]
    assert result["group_row"].tolist() == [0, 0, 2, 2]
    with pytest.raises(GridError, match="Missing header"):
        grid.headers_left("group", column=0)
    nullable = grid.headers_left("group", column=0, missing="none").to_frame()
    assert nullable["group"].tolist() == ["G1", None, "G2", None]


def test_nonrectangular_mapping_and_reselection():
    grid = CellGrid.from_dataframe(
        pd.DataFrame([["Top", None, "Right"], [None, 42, None], ["Bottom", 7, None]])
    )
    selected = grid.data(rows=[1, 2], columns=[1])
    result = selected.associate("label", {(1, 1): (0, 2), (2, 1): (2, 0)}).to_frame()
    assert result["label"].tolist() == ["Right", "Bottom"]
    assert result["label_column"].tolist() == [2, 0]
    assert "label" not in selected.to_frame()
    associated = selected.associate("label", {(1, 1): (0, 2)}, missing="none")
    assert associated.to_frame()["label"].tolist() == ["Right", None]
    assert "label" not in associated.data(rows=[1], columns=[1]).to_frame()
    assert associated.within(1, 3, 0, 3).to_frame().empty


@pytest.mark.parametrize(
    "bounds", [(-1, 2, 0, 2), (0, 3, 0, 2), (1, 0, 0, 2), (0, 2, 1, 0), (True, 2, 0, 2)]
)
def test_invalid_region(bounds):
    with pytest.raises(GridError):
        CellGrid.from_dataframe(pd.DataFrame([[1, 2], [3, 4]])).within(*bounds)


@pytest.mark.parametrize(
    "rows,columns", [([0, 0], [1]), ([False], [1]), ([0.5], [1]), ([0], [2]), ([-1], [1])]
)
def test_invalid_data_positions(rows, columns):
    with pytest.raises(GridError):
        CellGrid.from_dataframe(pd.DataFrame([[1, 2]])).data(rows=rows, columns=columns)


def test_invalid_association_rules():
    grid = CellGrid.from_dataframe(pd.DataFrame([["x", None], ["a", 2]])).data(
        rows=[1], columns=[1]
    )
    with pytest.raises(GridError, match="above"):
        grid.headers_above("h", row=1)
    with pytest.raises(GridError, match="left"):
        grid.headers_left("h", column=1)
    for row, span in [(3, "none"), (0, "guess"), (True, "none")]:
        with pytest.raises(GridError):
            grid.headers_above("h", row=row, span=span)
    for column, span in [(3, "none"), (0, "guess"), (True, "none")]:
        with pytest.raises(GridError):
            grid.headers_left("h", column=column, span=span)
    for name in ["", 1, "value", "row", "source_row"]:
        with pytest.raises(GridError):
            grid.headers_left(name, column=0)
    with pytest.raises(GridError, match="missing"):
        grid.headers_left("h", column=0, missing="guess")
    with pytest.raises(GridError, match="outside the selected"):
        grid.associate("h", {(0, 0): (0, 0)})
    with pytest.raises(GridError, match="Missing"):
        grid.associate("h", {})
    with pytest.raises(GridError, match="tuples"):
        grid.associate("h", {(1, 1): (0,)})
    with pytest.raises(GridError, match="collides"):
        grid.headers_left("group", column=0).headers_left("group_row", column=0)
    with pytest.raises(TypeError):
        CellGrid.from_dataframe([[1]])


def test_xlsx_sheet_merged_values_and_file_unchanged(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Data"
    sheet.append(["Year", 2024, None])
    sheet.merge_cells("B1:C1")
    sheet.append(["Mexico", 10, 20])
    path = tmp_path / "merged.xlsx"
    workbook.save(path)
    workbook.close()
    before = path.read_bytes()
    plain = CellGrid.from_xlsx(path, sheet="Data")
    assert plain.cell(0, 2).value is None
    assert plain.cell(0, 2).source_column == 1
    propagated = CellGrid.from_xlsx(path, merged="propagate")
    assert propagated.cell(0, 2).value == 2024
    assert propagated.cell(0, 2).column == 2
    assert propagated.cell(0, 2).source_column == 1
    assert path.read_bytes() == before
    for missing_sheet in [-1, 1, "missing", True, 1.5]:
        with pytest.raises(GridError, match="sheet"):
            CellGrid.from_xlsx(path, sheet=missing_sheet)
    with pytest.raises(GridError, match="merged"):
        CellGrid.from_xlsx(path, merged="guess")


def test_optional_xlsx_dependency_error(monkeypatch):
    real_import = builtins.__import__

    def import_without_openpyxl(name, *args, **kwargs):
        if name == "openpyxl":
            raise ImportError("intentionally unavailable optional dependency")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_openpyxl)
    with pytest.raises(ImportError, match="cellwalk\\[xlsx\\]"):
        CellGrid.from_xlsx("unused.xlsx")
