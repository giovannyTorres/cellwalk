# Changelog

## 0.1.1 — 2026-10-21

- Ignore trailing XLSX rows and columns containing formatting only, avoiding
  expansion of distant styled cells into millions of empty grid cells.
- Preserve physical coordinates of leading/interior blanks, uncached formulas,
  and explicit merged ranges. Empty worksheets now produce a zero-by-zero grid.

## 0.1.0 — 2026-10-21

- Initial independently installable release of cellwalk.
- Typed public API, original implementations, executable examples, tests, and reproducible benchmarks.

Publication state is recorded in RELEASE.md; this version number alone does not imply a PyPI upload.
