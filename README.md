<p align="center"><a href="https://kitsunetechnologies.org/work"><img src="https://raw.githubusercontent.com/KitsuneTech1/.github/main/assets/kitsune-banner.svg" alt="Built by Kitsune Technologies" width="760"></a></p>

# Repo Grade

Score a code repository on tests, documentation, dependency files, and source size.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)

The result is deterministic, weighted equally across four dimensions, and includes detail for each score.

## Quick start

Nothing to install. Python 3.8 or newer is the only requirement:

```bash
python score_repo.py /path/to/repo
```

For JSON output in scripts:

```bash
python score_repo.py /path/to/repo --format json
```

Each result shows the total from 0 to 100, plus a breakdown with `score`, `max`, and `detail` for Tests, Documentation, Dependencies, and Size. Each category is worth 25 points, so the total is their sum.

## How it works

Uses only Python's standard library. No external calls or network requests.

Scores on four equal dimensions:

- **Tests**: 25% - counts test files, does not measure coverage
- **Documentation**: 25% - README, docs/, and docstrings
- **Dependencies**: 25% - manifest and lock file presence
- **Size**: 25% - lines of code in supported languages

The scanner ignores hidden paths and standard generated directories: `.git`, `.hg`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `.svn`, `.tox`, `__pycache__`, `build`, `dist`, `node_modules`, `site-packages`, `.venv`, and `venv`. Symlinks are ignored.

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

MIT. Copyright (c) 2026 Kitsune Technologies LLC. Do what you like with it, commercially or otherwise, just keep the copyright notice. Full text in [LICENSE](LICENSE).

---

<p align="center"><sub>Part of <b>Buildtober 2026</b>: 31 open source projects in 31 days. Built by <a href="https://kitsunetechnologies.org/work">Kitsune Technologies</a>. More at <a href="https://github.com/KitsuneTech1">github.com/KitsuneTech1</a>.</sub></p>
