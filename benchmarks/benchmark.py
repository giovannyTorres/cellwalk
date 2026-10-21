"""Benchmark reconstruction against a manual coordinate-based Pandas recipe."""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import time
import tracemalloc
from collections.abc import Callable
from pathlib import Path

import pandas as pd
from pandas.testing import assert_frame_equal

from cellwalk import CellGrid


def manual(frame: pd.DataFrame) -> pd.DataFrame:
    """Explicit Pandas coordinate recipe for one already-understood layout."""
    years = frame.iloc[0, 1:].ffill().tolist()
    quarters = frame.iloc[1, 1:].tolist()
    records = []
    for row in range(2, len(frame)):
        for column in range(1, len(frame.columns)):
            records.append(
                [
                    row,
                    column,
                    frame.iat[row, column],
                    years[column - 1],
                    quarters[column - 1],
                    frame.iat[row, 0],
                ]
            )
    return pd.DataFrame(
        records, columns=["row", "column", "value", "year", "quarter", "entity"], dtype=object
    )


def library(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        CellGrid.from_dataframe(frame)
        .data(rows=range(2, len(frame)), columns=range(1, len(frame.columns)))
        .headers_above("year", row=0, span="right")
        .headers_above("quarter", row=1)
        .headers_left("entity", column=0)
        .to_frame()
    )


def measure(operation: Callable[[], object], repeats: int) -> dict[str, object]:
    operation()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        operation()
        samples.append(time.perf_counter() - start)
    tracemalloc.start()
    operation()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "seconds": samples,
        "median_seconds": statistics.median(samples),
        "min_seconds": min(samples),
        "max_seconds": max(samples),
        "traced_peak_bytes": peak,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=2_000)
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--output", type=Path, default=Path("benchmarks/results.json"))
    args = parser.parse_args()
    if args.rows < 1 or args.repeat < 2:
        parser.error("rows must be >=1 and repeat >=2")
    raw = [[None, 2024, None, 2025, None], [None, "Q1", "Q2", "Q1", "Q2"]]
    raw.extend([[f"entity-{row}", row, row + 1, row + 2, row + 3] for row in range(args.rows)])
    frame = pd.DataFrame(raw, dtype=object)
    columns = ["row", "column", "value", "year", "quarter", "entity"]
    assert_frame_equal(library(frame)[columns], manual(frame), check_dtype=False)
    result = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "pandas": pd.__version__,
        "data_rows": args.rows,
        "input_cells": frame.size,
        "output_records": args.rows * 4,
        "repeats": args.repeat,
        "manual_pandas": measure(lambda: manual(frame), args.repeat),
        "cellwalk": measure(lambda: library(frame), args.repeat),
        "notes": "Identical reconstructed values and data coordinates. Library additionally returns all header physical and anchor coordinates and validates bounds/rules. Memory measured separately with tracemalloc, not process RSS.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
