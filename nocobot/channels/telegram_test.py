"""Tests for Telegram markdown-to-HTML converter with table support."""

import pytest

from nocobot.channels.telegram import _strip_md, _render_table_box, _markdown_to_telegram_html


class TestStripMd:
    def test_bold(self):
        assert _strip_md("**hello**") == "hello"

    def test_underline(self):
        assert _strip_md("__world__") == "world"

    def test_strikethrough(self):
        assert _strip_md("~~gone~~") == "gone"

    def test_inline_code(self):
        assert _strip_md("`code`") == "code"

    def test_mixed(self):
        assert _strip_md("**bold** and `code`") == "bold and code"

    def test_plain_text(self):
        assert _strip_md("no formatting") == "no formatting"


class TestRenderTableBox:
    def test_basic_table(self):
        lines = [
            "| Name | Age |",
            "|------|-----|",
            "| Alice | 30 |",
            "| Bob   | 25 |",
        ]
        result = _render_table_box(lines)
        out_lines = result.split('\n')
        assert len(out_lines) == 4  # header + separator + 2 data rows
        assert '─' in out_lines[1]  # separator row uses box-drawing
        assert 'Alice' in out_lines[2]
        assert 'Bob' in out_lines[3]

    def test_no_separator_row_passthrough(self):
        lines = [
            "| Name | Age |",
            "| Alice | 30 |",
        ]
        result = _render_table_box(lines)
        assert result == '\n'.join(lines)

    def test_separator_with_colons(self):
        lines = [
            "| Left | Center | Right |",
            "|:-----|:------:|------:|",
            "| a    | b      | c     |",
        ]
        result = _render_table_box(lines)
        assert '─' in result
        assert 'Left' in result

    def test_cjk_characters(self):
        lines = [
            "| Name | 名前 |",
            "|------|------|",
            "| Alice | 太郎 |",
        ]
        result = _render_table_box(lines)
        out_lines = result.split('\n')
        assert len(out_lines) == 3
        # CJK chars take 2 columns, so alignment should account for that
        assert '太郎' in out_lines[2]

    def test_strips_markdown_in_cells(self):
        lines = [
            "| **Name** | `Age` |",
            "|----------|-------|",
            "| ~~old~~ | 30 |",
        ]
        result = _render_table_box(lines)
        assert '**' not in result
        assert '`' not in result
        assert '~~' not in result
        assert 'Name' in result
        assert 'old' in result


class TestMarkdownToTelegramHtmlWithTables:
    def test_table_rendered_as_pre_block(self):
        md = "Here is a table:\n| A | B |\n|---|---|\n| 1 | 2 |\nDone."
        html = _markdown_to_telegram_html(md)
        assert '<pre><code>' in html
        assert '</code></pre>' in html
        assert '─' in html
        assert 'Here is a table:' in html
        assert 'Done.' in html

    def test_table_without_separator_not_converted(self):
        md = "| A | B |\n| 1 | 2 |"
        html = _markdown_to_telegram_html(md)
        assert '<pre><code>' not in html

    def test_table_coexists_with_code_blocks(self):
        md = "```\ncode here\n```\n| X | Y |\n|---|---|\n| a | b |"
        html = _markdown_to_telegram_html(md)
        assert html.count('<pre><code>') == 2  # one for code block, one for table
        assert 'code here' in html
        assert '─' in html

    def test_existing_markdown_features_still_work(self):
        md = "**bold** and _italic_ and `code`"
        html = _markdown_to_telegram_html(md)
        assert '<b>bold</b>' in html
        assert '<i>italic</i>' in html
        assert '<code>code</code>' in html
