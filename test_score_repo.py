#!/usr/bin/env python3
"""Tests for code-quality-scorer."""

import os
import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

import score_repo


class TestScoreRepo(unittest.TestCase):
    """Test score_repo functionality."""

    def setUp(self):
        self.repo_path = Path(__file__).parent / "test-fixture"
        if self.repo_path.exists():
            shutil.rmtree(self.repo_path)
        self.repo_path.mkdir()

        (self.repo_path / "README.md").write_text("# Test Repo\n\nA test repository.")
        (self.repo_path / "main.py").write_text(
            '"""Main module."""\n\n'
            'def hello():\n    """Say hello."""\n    print("Hello")\n'
        )
        (self.repo_path / "utils.py").write_text(
            'def add(a, b):\n    """Add two numbers."""\n    return a + b\n'
        )
        (self.repo_path / "test_main.py").write_text(
            "def test_hello():\n    assert True\n"
        )
        (self.repo_path / "docs").mkdir()
        (self.repo_path / "docs" / "guide.md").write_text("# Guide\n\nThis is a guide.")
        (self.repo_path / "requirements.txt").write_text("requests==2.28.0\n")

    def tearDown(self):
        if self.repo_path.exists():
            shutil.rmtree(self.repo_path)

    def test_count_files_by_type(self):
        counts = score_repo.count_files_by_type(self.repo_path)
        self.assertEqual(counts[".py"], 3)
        self.assertEqual(counts[".md"], 2)

    def test_hidden_and_generated_files_are_ignored(self):
        (self.repo_path / ".env").write_text("SECRET=not-a-metric\n")
        (self.repo_path / ".hidden.py").write_text("x\n" * 1000)
        (self.repo_path / ".git").mkdir()
        (self.repo_path / ".git" / "ignored.py").write_text("x\n" * 1000)
        (self.repo_path / "Node_Modules").mkdir()
        (self.repo_path / "Node_Modules" / "ignored.js").write_text("x\n" * 1000)
        (self.repo_path / "Build").mkdir()
        (self.repo_path / "Build" / "ignored.py").write_text("x\n" * 1000)

        counts = score_repo.count_files_by_type(self.repo_path)
        self.assertNotIn(".env", counts)
        self.assertEqual(counts[".py"], 3)
        self.assertEqual(score_repo.score_size(self.repo_path)[0], 25)

    def test_root_symlinks_are_ignored(self):
        (self.repo_path / "README.md").unlink()
        (self.repo_path / "requirements.txt").unlink()
        (self.repo_path / "README-target").write_text("# Target\n")
        (self.repo_path / "requirements-target").write_text("requests==2.28.0\n")
        try:
            os.symlink("README-target", self.repo_path / "README.md")
            os.symlink("requirements-target", self.repo_path / "requirements.txt")
        except (NotImplementedError, OSError) as error:
            self.skipTest(f"symlinks unavailable: {error}")

        documentation_score, documentation_detail = score_repo.score_documentation(self.repo_path)
        dependency_score, dependency_detail = score_repo.score_dependencies(self.repo_path)
        self.assertNotIn("README.md", documentation_detail)
        self.assertEqual(documentation_score, 5)
        self.assertEqual((dependency_score, dependency_detail), (0, "no dependency files"))

    def test_score_tests_uses_test_conventions_not_substrings(self):
        (self.repo_path / "contest.py").write_text("print('not a test')\n")
        (self.repo_path / "tests").mkdir()
        (self.repo_path / "tests" / "support.py").write_text("HELPER = True\n")
        (self.repo_path / "feature.test.js").write_text("describe('feature', () => {})\n")

        score, detail = score_repo.score_tests(self.repo_path)
        self.assertEqual(score, 18)
        self.assertEqual(detail, "3 test files")

    def test_score_tests_with_no_files(self):
        for path in self.repo_path.glob("test_*"):
            path.unlink()
        score, detail = score_repo.score_tests(self.repo_path)
        self.assertEqual((score, detail), (0, "No test files found"))

    def test_score_documentation_counts_real_docstrings(self):
        (self.repo_path / "quotes.py").write_text(
            "text = '''not a docstring'''\n"
            "def documented():\n    '''A real docstring.'''\n    return 1\n"
        )
        score, detail = score_repo.score_documentation(self.repo_path)
        self.assertEqual(score, 16)
        self.assertIn("docstrings (4 found)", detail)

    def test_docs_directory_file_receives_points(self):
        score, detail = score_repo.score_documentation(self.repo_path)
        self.assertIn("docs/ (1 files)", detail)
        self.assertGreater(score, 10)

    def test_invalid_python_does_not_break_documentation_score(self):
        (self.repo_path / "broken.py").write_text("def broken(:\n")
        score, detail = score_repo.score_documentation(self.repo_path)
        self.assertGreater(score, 0)
        self.assertNotIn("broken", detail)

    def test_score_dependencies_requires_manifest_for_lock_bonus(self):
        (self.repo_path / "poetry.lock").write_text("# lock\n")
        (self.repo_path / "requirements.txt").unlink()
        score, detail = score_repo.score_dependencies(self.repo_path)
        self.assertEqual((score, detail), (0, "no dependency files"))

        (self.repo_path / "pyproject.toml").write_text("[project]\nname='demo'\n")
        score, detail = score_repo.score_dependencies(self.repo_path)
        self.assertEqual(score, 13)
        self.assertIn("pyproject.toml", detail)
        self.assertIn("poetry.lock", detail)

    def test_score_dependencies_requires_node_manifest_for_lock_bonus(self):
        (self.repo_path / "package-lock.json").write_text("{}\n")
        score, detail = score_repo.score_dependencies(self.repo_path)
        self.assertEqual((score, detail), (5, "requirements.txt"))

        (self.repo_path / "package.json").write_text("{}\n")
        score, detail = score_repo.score_dependencies(self.repo_path)
        self.assertEqual(score, 15)
        self.assertEqual(detail, "requirements.txt, package.json, lock file")

    def test_score_size_is_case_insensitive_and_reports_files(self):
        (self.repo_path / "EXTRA.JS").write_text("console.log('x')\n")
        score, detail = score_repo.score_size(self.repo_path)
        self.assertEqual(score, 25)
        self.assertIn("4 files", detail)

    def test_score_repository_is_deterministic_and_bounded(self):
        first = score_repo.score_repository(self.repo_path)
        second = score_repo.score_repository(self.repo_path)
        self.assertEqual(first, second)
        self.assertGreaterEqual(first["total"], 0)
        self.assertLessEqual(first["total"], 100)
        self.assertEqual(sum(item["score"] for item in first["breakdown"].values()), first["total"])
        for category in first["breakdown"].values():
            self.assertEqual(category["max"], 25)
            self.assertIn("detail", category)

    def test_score_repository_rejects_non_directory(self):
        with self.assertRaises(ValueError):
            score_repo.score_repository(self.repo_path / "missing")

    def test_cli_returns_json_for_repository(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).parent / "score_repo.py"),
                str(self.repo_path),
                "--format",
                "json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads(completed.stdout)
        self.assertEqual(result["total"], 55)
        self.assertEqual(result["breakdown"]["tests"]["detail"], "1 test file")


if __name__ == "__main__":
    unittest.main()
