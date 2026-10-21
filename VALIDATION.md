# Local validation record — cellwalk 0.1.0

Recorded from completed local checks on 2026-10-21 (UTC).
These results are separate from GitHub CI and from public PyPI installation.

| Check | Observed result |
|---|---|
| Editable installation with development dependencies | Passed |
| Pytest and coverage threshold | Passed |
| Ruff lint | Passed |
| Ruff formatting | Passed |
| Mypy, src/ | Passed |
| Wheel and sdist build | Passed |
| Twine distribution metadata checks | Passed |
| Independent clean wheel and sdist installations and shipped examples | Passed |
| Benchmark execution | Passed |

**Tests:** 44 passed.
**Statement coverage:** 100.00% (169 of 169 measured statements; 0 excluded lines). This is not a branch-coverage claim.

Wheel and sdist were installed separately in fresh virtual environments with declared runtime dependencies.
The shipped examples ran with Python's `-I` flag, isolating imports from the repository checkout.
These installations used local distribution files, not a public-index upload.

## Recorded benchmark

Environment: python: `3.13.5`; pandas: `3.0.6`; platform: `Windows-11-10.0.26200-SP0`.

data_rows: **2,000**; input_cells: **10,010**; output_records: **8,000**; repeats: **5**.

The synthetic worksheet has 2,000 entity rows, two header rows and five columns: 10,010 physical cells yield 8,000 data records. Year labels span pairs of quarter columns. Before timing, the manual coordinate-based Pandas recipe and library outputs are asserted equal for data row/column coordinates, values, year, quarter and entity. Each workflow warms up once, then records five perf_counter durations. Tracemalloc peak is collected in a separate execution. The library additionally validates boundaries/rules and retains physical and anchor coordinates for all associated headers.

| Workflow | Median seconds | Minimum–maximum seconds | Peak traced bytes |
|---|---:|---:|---:|
| `manual_pandas` | 0.161509 | 0.158172–0.181253 | 1,727,924 |
| `cellwalk` | 0.178309 | 0.175621–0.200259 | 6,400,520 |

Identical reconstructed values and data coordinates. Library additionally returns all header physical and anchor coordinates and validates bounds/rules. Memory measured separately with tracemalloc, not process RSS.

The [raw measurement file](benchmarks/results.json) is the source of these numbers.
See [benchmark code](benchmarks/benchmark.py) and its documented methodology for workload details.
`tracemalloc` figures, when present, are traced allocations rather than process RSS.
No universal performance advantage follows from a single workload.

## Reproduce

```bash
python -m pip install -e ".[dev]"
python -m pytest --cov=cellwalk --cov-report=term-missing --cov-fail-under=95
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m build
python -m twine check dist/*
python scripts/check_artifacts.py cellwalk
python benchmarks/benchmark.py
```

See [RELEASE.md](RELEASE.md) for publication status and the Trusted Publisher configuration.
