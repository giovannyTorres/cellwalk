# Reproducible reconstruction benchmark

```bash
python benchmarks/benchmark.py --rows 2000 --repeat 5
```

The input has 2,000 entity rows beneath two header rows and four value columns:
10,010 physical cells and 8,000 output records. Year labels span pairs of
quarter columns. The manual Pandas recipe explicitly fills the year heading
row, then loops through data coordinates and assembles tidy values. An assertion
checks that data coordinates, values, years, quarters and entity labels agree
with cellwalk before timing.

Each implementation warms up once, followed by five perf_counter measurements.
tracemalloc peak is measured in a separate execution, excludes some native
allocations, and is not process RSS. [results.json](results.json) is the
authoritative latest run and includes environment, raw samples, median and
range, plus memory for each workflow.

The library also stores every source cell, validates rules and boundaries, and
returns physical and anchor coordinates for all three associated headers. The
manual reference only returns reconstructed values and data coordinates. The
recorded run shows additional time and memory cost for these capabilities;
no performance advantage is claimed. A specialized recipe may be preferable
when its layout is fixed and no reusable provenance is needed. Results from one
synthetic layout should not be generalized to every workbook.

## XLSX dimensions with distant formatting

```bash
python benchmarks/xlsx_extent.py --repeat 5
```

This separate benchmark saves identical 3-by-30 values in a clean sheet, a sheet
with formatting at row 200,000, and a sheet with formatting at column 16,384.
It verifies every returned value and the 3-by-30 grid before timing. The reported
worksheet rectangles include respectively 90, 6,000,000 and 49,152 cells; only
90 grid cells are materialized in each case. Results include full workbook load
time and a separate tracemalloc peak, and avoid constructing the old inflated
grid merely to measure it. [xlsx_extent_results.json](xlsx_extent_results.json)
records the current measurements; these small synthetic files do not establish
load performance for dense or heavily merged workbooks.
