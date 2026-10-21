"""Real XLSX regression fixtures for sparse worksheet dimensions."""

from __future__ import annotations

from xml.etree import ElementTree
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from cellwalk import CellGrid, GridError


@pytest.mark.parametrize("styled_position", [(200_000, 30), (3, 16_384)])
def test_distant_formatting_does_not_expand_content_bounds(tmp_path, styled_position):
    openpyxl = pytest.importorskip("openpyxl")
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    for row in range(1, 4):
        sheet.append([row * column for column in range(1, 31)])
    sheet.cell(*styled_position).number_format = "0.00"
    path = tmp_path / "styled.xlsx"
    workbook.save(path)
    workbook.close()
    before = path.read_bytes()

    grid = CellGrid.from_xlsx(path)

    assert (grid.nrows, grid.ncolumns, grid.bounds) == (3, 30, (0, 3, 0, 30))
    assert grid.cell(2, 29).value == 90
    with pytest.raises(GridError, match="outside"):
        grid.cell(3, 0)
    assert path.read_bytes() == before


def test_leading_and_interior_blanks_and_false_values_keep_coordinates(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet["C3"] = 0
    sheet["E5"] = False
    sheet["G7"] = " "
    sheet["Z100"] = None
    path = tmp_path / "blanks.xlsx"
    workbook.save(path)
    workbook.close()

    grid = CellGrid.from_xlsx(path)

    assert (grid.nrows, grid.ncolumns) == (7, 7)
    assert grid.cell(0, 0).value is None
    assert grid.cell(3, 3).value is None
    assert grid.cell(2, 2).value == 0
    assert grid.cell(4, 4).value is False
    assert grid.cell(6, 6).value == " "


@pytest.mark.parametrize("merged", ["blank", "propagate"])
def test_merged_extent_and_anchor_provenance_survive_trimming(tmp_path, merged):
    openpyxl = pytest.importorskip("openpyxl")
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet["B2"] = "heading"
    sheet.merge_cells("B2:E4")
    sheet.merge_cells("G6:H7")  # Blank merged ranges still describe geometry.
    sheet["Z100"].number_format = "0.00"
    path = tmp_path / "merged.xlsx"
    workbook.save(path)
    workbook.close()

    grid = CellGrid.from_xlsx(path, merged=merged)

    assert (grid.nrows, grid.ncolumns) == (7, 8)
    child = grid.cell(3, 4)
    assert (child.source_row, child.source_column) == (1, 1)
    assert child.value == ("heading" if merged == "propagate" else None)
    empty_child = grid.cell(6, 7)
    assert (empty_child.source_row, empty_child.source_column) == (5, 6)
    assert empty_child.value is None


@pytest.mark.parametrize("formatting", [False, True])
def test_empty_worksheet_has_no_cells(tmp_path, formatting):
    openpyxl = pytest.importorskip("openpyxl")
    workbook = openpyxl.Workbook()
    if formatting:
        workbook.active["Z200000"].number_format = "0.00"
    path = tmp_path / "empty.xlsx"
    workbook.save(path)
    workbook.close()

    grid = CellGrid.from_xlsx(path)

    assert (grid.nrows, grid.ncolumns, grid.bounds) == (0, 0, (0, 0, 0, 0))
    assert grid.data(rows=[], columns=[]).to_frame().empty


@pytest.mark.parametrize("cached_value", [None, 2])
def test_formula_only_extent_retains_coordinates_and_cached_value(tmp_path, cached_value):
    openpyxl = pytest.importorskip("openpyxl")
    workbook = openpyxl.Workbook()
    workbook.active["E5"] = "=1+1"
    workbook.active["Z200000"].number_format = "0.00"
    path = tmp_path / "formula.xlsx"
    workbook.save(path)
    workbook.close()
    if cached_value is not None:
        # openpyxl writes formulas without caches. Supply the saved result that
        # Excel would write, without calculating or executing the expression.
        with ZipFile(path) as archive:
            parts = {name: archive.read(name) for name in archive.namelist()}
        name = "xl/worksheets/sheet1.xml"
        root = ElementTree.fromstring(parts[name])
        namespace = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
        value = root.find(f".//{namespace}c[@r='E5']/{namespace}v")
        assert value is not None
        value.text = str(cached_value)
        parts[name] = ElementTree.tostring(root)
        with ZipFile(path, "w", ZIP_DEFLATED) as archive:
            for name, content in parts.items():
                archive.writestr(name, content)
    before = path.read_bytes()

    grid = CellGrid.from_xlsx(path)

    assert (grid.nrows, grid.ncolumns) == (5, 5)
    assert grid.cell(4, 4).value == cached_value
    assert path.read_bytes() == before
