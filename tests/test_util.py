"""Unit tests for escape_markup utility."""

from gridnight_commander.util import escape_markup


class TestEscapeMarkup:
    def test_no_brackets(self):
        assert escape_markup("hello world") == "hello world"

    def test_empty_string(self):
        assert escape_markup("") == ""

    def test_left_bracket(self):
        assert escape_markup("[") == r"\["

    def test_right_bracket(self):
        assert escape_markup("]") == r"\]"

    def test_both_brackets(self):
        assert escape_markup("[bold]") == r"\[bold\]"

    def test_brackets_at_start_and_end(self):
        assert escape_markup("[text]") == r"\[text\]"

    def test_consecutive_left_brackets(self):
        assert escape_markup("[[") == r"\[\["

    def test_consecutive_right_brackets(self):
        assert escape_markup("]]") == r"\]\]"

    def test_nested_brackets(self):
        assert escape_markup("[[nested]]") == r"\[\[nested\]\]"

    def test_brackets_mid_string(self):
        assert escape_markup("Error: [Errno 2] No such file") == r"Error: \[Errno 2\] No such file"

    def test_only_right_bracket(self):
        assert escape_markup("foo]bar") == r"foo\]bar"

    def test_multiple_separate_groups(self):
        assert escape_markup("[a] and [b]") == r"\[a\] and \[b\]"

    def test_unicode_with_brackets(self):
        assert escape_markup("文件 [名]") == r"文件 \[名\]"

    def test_digits_in_brackets(self):
        assert escape_markup("[42]") == r"\[42\]"

    def test_backslash_not_modified(self):
        # Backslashes are left untouched; only the brackets are escaped
        result = escape_markup("a\\b")
        assert result == "a\\b"
