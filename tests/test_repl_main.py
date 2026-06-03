"""
test_repl_main.py - 測試 main.py 工具函式
涵蓋 parse_line_args 與 check_input_complete。
"""
import pytest
import main


class TestParseLineArgs:
    """測試 main.parse_line_args 在各種參數格式與 allow 旗標下的行為。"""

    def test_empty_allowed_returns_empty_list(self):
        result = main.parse_line_args("", "LIST", allow_empty=True, allow_range=True)
        assert result == []

    def test_empty_not_allowed_raises(self):
        with pytest.raises(Exception) as exc:
            main.parse_line_args("", "DELETE", allow_empty=False, allow_range=True)
        assert "DELETE" in str(exc.value)

    def test_single_number_returns_single_element(self):
        result = main.parse_line_args("5", "LIST", allow_empty=True, allow_range=True)
        assert result == [5]

    def test_single_number_boundary_one(self):
        result = main.parse_line_args("1", "LIST", allow_empty=True, allow_range=True)
        assert result == [1]

    def test_large_number_accepted(self):
        result = main.parse_line_args("9999", "LIST", allow_empty=True, allow_range=True)
        assert result == [9999]

    def test_range_returns_two_elements(self):
        result = main.parse_line_args("1-3", "LIST", allow_empty=True, allow_range=True)
        assert result == [1, 3]

    def test_range_same_start_and_end(self):
        result = main.parse_line_args("3-3", "LIST", allow_empty=True, allow_range=True)
        assert result == [3, 3]

    def test_range_not_allowed_raises(self):
        with pytest.raises(Exception) as exc:
            main.parse_line_args("1-5", "INSERT", allow_empty=False, allow_range=False)
        assert "INSERT" in str(exc.value)

    def test_comma_format_raises(self):
        with pytest.raises(Exception):
            main.parse_line_args("1,5", "LIST", allow_empty=True, allow_range=True)

    def test_space_separated_format_raises(self):
        with pytest.raises(Exception):
            main.parse_line_args("1 5", "LIST", allow_empty=True, allow_range=True)

    def test_non_numeric_raises(self):
        with pytest.raises(Exception):
            main.parse_line_args("abc", "LIST", allow_empty=True, allow_range=True)

    def test_negative_number_raises(self):
        # RE_SINGLE 只接受正整數，負號不合法
        with pytest.raises(Exception):
            main.parse_line_args("-1", "LIST", allow_empty=True, allow_range=True)

    def test_error_message_mentions_command(self):
        with pytest.raises(Exception) as exc:
            main.parse_line_args("bad", "MYCOMMAND", allow_empty=True, allow_range=True)
        assert "MYCOMMAND" in str(exc.value)

    def test_zero_accepted_as_single(self):
        # parse_line_args 本身不做邊界檢查，0 是合法整數（會由 repl.LIST 等拒絕）
        result = main.parse_line_args("0", "LIST", allow_empty=True, allow_range=True)
        assert result == [0]

    def test_range_start_greater_than_end_still_accepted(self):
        # 反向範圍由 repl.DELETE 拒絕，parse_line_args 只負責格式解析
        result = main.parse_line_args("5-2", "DELETE", allow_empty=False, allow_range=True)
        assert result == [5, 2]

    def test_leading_zero_number_accepted(self):
        # "01" 通過 \d+ 正則，int("01") == 1；EDIT 只接受單一行號
        result = main.parse_line_args("01", "EDIT", allow_empty=False, allow_range=False)
        assert result == [1]

    def test_triple_segment_raises(self):
        # "1-3-5" 不符合 DELETE 的任何合法格式
        with pytest.raises(Exception):
            main.parse_line_args("1-3-5", "DELETE", allow_empty=False, allow_range=True)

    def test_dash_only_raises(self):
        # 單獨破折號對 DELETE 無意義
        with pytest.raises(Exception):
            main.parse_line_args("-", "DELETE", allow_empty=False, allow_range=True)

    def test_range_with_spaces_raises(self):
        # "1 - 3" 有空格，不符合 RE_RANGE；DELETE 應拒絕
        with pytest.raises(Exception):
            main.parse_line_args("1 - 3", "DELETE", allow_empty=False, allow_range=True)

    def test_whitespace_only_raises(self):
        # 純空格不是空字串，也不符合數字格式；INSERT 不允許空參數
        with pytest.raises(Exception):
            main.parse_line_args("  ", "INSERT", allow_empty=False, allow_range=False)


class TestCheckInputComplete:
    """測試 main.check_input_complete 的括號配對狀態機。"""

    def test_simple_statement_complete(self):
        assert main.check_input_complete("int x = 5;\n") is True

    def test_unclosed_brace_incomplete(self):
        assert main.check_input_complete("if (x) {\n") is False

    def test_closed_brace_complete(self):
        assert main.check_input_complete("{\n    x = 1;\n}\n") is True

    def test_unclosed_paren_incomplete(self):
        assert main.check_input_complete("int a = (5 + (\n") is False

    def test_open_block_comment_incomplete(self):
        assert main.check_input_complete("/* comment\n") is False

    def test_closed_block_comment_complete(self):
        assert main.check_input_complete("/* comment */ int x;\n") is True

    def test_line_comment_braces_ignored(self):
        # // 後的 { 不計入括號配對
        assert main.check_input_complete("// {\nint x;\n") is True

    def test_string_literal_braces_ignored(self):
        assert main.check_input_complete('int s = "{";\n') is True

    def test_char_literal_brace_ignored(self):
        assert main.check_input_complete("char c = '{';\n") is True

    def test_mismatched_close_brace_treated_as_complete(self):
        # 多餘的右括號不代表「需要更多輸入」，讓 parser 報錯即可
        assert main.check_input_complete("}\n") is True

    def test_nested_braces_incomplete(self):
        assert main.check_input_complete("void f() {\n    if (x) {\n") is False

    def test_nested_braces_complete(self):
        assert main.check_input_complete("void f() {\n    if (x) {\n    }\n}\n") is True

    def test_square_bracket_incomplete(self):
        assert main.check_input_complete("int a[\n") is False

    def test_empty_string_complete(self):
        assert main.check_input_complete("") is True
