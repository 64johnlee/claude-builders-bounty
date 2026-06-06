"""Tests for claude-review CLI."""
import importlib.util
import sys
import os
import json
import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO

# Load module from extensionless file
import importlib.machinery
_path = os.path.join(os.path.dirname(__file__), "claude-review")
_loader = importlib.machinery.SourceFileLoader("claude_review", _path)
_spec = importlib.util.spec_from_loader("claude_review", _loader)
mod = importlib.util.module_from_spec(_spec)
_loader.exec_module(mod)


class TestParsePrUrl(unittest.TestCase):
    def test_valid_url(self):
        owner, repo, num = mod.parse_pr_url("https://github.com/acme/myrepo/pull/42")
        self.assertEqual(owner, "acme")
        self.assertEqual(repo, "myrepo")
        self.assertEqual(num, 42)

    def test_url_with_trailing_slash(self):
        owner, repo, num = mod.parse_pr_url("https://github.com/org/repo/pull/99")
        self.assertEqual(num, 99)

    def test_invalid_url_exits(self):
        with self.assertRaises(SystemExit):
            mod.parse_pr_url("https://gitlab.com/foo/bar/merge_requests/1")

    def test_non_pr_github_url_exits(self):
        with self.assertRaises(SystemExit):
            mod.parse_pr_url("https://github.com/foo/bar/issues/1")


class TestClaudeReview(unittest.TestCase):
    PR_META = {
        "title": "Add feature X",
        "user": {"login": "alice"},
        "base": {"label": "main"},
        "head": {"label": "alice:feature-x"},
        "changed_files": 3,
        "additions": 50,
        "deletions": 10,
        "body": "Adds feature X.",
    }
    DIFF = "diff --git a/foo.py b/foo.py\n+print('hello')\n"

    def test_output_contains_summary_section(self):
        review_text = (
            "## Summary\nThis PR adds feature X.\n\n"
            "## Identified Risks\n- None\n\n"
            "## Improvement Suggestions\n- Add tests\n\n"
            "## Confidence Score\n**High** — Small focused change.\n"
        )
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value.__enter__ = lambda s: BytesIO(
                json.dumps({"content": [{"type": "text", "text": review_text}]}).encode()
            )
            mock_open.return_value.__exit__ = MagicMock(return_value=False)
            result = mod.claude_review(self.PR_META, self.DIFF, "fake-key")

        self.assertIn("## Summary", result)
        self.assertIn("## Identified Risks", result)
        self.assertIn("## Improvement Suggestions", result)
        self.assertIn("## Confidence Score", result)

    def test_output_contains_confidence_keyword(self):
        review_text = (
            "## Summary\nX.\n\n## Identified Risks\n- Y\n\n"
            "## Improvement Suggestions\n- Z\n\n## Confidence Score\n**Medium** — unclear.\n"
        )
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value.__enter__ = lambda s: BytesIO(
                json.dumps({"content": [{"type": "text", "text": review_text}]}).encode()
            )
            mock_open.return_value.__exit__ = MagicMock(return_value=False)
            result = mod.claude_review(self.PR_META, self.DIFF, "fake-key")

        import re
        self.assertRegex(result, r"\*\*(Low|Medium|High)\*\*")


class TestGithubGet(unittest.TestCase):
    def test_returns_parsed_json(self):
        payload = json.dumps({"title": "Test PR"}).encode()
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value.__enter__ = lambda s: BytesIO(payload)
            mock_open.return_value.__exit__ = MagicMock(return_value=False)
            result = mod.github_get("/repos/foo/bar/pulls/1", token=None)
        self.assertEqual(result["title"], "Test PR")


if __name__ == "__main__":
    unittest.main()
