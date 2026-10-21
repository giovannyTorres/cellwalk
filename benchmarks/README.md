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
