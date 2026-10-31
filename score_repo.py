#!/usr/bin/env python3
"""Score a code repository on tests, documentation, dependencies, and size."""

import ast
import json
from argparse import ArgumentParser
from pathlib import Path


CATEGORY_MAX = 25
SOURCE_SUFFIXES = {".py", ".js", ".rs", ".go", ".java", ".cs"}
IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "site-packages",
    ".venv",
    "venv",
}
TEST_DIRECTORY_NAMES = {"test", "tests", "spec", "specs"}


def _is_ignored(path, repo_path):
    """Return whether a repository-relative path should be left out of metrics."""
    relative = path.relative_to(repo_path)
    return any(
        part.startswith(".") or part.lower() in IGNORED_DIRECTORIES
        for part in relative.parts
    )


def _iter_files(repo_path):
    """Yield regular, visible repository files in a stable order."""
    repo_path = Path(repo_path)
    paths = sorted(repo_path.rglob("*"), key=lambda item: (item.as_posix().lower(), item.as_posix()))
    for path in paths:
        if path.is_file() and not path.is_symlink() and not _is_ignored(path, repo_path):
            yield path


def _root_file(repo_path, *names):
    """Find a named file at the repository root, case-insensitively."""
    wanted = {name.lower() for name in names}
    for path in sorted(Path(repo_path).iterdir(), key=lambda item: item.name.lower()):
        if path.is_file() and path.name.lower() in wanted:
            return path
    return None


def count_files_by_type(repo_path):
    """Count visible regular files by extension."""
    counts = {}
    for item in _iter_files(Path(repo_path)):
        extension = item.suffix.lower() or "no_extension"
        counts[extension] = counts.get(extension, 0) + 1
    return counts


def _is_test_file(path, repo_path):
    """Return whether a path follows a common test-file convention."""
    name = path.name.lower()
    stem = path.stem.lower()
    suffix = path.suffix.lower()
    in_test_directory = any(
        part.lower() in TEST_DIRECTORY_NAMES
        for part in path.relative_to(repo_path).parts[:-1]
    )
    named_test = (
        name in {"test.py", "test.rs"}
        or stem.startswith("test_")
        or stem.endswith("_test")
        or stem.endswith(".test")
        or stem.endswith(".spec")
    )
    known_test_suffix = suffix in {".py", ".rs", ".go", ".js", ".ts", ".rb"}
    return known_test_suffix and (in_test_directory or named_test)


def score_tests(repo_path):
    """Score the number of test files found by common naming conventions."""
    repo_path = Path(repo_path)
    test_files = [path for path in _iter_files(repo_path) if _is_test_file(path, repo_path)]

    count = len(test_files)
    if count == 0:
        return 0, "No test files found"
    if count < 3:
        label = "test file" if count == 1 else "test files"
        return 10, f"{count} {label}"
    if count < 10:
        return 18, f"{count} test files"
    return 25, f"{count} test files"


def _count_python_docstrings(repo_path):
    """Count actual module, class, and function docstrings in Python files."""
    count = 0
    for py_file in _iter_files(Path(repo_path)):
        if py_file.suffix.lower() != ".py":
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeError):
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if ast.get_docstring(node, clean=False) is not None:
                    count += 1
    return count


def _count_documentation_files(docs_path):
    """Count visible regular files below a docs directory."""
    if not docs_path.is_dir():
        return 0
    return sum(1 for path in _iter_files(docs_path.parent) if docs_path in path.parents)


def score_documentation(repo_path):
    """Score README files, documentation files, and actual Python docstrings."""
    repo_path = Path(repo_path)
    score = 0
    details = []

    if _root_file(repo_path, "README.md"):
        score += 10
        details.append("README.md")
    elif _root_file(repo_path, "README", "README.txt", "README.rst"):
        score += 7
        details.append("README (non-markdown)")

    docs_path = repo_path / "docs"
    doc_count = _count_documentation_files(docs_path)
    if doc_count:
        score += min(10, doc_count * 2)
        details.append(f"docs/ ({doc_count} files)")

    docstring_count = _count_python_docstrings(repo_path)
    if docstring_count:
        score += min(5, docstring_count)
        details.append(f"docstrings ({docstring_count} found)")

    return min(CATEGORY_MAX, score), ", ".join(details) if details else "minimal documentation"


def _has_root_file(repo_path, *names):
    return _root_file(repo_path, *names) is not None


def score_dependencies(repo_path):
    """Score common dependency manifests and their lock files."""
    repo_path = Path(repo_path)
    score = 0
    details = []

    has_python_manifest = False
    if _has_root_file(repo_path, "pyproject.toml"):
        score += 8
        details.append("pyproject.toml")
        has_python_manifest = True
    elif _has_root_file(repo_path, "requirements.txt"):
        score += 5
        details.append("requirements.txt")
        has_python_manifest = True
    elif _has_root_file(repo_path, "setup.py"):
        score += 3
        details.append("setup.py")
        has_python_manifest = True

    if has_python_manifest and _has_root_file(repo_path, "poetry.lock"):
        score += 5
        details.append("poetry.lock")

    has_node_manifest = _has_root_file(repo_path, "package.json")
    if has_node_manifest:
        score += 5
        details.append("package.json")
        if _has_root_file(repo_path, "package-lock.json", "yarn.lock"):
            score += 5
            details.append("lock file")

    has_rust_manifest = _has_root_file(repo_path, "Cargo.toml")
    if has_rust_manifest:
        score += 8
        details.append("Cargo.toml")
        if _has_root_file(repo_path, "Cargo.lock"):
            score += 5
            details.append("Cargo.lock")

    return min(CATEGORY_MAX, score), ", ".join(details) if details else "no dependency files"


def score_size(repo_path):
    """Score source size, counting supported source files and their lines."""
    source_files = 0
    total_lines = 0

    for item in _iter_files(Path(repo_path)):
        if item.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        source_files += 1
        try:
            total_lines += len(item.read_text(encoding="utf-8", errors="ignore").splitlines())
        except OSError:
            continue

    if source_files == 0:
        return 0, "no source code"
    if total_lines < 500:
        score = 25
    elif total_lines < 2000:
        score = 20
    elif total_lines < 5000:
        score = 15
    elif total_lines < 10000:
        score = 10
    else:
        score = 5
    return score, f"{total_lines} lines ({source_files} files)"


def score_repository(repo_path):
    """Score a repository and return an auditable 0-100 breakdown."""
    repo_path = Path(repo_path)
    if not repo_path.is_dir():
        raise ValueError(f"{repo_path} is not a directory")

    tests_score, tests_detail = score_tests(repo_path)
    docs_score, docs_detail = score_documentation(repo_path)
    deps_score, deps_detail = score_dependencies(repo_path)
    size_score, size_detail = score_size(repo_path)

    return {
        "total": tests_score + docs_score + deps_score + size_score,
        "breakdown": {
            "tests": {"score": tests_score, "max": CATEGORY_MAX, "detail": tests_detail},
            "documentation": {"score": docs_score, "max": CATEGORY_MAX, "detail": docs_detail},
            "dependencies": {"score": deps_score, "max": CATEGORY_MAX, "detail": deps_detail},
            "size": {"score": size_score, "max": CATEGORY_MAX, "detail": size_detail},
        },
    }


def _print_text_result(result):
    print(f"Repository Quality Score: {result['total']}/100")
    print()
    for category, data in result["breakdown"].items():
        print(f"{category.capitalize():15} {data['score']:2}/{data['max']}  {data['detail']}")
    print()
    print("Interpretation:")
    score = result["total"]
    if score >= 90:
        message = "Excellent: well-tested, documented, and focused."
    elif score >= 75:
        message = "Good: solid foundation with room for improvement."
    elif score >= 60:
        message = "Fair: basic quality practices in place."
    elif score >= 40:
        message = "Needs work: consider improving test coverage and docs."
    else:
        message = "Early stage: focus on adding tests and documentation."
    print(f"  {message}")


def main():
    parser = ArgumentParser(description="Score a code repository on quality metrics.")
    parser.add_argument("repo_path", help="Path to the repository")
    parser.add_argument("--format", choices=["json", "text"], default="text",
                        help="Output format (default: text)")
    args = parser.parse_args()

    try:
        result = score_repository(args.repo_path)
    except ValueError as error:
        parser.error(str(error))

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        _print_text_result(result)


if __name__ == "__main__":
    main()
