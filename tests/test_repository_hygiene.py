"""Small Git-hygiene checks for files that must stay out of the repository."""

from __future__ import annotations

from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


def is_ignored(path: str) -> bool:
    """Return whether Git ignores a path without creating that path."""
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", path],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


class RepositoryHygieneTests(unittest.TestCase):
    def test_virtual_environment_folder_names_are_ignored(self) -> None:
        """Common local virtual-environment folders must not be commit candidates."""
        self.assertTrue(is_ignored(".venv"))
        self.assertTrue(is_ignored(".venvv"))

    def test_similar_non_environment_name_is_not_broadly_ignored(self) -> None:
        """Ignore rules should be specific rather than hiding unrelated folders."""
        self.assertFalse(is_ignored(".venv_backup"))


if __name__ == "__main__":
    unittest.main()
