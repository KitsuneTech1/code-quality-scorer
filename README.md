# code-quality-scorer

Score a code repository on tests, documentation, dependency files, and source size. The result is deterministic, uses four equal weights, and includes the detail behind each score.

## What it does

The scorer returns a total from 0 to 100:

- Tests: 25% of the total
- Documentation: 25%
- Dependencies: 25%
- Size: 25%

It uses only the Python standard library. It does not make model calls or network requests.

## Installation

There is nothing to install. Run the script with Python 3.8 or newer:

```bash
python score_repo.py <repo_path> [--format text|json]
```

## Usage

Human-readable output is the default:

```bash
python score_repo.py /path/to/repo
```

Use JSON for scripts:

```bash
python score_repo.py /path/to/repo --format json
```

Each result contains `total` and a `breakdown` with `score`, `max`, and `detail` for all four dimensions. A category score is never higher than 25, so the total is the sum of the four category scores.

## Scoring rules

The scanner ignores hidden paths and these common generated or dependency directories: `.git`, `.hg`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `.svn`, `.tox`, `__pycache__`, `build`, `dist`, `node_modules`, `site-packages`, `.venv`, and `venv`. Symlinks are ignored.

### Tests

Test files are regular files with a supported test naming convention. The scorer recognizes files inside `test`, `tests`, `spec`, or `specs` directories, plus names such as `test_*.py`, `*_test.py`, `*.test.js`, and `*.spec.js`. The score is based on the number of files:

- 0 files: 0 points
- 1 or 2 files: 10 points
- 3 to 9 files: 18 points
- 10 or more files: 25 points

This counts test files. It does not measure test coverage or run the tests.

### Documentation

- Root `README.md`: 10 points
- Root `README`, `README.txt`, or `README.rst`: 7 points when `README.md` is absent
- Files below `docs/`: 2 points per file, up to 10 points
- Python module, class, and function docstrings: 1 point each, up to 5 points

Python files that cannot be parsed are skipped for the docstring count.

### Dependencies

The scorer checks for common manifests and matching lock files. It checks file presence, not the contents or freshness of a dependency list.

- `pyproject.toml`: 8 points, otherwise `requirements.txt`: 5, otherwise `setup.py`: 3
- `poetry.lock` with a Python manifest: 5 points
- `package.json`: 5 points
- `package-lock.json` or `yarn.lock` with `package.json`: 5 points
- `Cargo.toml`: 8 points
- `Cargo.lock` with `Cargo.toml`: 5 points

The category is capped at 25 points. A lock file without its matching manifest does not receive a lock-file bonus.

### Size

Size counts lines in visible files with these extensions: `.py`, `.js`, `.rs`, `.go`, `.java`, and `.cs`.

- Under 500 lines: 25 points
- 500 to 1,999 lines: 20 points
- 2,000 to 4,999 lines: 15 points
- 5,000 to 9,999 lines: 10 points
- 10,000 or more lines: 5 points
- No supported source files: 0 points

## Testing

```bash
python -m unittest test_score_repo
```

## License

MIT License

Copyright (c) 2026 KitsuneTech1
