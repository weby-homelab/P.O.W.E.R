"""Tests for markdown quality checks."""

from __future__ import annotations

from power_framework.core.markdown_checks import (
    check_all,
    check_code_block_language,
    check_header_jumps,
    check_list_markers,
    check_trailing_whitespace,
    fix_all,
    fix_list_markers,
    fix_trailing_whitespace,
)


class TestTrailingWhitespace:
    def test_detects_trailing_whitespace(self):
        content = "line one  \nline two\nline three "
        issues = check_trailing_whitespace(content)
        assert len(issues) == 2
        assert all(i["type"] == "trailing-whitespace" for i in issues)

    def test_clean_content(self):
        content = "line one\nline two\nline three"
        assert check_trailing_whitespace(content) == []

    def test_fix_removes_whitespace(self):
        content = "line one  \nline two  \nline three"
        fixed = fix_trailing_whitespace(content)
        assert "  \n" not in fixed


class TestListMarkers:
    def test_detects_inconsistent_markers(self):
        content = "- item one\n- item two\n* item three"
        issues = check_list_markers(content)
        assert len(issues) >= 1

    def test_consistent_markers_no_issue(self):
        content = "- item one\n- item two\n- item three"
        assert check_list_markers(content) == []

    def test_fix_standardizes_to_dash(self):
        content = "- item one\n* item two\n- item three"
        fixed = fix_list_markers(content, preferred="-")
        assert "* item two" not in fixed
        assert "- item two" in fixed

    def test_skips_code_blocks(self):
        content = "- item\n```\n* not a list\n```\n- another"
        fixed = fix_list_markers(content, preferred="-")
        assert "* not a list" in fixed  # inside code block, unchanged


class TestHeaderJumps:
    def test_detects_jump(self):
        content = "# H1\n\n### H3"
        issues = check_header_jumps(content)
        assert len(issues) == 1
        assert "header-jump" in issues[0]["type"]

    def test_no_jump(self):
        content = "# H1\n\n## H2\n\n### H3"
        assert check_header_jumps(content) == []

    def test_multiple_jumps(self):
        content = "# H1\n\n#### H4\n\n###### H6"
        issues = check_header_jumps(content)
        assert len(issues) == 2


class TestCodeBlockLanguage:
    def test_detects_missing_language(self):
        content = "```\ncode without language\n```"
        issues = check_code_block_language(content)
        assert len(issues) == 1

    def test_with_language(self):
        content = "```python\nprint('hello')\n```"
        assert check_code_block_language(content) == []

    def test_multiple_blocks(self):
        content = "```\nno lang\n```\n\n```bash\nwith lang\n```"
        issues = check_code_block_language(content)
        assert len(issues) == 1


class TestCheckAll:
    def test_finds_all_issues(self):
        content = "# H1  \n\n### H3\n\n```\nno lang\n```\n* item\n- item"
        issues = check_all(content)
        types = {i["type"] for i in issues}
        assert len(types) >= 3  # trailing-whitespace, header-jump, missing-code-language, etc.

    def test_no_issues(self):
        content = "# H1\n\n## H2\n\nSome text\n\n```python\ncode\n```"
        assert check_all(content) == []


class TestFixAll:
    def test_fixes_whitespace_and_list_markers(self):
        content = "# H1  \n\nSome text\n* item one\n- item two"
        fixed, changes = fix_all(content)
        assert len(changes) >= 1
        assert "  \n" not in fixed

    def test_no_changes_needed(self):
        content = "# Clean\n\nNo issues here."
        fixed, changes = fix_all(content)
        assert changes == []
        assert fixed == content
