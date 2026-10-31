# code-quality-scorer

Score a code repository on tests, documentation, dependencies, and size with a deterministic weighted ranking you can audit.

## What it does

Examines a repository and scores it on four dimensions:

- Tests: 0-25 points based on test file count and presence
- Documentation: 0-25 points for README, docs/, and docstrings
- Dependencies: 0-25 points for dependency declaration and lock files
- Size: 0-25 points, favoring small focused projects over large monoliths

Total score ranges from 0-100. No machine learning, no hidden heuristics, just auditable metrics.

## Installation

```bash
pip install -e .
```

Or run directly:

```bash
python score_repo.py <repo_path> [options]
```

## Usage

### Basic usage

Score a repository:

```bash
python score_repo.py /path/to/repo
```

Output:

```
Repository Quality Score: 78/100

Tests           23/25  15 test files
Documentation   18/25  README.md, docs/ (4 files), docstrings (12 found)
Dependencies    20/25  pyproject.toml, poetry.lock
Size            17/25  2341 lines (12 files)

Interpretation:
  Good: solid foundation with room for improvement.
```

### Output formats

Text (default):

```bash
python score_repo.py /path/to/repo --format text
```

JSON:

```bash
python score_repo.py /path/to/repo --format json
```

JSON output:

```json
{
  "total": 78,
  "breakdown": {
    "tests": {
      "score": 23,
      "max": 25,
      "detail": "15 test files"
    },
    "documentation": {
      "score": 18,
      "max": 25,
      "detail": "README.md, docs/"
    },
    "dependencies": {
      "score": 20,
      "max": 25,
      "detail": "pyproject.toml, poetry.lock"
    },
    "size": {
      "score": 17,
      "max": 25,
      "detail": "2341 lines (12 files)"
    }
  }
}
```

## Scoring interpretation

- 90-100: Excellent. Well-tested, documented, and focused.
- 75-89: Good. Solid foundation with room for improvement.
- 60-74: Fair. Basic quality practices in place.
- 40-59: Needs work. Consider improving test coverage and docs.
- Below 40: Early stage. Focus on adding tests and documentation.

## Metrics details

### Tests (0-25)

- 0 files: 0 points
- 1-2 files: 10 points
- 3-9 files: 18 points
- 10+ files: 25 points

### Documentation (0-25)

- README.md: 10 points
- Alternative README format: 7 points
- docs/ directory: up to 10 points based on file count
- Docstrings: up to 5 points based on count

### Dependencies (0-25)

Awarded for presence of:
- pyproject.toml (8) or requirements.txt (5) or setup.py (3)
- poetry.lock (5)
- package.json (5) or package-lock.json/yarn.lock (5)
- Cargo.toml (8) or Cargo.lock (5)

### Size (0-25)

- < 500 lines: 25 points (tight focus)
- 500-2000 lines: 20 points
- 2000-5000 lines: 15 points
- 5000-10000 lines: 10 points
- 10000+ lines: 5 points

## Testing

```bash
python -m unittest test_score_repo
```

## License

MIT License

Copyright (c) 2026 KitsuneTech1
