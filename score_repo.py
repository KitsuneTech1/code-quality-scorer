#!/usr/bin/env python3
"""Score a code repository on test coverage, documentation, dependencies, and size."""

import json
import sys
from pathlib import Path
from argparse import ArgumentParser
from collections import defaultdict


def count_files_by_type(repo_path):
    """Count files by extension in the repository."""
    counts = defaultdict(int)
    for item in Path(repo_path).rglob('*'):
        if item.is_file() and not any(p.name.startswith('.') for p in item.parents):
            ext = item.suffix.lower() or 'no_extension'
            counts[ext] += 1
    return dict(counts)


def score_tests(repo_path):
    """Score test coverage: 0-25 points based on test file existence and count."""
    test_files = []
    patterns = ['test_', '_test.py', 'tests/', 'test.rs', '.test.js', '.spec.js']

    for item in Path(repo_path).rglob('*'):
        if item.is_file():
            name = item.name.lower()
            if any(p in name for p in patterns):
                test_files.append(str(item))

    count = len(test_files)
    if count == 0:
        return 0, "No test files found"
    elif count < 3:
        return 10, f"{count} test file(s)"
    elif count < 10:
        return 18, f"{count} test files"
    else:
        return 25, f"{count} test files"


def score_documentation(repo_path):
    """Score documentation: 0-25 points based on README, docs, and docstrings."""
    score = 0
    details = []

    # Check README
    if (Path(repo_path) / 'README.md').exists():
        score += 10
        details.append("README.md")
    elif (Path(repo_path) / 'README').exists() or (Path(repo_path) / 'readme.txt').exists():
        score += 7
        details.append("README (non-markdown)")

    # Check docs directory
    if (Path(repo_path) / 'docs').is_dir():
        doc_count = len(list((Path(repo_path) / 'docs').rglob('*')))
        if doc_count > 0:
            score += min(10, doc_count // 2)
            details.append(f"docs/ ({doc_count} files)")

    # Check for docstrings in source files
    docstring_count = 0
    for py_file in Path(repo_path).rglob('*.py'):
        try:
            with open(py_file, 'r') as f:
                content = f.read()
                docstring_count += content.count('"""') + content.count("'''")
        except:
            pass

    if docstring_count > 0:
        score += min(5, docstring_count // 20)
        details.append(f"docstrings ({docstring_count // 2} found)")

    return min(25, score), ", ".join(details) if details else "minimal documentation"


def score_dependencies(repo_path):
    """Score dependency hygiene: 0-25 points based on lock files and dependency count."""
    score = 0
    details = []

    # Python
    if (Path(repo_path) / 'pyproject.toml').exists():
        score += 8
        details.append("pyproject.toml")
    elif (Path(repo_path) / 'requirements.txt').exists():
        score += 5
        details.append("requirements.txt")
    elif (Path(repo_path) / 'setup.py').exists():
        score += 3
        details.append("setup.py")

    if (Path(repo_path) / 'poetry.lock').exists():
        score += 5
        details.append("poetry.lock")

    # Node
    if (Path(repo_path) / 'package.json').exists():
        score += 5
        details.append("package.json")

    if (Path(repo_path) / 'package-lock.json').exists() or (Path(repo_path) / 'yarn.lock').exists():
        score += 5
        details.append("lock file")

    # Rust
    if (Path(repo_path) / 'Cargo.toml').exists():
        score += 8
        details.append("Cargo.toml")

    if (Path(repo_path) / 'Cargo.lock').exists():
        score += 5
        details.append("Cargo.lock")

    return min(25, score), ", ".join(details) if details else "no dependency files"


def score_size(repo_path):
    """Score codebase size: 0-25 points. Prefer small, focused projects."""
    source_files = 0
    total_lines = 0

    for item in Path(repo_path).rglob('*'):
        if item.is_file() and item.suffix in ['.py', '.js', '.rs', '.go', '.java', '.cs']:
            source_files += 1
            try:
                with open(item, 'r', encoding='utf-8', errors='ignore') as f:
                    total_lines += len(f.readlines())
            except:
                pass

    # Small and focused: many points. Too large: fewer points.
    if total_lines == 0:
        return 0, "no source code"
    elif total_lines < 500:
        return 25, f"{total_lines} lines ({source_files} files)"
    elif total_lines < 2000:
        return 20, f"{total_lines} lines ({source_files} files)"
    elif total_lines < 5000:
        return 15, f"{total_lines} lines ({source_files} files)"
    elif total_lines < 10000:
        return 10, f"{total_lines} lines ({source_files} files)"
    else:
        return 5, f"{total_lines} lines ({source_files} files)"


def score_repository(repo_path):
    """Score a repository on multiple dimensions. Return score 0-100 and breakdown."""
    repo_path = Path(repo_path)

    if not repo_path.is_dir():
        print(f"Error: {repo_path} is not a directory", file=sys.stderr)
        sys.exit(1)

    tests_score, tests_detail = score_tests(repo_path)
    docs_score, docs_detail = score_documentation(repo_path)
    deps_score, deps_detail = score_dependencies(repo_path)
    size_score, size_detail = score_size(repo_path)

    total = tests_score + docs_score + deps_score + size_score

    return {
        "total": total,
        "breakdown": {
            "tests": {"score": tests_score, "max": 25, "detail": tests_detail},
            "documentation": {"score": docs_score, "max": 25, "detail": docs_detail},
            "dependencies": {"score": deps_score, "max": 25, "detail": deps_detail},
            "size": {"score": size_score, "max": 25, "detail": size_detail},
        }
    }


def main():
    parser = ArgumentParser(description='Score a code repository on quality metrics.')
    parser.add_argument('repo_path', help='Path to the repository')
    parser.add_argument('--format', choices=['json', 'text'], default='text',
                        help='Output format (default: text)')

    args = parser.parse_args()

    result = score_repository(args.repo_path)

    if args.format == 'json':
        print(json.dumps(result, indent=2))
    else:
        print(f"Repository Quality Score: {result['total']}/100")
        print()
        for category, data in result['breakdown'].items():
            print(f"{category.capitalize():15} {data['score']:2}/{data['max']}  {data['detail']}")
        print()
        print("Interpretation:")
        score = result['total']
        if score >= 90:
            print("  Excellent: well-tested, documented, and focused.")
        elif score >= 75:
            print("  Good: solid foundation with room for improvement.")
        elif score >= 60:
            print("  Fair: basic quality practices in place.")
        elif score >= 40:
            print("  Needs work: consider improving test coverage and docs.")
        else:
            print("  Early stage: focus on adding tests and documentation.")


if __name__ == '__main__':
    main()
