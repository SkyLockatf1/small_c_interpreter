"""
test_repl_main.py - 測試 main.py 工具函式
涵蓋 parse_line_args 與 check_input_complete。
"""
import runpy

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


class TestRunCommand:
    """測試 RUN 指令是否能在 REPL 中從 main() 執行程式緩衝區。"""

    def run_repl(self, monkeypatch, capsys, commands):
        inputs = iter(commands)
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
        runpy.run_path("main.py", run_name="__main__")
        return capsys.readouterr().out

    def test_run_empty_buffer_reports_error(self, monkeypatch, capsys):
        out = self.run_repl(monkeypatch, capsys, ["RUN", "QUIT"])

        assert "Error: no program to run." in out

    def test_run_basic_main_prints_and_returns_zero(self, monkeypatch, capsys):
        out = self.run_repl(monkeypatch, capsys, [
            "int main() {",
            'printf("hello\\n");',
            "return 0;",
            "}",
            "RUN",
            "QUIT",
            "y",
        ])

        assert "hello" in out
        assert "Program exited with return value 0." in out

    def test_run_uses_main_return_value(self, monkeypatch, capsys):
        out = self.run_repl(monkeypatch, capsys, [
            "int main() {",
            "return 7;",
            "}",
            "RUN",
            "QUIT",
            "y",
        ])

        assert "Program exited with return value 7." in out

    def test_run_without_main_reports_error(self, monkeypatch, capsys):
        out = self.run_repl(monkeypatch, capsys, [
            "int add(int a, int b) {",
            "return a + b;",
            "}",
            "RUN",
            "QUIT",
            "y",
        ])

        assert "Error: main function not found." in out

    def test_run_without_main_does_not_execute_top_level_statement(self, monkeypatch, capsys):
        out = self.run_repl(monkeypatch, capsys, [
            "APPEND",
            'printf("should not run\\n");',
            ".",
            "RUN",
            "QUIT",
            "y",
        ])

        assert "Error: main function not found." in out
        assert "should not run" not in out

    def test_run_with_main_skips_top_level_statement(self, monkeypatch, capsys):
        out = self.run_repl(monkeypatch, capsys, [
            "APPEND",
            'printf("top level should not run\\n");',
            "int main() {",
            'printf("main only\\n");',
            "return 0;",
            "}",
            ".",
            "RUN",
            "QUIT",
            "y",
        ])

        assert "top level should not run" not in out
        assert "main only" in out
        assert "Program exited with return value 0." in out

    def test_run_twice_uses_fresh_runtime_each_time(self, monkeypatch, capsys):
        out = self.run_repl(monkeypatch, capsys, [
            "int counter = 0;",
            "int main() {",
            "counter = counter + 1;",
            'printf("counter=%d\\n", counter);',
            "return counter;",
            "}",
            "RUN",
            "RUN",
            "QUIT",
            "y",
        ])

        assert out.count("counter=1") == 2
        assert out.count("Program exited with return value 1.") == 2

    def test_run_void_main_uses_zero_exit_code(self, monkeypatch, capsys):
        out = self.run_repl(monkeypatch, capsys, [
            "void main() {",
            'printf("ok\\n");',
            "}",
            "RUN",
            "QUIT",
            "y",
        ])

        assert "ok" in out
        assert "Program exited with return value 0." in out

    def test_run_runtime_error_returns_to_repl_without_traceback(self, monkeypatch, capsys):
        out = self.run_repl(monkeypatch, capsys, [
            "int main() {",
            'printf("%d\\n", 10 / 0);',
            "return 0;",
            "}",
            "RUN",
            "QUIT",
            "y",
        ])

        assert "Runtime error" in out
        assert "zero" in out.lower()
        assert "Traceback" not in out

    def test_trace_on_prints_main_statements_before_run_execution(self, monkeypatch, capsys):
        out = self.run_repl(monkeypatch, capsys, [
            "int main() {",
            "int result;",
            "result = 3 + 4;",
            'printf("result=%d\\n", result);',
            "return result;",
            "}",
            "TRACE ON",
            "RUN",
            "QUIT",
            "y",
        ])

        assert "Trace mode enabled." in out
        assert "[line 2] int result;" in out
        assert "[line 3] result = 3 + 4;" in out
        assert "[line 4] printf(\"result=%d\\n\", result);" in out
        assert "result=7" in out
        assert "Program exited with return value 7." in out

    def test_trace_on_prints_user_function_statements(self, monkeypatch, capsys):
        out = self.run_repl(monkeypatch, capsys, [
            "int gcd(int a, int b) {",
            "int temp;",
            "while (b != 0) {",
            "temp = b;",
            "b = a % b;",
            "a = temp;",
            "}",
            "return a;",
            "}",
            "int main() {",
            "int result;",
            "result = gcd(48, 18);",
            'printf("GCD=%d\\n", result);',
            "return 0;",
            "}",
            "TRACE ON",
            "RUN",
            "QUIT",
            "y",
        ])

        assert "[line 11] int result;" in out
        assert "[line 12] result = gcd(48, 18);" in out
        assert "[line 2] int temp;" in out
        assert "[line 4] temp = b;" in out
        assert "GCD=6" in out

    def test_trace_off_stops_printing_trace_lines(self, monkeypatch, capsys):
        out = self.run_repl(monkeypatch, capsys, [
            "int main() {",
            'printf("ok\\n");',
            "return 0;",
            "}",
            "TRACE ON",
            "TRACE OFF",
            "RUN",
            "QUIT",
            "y",
        ])

        assert "Trace mode enabled." in out
        assert "Trace mode disabled." in out
        assert "[line 2]" not in out
        assert "ok" in out


class TestCheckCommand:
    """測試 CHECK 指令只分析程式緩衝區，不執行 main()。"""

    def run_repl(self, monkeypatch, capsys, commands):
        inputs = iter(commands)
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
        runpy.run_path("main.py", run_name="__main__")
        return capsys.readouterr().out

    def test_check_empty_buffer_reports_error(self, monkeypatch, capsys):
        out = self.run_repl(monkeypatch, capsys, ["CHECK", "QUIT"])

        assert "Error: no program to check." in out

    def test_check_valid_program_reports_no_errors(self, monkeypatch, capsys):
        out = self.run_repl(monkeypatch, capsys, [
            "APPEND",
            "int main() {",
            'printf("ok\\n");',
            "return 0;",
            "}",
            ".",
            "CHECK",
            "QUIT",
            'y',
        ])

        assert "No errors found." in out
        assert "ok" not in out

    def test_check_does_not_execute_printf(self, monkeypatch, capsys):
        out = self.run_repl(monkeypatch, capsys, [
            "APPEND",
            "int main() {",
            'printf("this should not print\\n");',
            "return 0;",
            "}",
            ".",
            "CHECK",
            "QUIT",
            "y",
        ])

        assert "No errors found." in out
        assert "this should not print" not in out

    def test_check_syntax_error_reports_error_without_traceback(self, monkeypatch, capsys):
        out = self.run_repl(monkeypatch, capsys, [
            "APPEND",
            "int main() {",
            "int bad = ;",
            "return 0;",
            "}",
            ".",
            "CHECK",
            "QUIT",
            "y",
        ])

        assert "Syntax error" in out
        assert "line 2" in out
        assert "Traceback" not in out

    def test_check_does_not_change_existing_runtime_state(self, monkeypatch, capsys):
        out = self.run_repl(monkeypatch, capsys, [
            "int x = 1;",
            "APPEND",
            "int main() {",
            "x = 99;",
            "return 0;",
            "}",
            ".",
            "CHECK",
            "VARS",
            "QUIT",
            'y',
        ])

        assert "No errors found." in out
        assert "int x = 1" in out
        assert "int x = 99" not in out


class TestReplVarsScenario:
    """REPL-level tests for debugger/status commands."""

    def test_vars_lists_array_scenario_09_state(self, monkeypatch, capsys):
        inputs = iter([
            "NEW",
            "int arr[10];",
            "int i;",
            "for (i = 0; i < 10; i = i + 1) {",
            "arr[i] = (i + 1) * 10;",
            "}",
            "for (i = 0; i < 10; i = i + 1) {",
            'printf("arr[%d] = %d\\n", i, arr[i]);',
            "}",
            "VARS",
            "QUIT",
            "y",
        ])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

        runpy.run_path("main.py", run_name="__main__")
        out = capsys.readouterr().out

        expected_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for index, value in enumerate(expected_values):
            assert f"arr[{index}] = {value}" in out

        assert "int arr[10] = {10, 20, 30, 40, 50, 60, 70, 80, 90, 100}" in out
        assert "int i = 10" in out


class TestReplFuncsScenario:
    """REPL-level tests for FUNCS command output."""

    def test_funcs_lists_hard_coded_builtins(self, monkeypatch, capsys):
        inputs = iter(["FUNCS", "QUIT"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

        runpy.run_path("main.py", run_name="__main__")
        out = capsys.readouterr().out

        expected_lines = [
            "--- built-in functions ---",
            "int putchar(int ch) [built-in]",
            "int getchar() [built-in]",
            "void printf(char *fmt, ...) [built-in]",
            "void puts(char *s) [built-in]",
            "int scanf(char *fmt, ...) [built-in]",
            "int strlen(char *s) [built-in]",
            "void strcpy(char *dest, char *src) [built-in]",
            "int strcmp(char *s1, char *s2) [built-in]",
            "void strcat(char *dest, char *src) [built-in]",
            "int abs(int x) [built-in]",
            "int max(int a, int b) [built-in]",
            "int min(int a, int b) [built-in]",
            "int pow(int base, int exp) [built-in]",
            "int sqrt(int x) [built-in]",
            "int mod(int a, int b) [built-in]",
            "int rand() [built-in]",
            "void srand(int seed) [built-in]",
            "void memset(char *ptr, int val, int n) [built-in]",
            "int sizeof_int() [built-in]",
            "int sizeof_char() [built-in]",
            "int atoi(char *s) [built-in]",
            "void itoa(int val, char *str) [built-in]",
            "void exit(int code) [built-in]",
        ]
        for line in expected_lines:
            assert line in out

    def test_funcs_lists_user_function_with_line_number(self, monkeypatch, capsys):
        inputs = iter([
            "int add(int a, int b) {",
            "return a + b;",
            "}",
            "FUNCS",
            "QUIT",
            "y",
        ])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

        runpy.run_path("main.py", run_name="__main__")
        out = capsys.readouterr().out

        assert "int add(int a, int b) line 1" in out
        assert "--- built-in functions ---" in out
