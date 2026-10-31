#!/usr/bin/env python3
"""Tests for code-quality-scorer."""

import unittest
import tempfile
from pathlib import Path
import score_repo


class TestScoreRepo(unittest.TestCase):
    """Test score_repo functionality."""

    def setUp(self):
        """Create a sample repository structure."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = Path(self.temp_dir)

        # Create README
        (self.repo_path / 'README.md').write_text('# Test Repo\n\nA test repository.')

        # Create source files
        (self.repo_path / 'main.py').write_text('def hello():\n    """Say hello."""\n    print("Hello")\n' * 10)
        (self.repo_path / 'utils.py').write_text('def add(a, b):\n    """Add two numbers."""\n    return a + b\n' * 5)

        # Create test files
        (self.repo_path / 'test_main.py').write_text('def test_hello():\n    assert True\n')

        # Create docs
        (self.repo_path / 'docs').mkdir()
        (self.repo_path / 'docs' / 'guide.md').write_text('# Guide\n\nThis is a guide.')

        # Create dependency files
        (self.repo_path / 'requirements.txt').write_text('requests==2.28.0\n')

    def test_count_files_by_type(self):
        """Test counting files by extension."""
        counts = score_repo.count_files_by_type(self.repo_path)
        self.assertGreater(counts['.py'], 0)
        self.assertGreater(counts['.md'], 0)

    def test_score_tests_with_files(self):
        """Test scoring when test files exist."""
        score, detail = score_repo.score_tests(self.repo_path)
        self.assertGreater(score, 0)
        self.assertIn('test file', detail)

    def test_score_documentation_with_readme(self):
        """Test scoring when README exists."""
        score, detail = score_repo.score_documentation(self.repo_path)
        self.assertGreater(score, 0)
        self.assertIn('README', detail)

    def test_score_dependencies(self):
        """Test scoring dependencies."""
        score, detail = score_repo.score_dependencies(self.repo_path)
        self.assertGreater(score, 0)
        self.assertIn('requirements.txt', detail)

    def test_score_size(self):
        """Test scoring code size."""
        score, detail = score_repo.score_size(self.repo_path)
        self.assertGreater(score, 0)
        self.assertIn('lines', detail)

    def test_score_repository(self):
        """Test full repository scoring."""
        result = score_repo.score_repository(self.repo_path)

        self.assertIn('total', result)
        self.assertIn('breakdown', result)
        self.assertGreaterEqual(result['total'], 0)
        self.assertLessEqual(result['total'], 100)

        breakdown = result['breakdown']
        self.assertIn('tests', breakdown)
        self.assertIn('documentation', breakdown)
        self.assertIn('dependencies', breakdown)
        self.assertIn('size', breakdown)

        for category in breakdown.values():
            self.assertIn('score', category)
            self.assertIn('max', category)
            self.assertIn('detail', category)

    def test_score_repository_minimal(self):
        """Test scoring a minimal repository."""
        minimal_dir = Path(tempfile.mkdtemp())
        (minimal_dir / 'main.py').write_text('print("hello")')

        result = score_repo.score_repository(minimal_dir)
        self.assertGreaterEqual(result['total'], 0)
        self.assertLessEqual(result['total'], 100)


if __name__ == '__main__':
    unittest.main()
