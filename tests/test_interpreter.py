"""
test_interpreter.py - 測試 C 語言解譯管線
涵蓋變數、運算子、控制流、函式、陣列、指標、printf、執行期錯誤。
"""
import pytest
from test_helpers import _run_code, _get_int, _get_char, _filter_debug


class TestInterpreterVariables:
    """測試變數宣告、初始化、算術運算、位元運算、複合指定。"""

    def test_int_declaration_default_zero(self, fresh_interp):
        _run_code(fresh_interp, "int x;")
        assert _get_int(fresh_interp, "x") == 0

    def test_int_declaration_with_init(self, fresh_interp):
        _run_code(fresh_interp, "int x = 42;")
        assert _get_int(fresh_interp, "x") == 42

    def test_char_declaration_with_literal(self, fresh_interp):
        _run_code(fresh_interp, "char c = 'A';")
        assert _get_char(fresh_interp, "c") == 65

    def test_hex_literal(self, fresh_interp):
        _run_code(fresh_interp, "int x = 0xFF;")
        assert _get_int(fresh_interp, "x") == 255

    def test_arithmetic_add(self, fresh_interp):
        _run_code(fresh_interp, "int x = 3 + 4;")
        assert _get_int(fresh_interp, "x") == 7

    def test_arithmetic_sub(self, fresh_interp):
        _run_code(fresh_interp, "int x = 10 - 3;")
        assert _get_int(fresh_interp, "x") == 7

    def test_arithmetic_mul(self, fresh_interp):
        _run_code(fresh_interp, "int x = 3 * 4;")
        assert _get_int(fresh_interp, "x") == 12

    def test_arithmetic_div_truncation(self, fresh_interp):
        _run_code(fresh_interp, "int x = 10 / 3;")
        assert _get_int(fresh_interp, "x") == 3

    def test_arithmetic_div_negative_truncates_toward_zero(self, fresh_interp):
        # C 規格：-7 / 2 == -3（向零截斷），不同於 Python 的 -4（向負無窮）
        _run_code(fresh_interp, "int x = -7 / 2;")
        assert _get_int(fresh_interp, "x") == -3

    def test_arithmetic_mod(self, fresh_interp):
        _run_code(fresh_interp, "int x = 10 % 3;")
        assert _get_int(fresh_interp, "x") == 1

    def test_compound_assign_add(self, fresh_interp):
        _run_code(fresh_interp, "int x = 5;\nx += 3;")
        assert _get_int(fresh_interp, "x") == 8

    def test_compound_assign_sub(self, fresh_interp):
        _run_code(fresh_interp, "int x = 5;\nx -= 2;")
        assert _get_int(fresh_interp, "x") == 3

    def test_compound_assign_mul(self, fresh_interp):
        _run_code(fresh_interp, "int x = 5;\nx *= 3;")
        assert _get_int(fresh_interp, "x") == 15

    def test_compound_assign_div(self, fresh_interp):
        _run_code(fresh_interp, "int x = 10;\nx /= 4;")
        assert _get_int(fresh_interp, "x") == 2

    def test_compound_assign_mod(self, fresh_interp):
        _run_code(fresh_interp, "int x = 10;\nx %= 3;")
        assert _get_int(fresh_interp, "x") == 1

    def test_unary_minus(self, fresh_interp):
        _run_code(fresh_interp, "int x = -5;")
        assert _get_int(fresh_interp, "x") == -5

    def test_bitwise_and(self, fresh_interp):
        _run_code(fresh_interp, "int x = 0xF0 & 0x0F;")
        assert _get_int(fresh_interp, "x") == 0

    def test_bitwise_or(self, fresh_interp):
        _run_code(fresh_interp, "int x = 0xF0 | 0x0F;")
        assert _get_int(fresh_interp, "x") == 0xFF

    def test_bitwise_xor(self, fresh_interp):
        _run_code(fresh_interp, "int x = 0xFF ^ 0x0F;")
        assert _get_int(fresh_interp, "x") == 0xF0

    def test_bitwise_left_shift(self, fresh_interp):
        _run_code(fresh_interp, "int x = 1 << 4;")
        assert _get_int(fresh_interp, "x") == 16

    def test_bitwise_right_shift(self, fresh_interp):
        _run_code(fresh_interp, "int x = 32 >> 2;")
        assert _get_int(fresh_interp, "x") == 8


class TestVariableScenario:
    """
    範例 4：驗證跨多行輸入的狀態保留、複合指定，以及 VARS 的資料來源。
    每個 _run_code 對應 REPL 的一次 sc> 輸入，interpreter 實例在各行之間保留狀態。
    """

    def test_multi_var_declaration_and_assign(self, fresh_interp):
        _run_code(fresh_interp, "int x = 10;")
        _run_code(fresh_interp, "int y = 20;")
        _run_code(fresh_interp, "int z;")
        _run_code(fresh_interp, "z = x + y;")
        assert _get_int(fresh_interp, "x") == 10
        assert _get_int(fresh_interp, "y") == 20
        assert _get_int(fresh_interp, "z") == 30

    def test_compound_assignment_updates_existing_vars(self, fresh_interp):
        _run_code(fresh_interp, "int x = 10;")
        _run_code(fresh_interp, "int y = 20;")
        _run_code(fresh_interp, "x += 5;")
        _run_code(fresh_interp, "y -= 3;")
        assert _get_int(fresh_interp, "x") == 15
        assert _get_int(fresh_interp, "y") == 17

    def test_char_variable_ascii_value(self, fresh_interp):
        _run_code(fresh_interp, "char ch = 'A';")
        assert _get_char(fresh_interp, "ch") == 65

    def test_vars_data_source_all_variables_correct(self, fresh_interp):
        _run_code(fresh_interp, "int x = 10;")
        _run_code(fresh_interp, "int y = 20;")
        _run_code(fresh_interp, "int z;")
        _run_code(fresh_interp, "z = x + y;")
        _run_code(fresh_interp, "x += 5;")
        _run_code(fresh_interp, "y -= 3;")
        _run_code(fresh_interp, "char ch = 'A';")

        var_map = {v.name: v for v in fresh_interp.symtable.iter_vars()}
        assert set(var_map.keys()) == {"x", "y", "z", "ch"}
        assert _get_int(fresh_interp, "x") == 15
        assert _get_int(fresh_interp, "y") == 17
        assert _get_int(fresh_interp, "z") == 30
        assert _get_char(fresh_interp, "ch") == 65
        assert var_map["x"].var_type == "int"
        assert var_map["y"].var_type == "int"
        assert var_map["z"].var_type == "int"
        assert var_map["ch"].var_type == "char"


class TestOperatorPrecedence:
    """測試運算子優先順序與括號覆蓋（對應 REPL 實際執行結果）。"""

    def test_mul_before_add(self, fresh_interp):
        _run_code(fresh_interp, "int x = 2 + 3 * 4;")
        assert _get_int(fresh_interp, "x") == 14

    def test_paren_overrides_precedence(self, fresh_interp):
        _run_code(fresh_interp, "int x = (2 + 3) * 4;")
        assert _get_int(fresh_interp, "x") == 20

    def test_integer_division_truncation(self, fresh_interp):
        _run_code(fresh_interp, "int x = 100 / 7;")
        assert _get_int(fresh_interp, "x") == 14

    def test_modulo(self, fresh_interp):
        _run_code(fresh_interp, "int x = 100 % 7;")
        assert _get_int(fresh_interp, "x") == 2

    def test_unary_minus_with_add(self, fresh_interp):
        _run_code(fresh_interp, "int x = -5 + 3;")
        assert _get_int(fresh_interp, "x") == -2

    def test_mixed_precedence(self, fresh_interp):
        # 2 + 3 * 4 - 8 / 2 → 2 + 12 - 4 = 10
        _run_code(fresh_interp, "int x = 2 + 3 * 4 - 8 / 2;")
        assert _get_int(fresh_interp, "x") == 10

    def test_nested_parens(self, fresh_interp):
        # ((2 + 3) * (4 - 1)) / 5 → (5 * 3) / 5 = 3
        _run_code(fresh_interp, "int x = ((2 + 3) * (4 - 1)) / 5;")
        assert _get_int(fresh_interp, "x") == 3


class TestBitwiseOperators:
    """測試位元運算子的正確性（系統程式設計常用）。"""

    def test_bitwise_and(self, fresh_interp):
        _run_code(fresh_interp, "int x = 0xFF & 0x0F;")
        assert _get_int(fresh_interp, "x") == 15

    def test_bitwise_or(self, fresh_interp):
        _run_code(fresh_interp, "int x = 0xA0 | 0x05;")
        assert _get_int(fresh_interp, "x") == 165

    def test_bitwise_xor(self, fresh_interp):
        _run_code(fresh_interp, "int x = 0xFF ^ 0x0F;")
        assert _get_int(fresh_interp, "x") == 240

    def test_bitwise_not_zero(self, fresh_interp):
        _run_code(fresh_interp, "int x = ~0;")
        assert _get_int(fresh_interp, "x") == -1

    def test_left_shift(self, fresh_interp):
        _run_code(fresh_interp, "int x = 1 << 8;")
        assert _get_int(fresh_interp, "x") == 256

    def test_right_shift(self, fresh_interp):
        _run_code(fresh_interp, "int x = 256 >> 4;")
        assert _get_int(fresh_interp, "x") == 16

    def test_combined_and_or(self, fresh_interp):
        # (0xAB & 0xF0) | 0x0C → 0xA0 | 0x0C = 0xAC = 172
        _run_code(fresh_interp, "int x = (0xAB & 0xF0) | 0x0C;")
        assert _get_int(fresh_interp, "x") == 0xAC


class TestRelationalAndLogical:
    """測試關係運算子與邏輯運算子的求值結果（控制結構的運作前提）。"""

    def test_greater_than_true(self, fresh_interp):
        _run_code(fresh_interp, "int x = 5 > 3;")
        assert _get_int(fresh_interp, "x") == 1

    def test_less_than_false(self, fresh_interp):
        _run_code(fresh_interp, "int x = 5 < 3;")
        assert _get_int(fresh_interp, "x") == 0

    def test_equal_true(self, fresh_interp):
        _run_code(fresh_interp, "int x = 5 == 5;")
        assert _get_int(fresh_interp, "x") == 1

    def test_not_equal_false(self, fresh_interp):
        _run_code(fresh_interp, "int x = 5 != 5;")
        assert _get_int(fresh_interp, "x") == 0

    def test_logical_and_both_true(self, fresh_interp):
        _run_code(fresh_interp, "int x = 5 >= 5 && 3 < 4;")
        assert _get_int(fresh_interp, "x") == 1

    def test_logical_or_one_true(self, fresh_interp):
        _run_code(fresh_interp, "int x = 5 > 10 || 3 < 4;")
        assert _get_int(fresh_interp, "x") == 1

    def test_logical_not(self, fresh_interp):
        _run_code(fresh_interp, "int x = !(5 > 3);")
        assert _get_int(fresh_interp, "x") == 0

    def test_less_than_or_equal_true(self, fresh_interp):
        _run_code(fresh_interp, "int x = 3 <= 3;")
        assert _get_int(fresh_interp, "x") == 1

    def test_greater_than_or_equal_false(self, fresh_interp):
        _run_code(fresh_interp, "int x = 2 >= 5;")
        assert _get_int(fresh_interp, "x") == 0

    def test_logical_and_one_false(self, fresh_interp):
        _run_code(fresh_interp, "int x = 1 && 0;")
        assert _get_int(fresh_interp, "x") == 0

    def test_logical_or_both_false(self, fresh_interp):
        _run_code(fresh_interp, "int x = 0 || 0;")
        assert _get_int(fresh_interp, "x") == 0


class TestInterpreterControlFlow:
    """測試控制流程：if/else、while、for、do-while、break、continue、短路求值。"""

    def test_if_true_branch(self, fresh_interp):
        _run_code(fresh_interp, "int x = 0;\nif (1) { x = 10; }")
        assert _get_int(fresh_interp, "x") == 10

    def test_if_false_skips_body(self, fresh_interp):
        _run_code(fresh_interp, "int x = 0;\nif (0) { x = 10; }")
        assert _get_int(fresh_interp, "x") == 0

    def test_if_else_true_branch(self, fresh_interp):
        _run_code(fresh_interp, "int x = 0;\nif (1) { x = 1; } else { x = 2; }")
        assert _get_int(fresh_interp, "x") == 1

    def test_if_else_false_branch(self, fresh_interp):
        _run_code(fresh_interp, "int x = 0;\nif (0) { x = 1; } else { x = 2; }")
        assert _get_int(fresh_interp, "x") == 2

    def test_nested_if_else(self, fresh_interp):
        code = "int x = 5;\nint r = 0;\nif (x < 0) { r = -1; } else if (x == 0) { r = 0; } else { r = 1; }"
        _run_code(fresh_interp, code)
        assert _get_int(fresh_interp, "r") == 1

    def test_while_loop_count(self, fresh_interp):
        _run_code(fresh_interp, "int i = 0;\nwhile (i < 3) { i = i + 1; }")
        assert _get_int(fresh_interp, "i") == 3

    def test_while_false_condition_skips_body(self, fresh_interp):
        _run_code(fresh_interp, "int x = 0;\nwhile (0) { x = 10; }")
        assert _get_int(fresh_interp, "x") == 0

    def test_for_loop_sum(self, fresh_interp):
        code = "int sum = 0;\nint i = 0;\nfor (i = 1; i <= 5; i = i + 1) { sum = sum + i; }"
        _run_code(fresh_interp, code)
        assert _get_int(fresh_interp, "sum") == 15

    def test_do_while_executes_at_least_once(self, fresh_interp):
        _run_code(fresh_interp, "int x = 0;\ndo { x = x + 1; } while (0);")
        assert _get_int(fresh_interp, "x") == 1

    def test_do_while_loop_count(self, fresh_interp):
        _run_code(fresh_interp, "int i = 0;\ndo { i = i + 1; } while (i < 3);")
        assert _get_int(fresh_interp, "i") == 3

    def test_break_exits_while(self, fresh_interp):
        code = "int i = 0;\nwhile (1) { i = i + 1;\nif (i == 3) { break; } }"
        _run_code(fresh_interp, code)
        assert _get_int(fresh_interp, "i") == 3

    def test_continue_skips_iteration(self, fresh_interp):
        code = "int sum = 0;\nint i = 0;\nfor (i = 0; i < 5; i = i + 1) { if (i == 2) { continue; } sum = sum + i; }"
        _run_code(fresh_interp, code)
        assert _get_int(fresh_interp, "sum") == 8

    def test_logical_and_short_circuit(self, fresh_interp):
        _run_code(fresh_interp, "int x = 0;")
        _run_code(fresh_interp, "int mark() { x = 99; return 1; }")
        _run_code(fresh_interp, "int r = 0 && mark();")
        assert _get_int(fresh_interp, "x") == 0

    def test_logical_or_short_circuit(self, fresh_interp):
        _run_code(fresh_interp, "int x = 0;")
        _run_code(fresh_interp, "int mark() { x = 99; return 1; }")
        _run_code(fresh_interp, "int r = 1 || mark();")
        assert _get_int(fresh_interp, "x") == 0

    def test_grade_classification_b(self, fresh_interp, capsys):
        _run_code(fresh_interp, "int score = 85;")
        grade_code = (
            "if (score >= 90) {\n"
            '    printf("Grade: A\\n");\n'
            "} else if (score >= 80) {\n"
            '    printf("Grade: B\\n");\n'
            "} else if (score >= 70) {\n"
            '    printf("Grade: C\\n");\n'
            "} else {\n"
            '    printf("Grade: F\\n");\n'
            "}"
        )
        _run_code(fresh_interp, grade_code)
        out = _filter_debug(capsys.readouterr().out)
        assert "Grade: B" in out

    def test_grade_classification_a(self, fresh_interp, capsys):
        _run_code(fresh_interp, "int score = 95;")
        grade_code = (
            "if (score >= 90) {\n"
            '    printf("Grade: A\\n");\n'
            "} else if (score >= 80) {\n"
            '    printf("Grade: B\\n");\n'
            "} else {\n"
            '    printf("Grade: F\\n");\n'
            "}"
        )
        _run_code(fresh_interp, grade_code)
        out = _filter_debug(capsys.readouterr().out)
        assert "Grade: A" in out

    def test_grade_classification_f(self, fresh_interp, capsys):
        _run_code(fresh_interp, "int score = 60;")
        grade_code = (
            "if (score >= 90) {\n"
            '    printf("Grade: A\\n");\n'
            "} else if (score >= 80) {\n"
            '    printf("Grade: B\\n");\n'
            "} else if (score >= 70) {\n"
            '    printf("Grade: C\\n");\n'
            "} else {\n"
            '    printf("Grade: F\\n");\n'
            "}"
        )
        _run_code(fresh_interp, grade_code)
        out = _filter_debug(capsys.readouterr().out)
        assert "Grade: F" in out

    def test_even_odd_odd(self, fresh_interp, capsys):
        _run_code(fresh_interp, "int n = 17;")
        _run_code(
            fresh_interp,
            'if (n % 2 == 0) { printf("%d is even\\n", n); }'
            ' else { printf("%d is odd\\n", n); }'
        )
        out = _filter_debug(capsys.readouterr().out)
        assert "17 is odd" in out

    def test_even_odd_even(self, fresh_interp, capsys):
        _run_code(fresh_interp, "int n = 16;")
        _run_code(
            fresh_interp,
            'if (n % 2 == 0) { printf("%d is even\\n", n); }'
            ' else { printf("%d is odd\\n", n); }'
        )
        out = _filter_debug(capsys.readouterr().out)
        assert "16 is even" in out

    def test_while_sum_1_to_100(self, fresh_interp, capsys):
        _run_code(fresh_interp, "int i = 1;")
        _run_code(fresh_interp, "int sum = 0;")
        _run_code(fresh_interp, "while (i <= 100) { sum += i;\ni = i + 1; }")
        _run_code(fresh_interp, 'printf("1+2+...+100 = %d\\n", sum);')
        out = _filter_debug(capsys.readouterr().out)
        assert "5050" in out

    def test_break_and_continue_combined(self, fresh_interp, capsys):
        # for i=1..20：continue 跳過 3 的倍數，break 在 i>15 時中止
        _run_code(fresh_interp, "int i;")
        loop_code = (
            "for (i = 1; i <= 20; i = i + 1) {\n"
            "    if (i % 3 == 0) continue;\n"
            "    if (i > 15) break;\n"
            '    printf("%d ", i);\n'
            "}"
        )
        _run_code(fresh_interp, loop_code)
        out = _filter_debug(capsys.readouterr().out)
        assert "1 2 4 5 7 8 10 11 13 14" in out

    def test_switch_matching_case_executes(self, fresh_interp):
        code = (
            "int n = 2;\n"
            "int result = 0;\n"
            "switch (n) {\n"
            "    case 1: result = 10; break;\n"
            "    case 2: result = 20; break;\n"
            "    default: result = 99;\n"
            "}"
        )
        _run_code(fresh_interp, code)
        assert _get_int(fresh_interp, "result") == 20

    def test_switch_default_executes_when_no_case_matches(self, fresh_interp):
        code = (
            "int n = 5;\n"
            "int result = 0;\n"
            "switch (n) {\n"
            "    case 1: result = 10; break;\n"
            "    default: result = 99;\n"
            "}"
        )
        _run_code(fresh_interp, code)
        assert _get_int(fresh_interp, "result") == 99

    def test_switch_no_match_without_default_executes_nothing(self, fresh_interp):
        code = (
            "int n = 5;\n"
            "int result = 7;\n"
            "switch (n) {\n"
            "    case 1: result = 10; break;\n"
            "    case 2: result = 20; break;\n"
            "}"
        )
        _run_code(fresh_interp, code)
        assert _get_int(fresh_interp, "result") == 7

    def test_switch_fallthrough_executes_following_clauses(self, fresh_interp):
        code = (
            "int n = 1;\n"
            "int result = 0;\n"
            "switch (n) {\n"
            "    case 1: result += 1;\n"
            "    case 2: result += 10;\n"
            "    default: result += 100;\n"
            "}"
        )
        _run_code(fresh_interp, code)
        assert _get_int(fresh_interp, "result") == 111

    def test_switch_break_prevents_fallthrough(self, fresh_interp):
        code = (
            "int n = 1;\n"
            "int result = 0;\n"
            "switch (n) {\n"
            "    case 1: result += 1; break;\n"
            "    case 2: result += 10;\n"
            "    default: result += 100;\n"
            "}"
        )
        _run_code(fresh_interp, code)
        assert _get_int(fresh_interp, "result") == 1

    def test_switch_case_constant_expression_matches(self, fresh_interp):
        code = (
            "int n = 3;\n"
            "int result = 0;\n"
            "switch (n) {\n"
            "    case 1 + 2: result = 30; break;\n"
            "    default: result = 99;\n"
            "}"
        )
        _run_code(fresh_interp, code)
        assert _get_int(fresh_interp, "result") == 30

    def test_switch_case_char_constant_matches(self, fresh_interp):
        code = (
            "char ch = 'A';\n"
            "int result = 0;\n"
            "switch (ch) {\n"
            "    case 'A': result = 1; break;\n"
            "    default: result = 2;\n"
            "}"
        )
        _run_code(fresh_interp, code)
        assert _get_int(fresh_interp, "result") == 1

    def test_switch_case_logical_or_constant_short_circuits(self, fresh_interp):
        code = (
            "int n = 1;\n"
            "int result = 0;\n"
            "switch (n) {\n"
            "    case 1 || (1 / 0): result = 1; break;\n"
            "    default: result = 2;\n"
            "}"
        )
        _run_code(fresh_interp, code)
        assert _get_int(fresh_interp, "result") == 1

    def test_switch_case_logical_and_constant_short_circuits(self, fresh_interp):
        code = (
            "int n = 0;\n"
            "int result = 0;\n"
            "switch (n) {\n"
            "    case 0 && (1 / 0): result = 1; break;\n"
            "    default: result = 2;\n"
            "}"
        )
        _run_code(fresh_interp, code)
        assert _get_int(fresh_interp, "result") == 1

    def test_switch_allows_empty_statements_before_case(self, fresh_interp):
        code = (
            "int n = 1;\n"
            "int result = 0;\n"
            "switch (n) {\n"
            "    ;\n"
            "    ;\n"
            "    case 1: result = 7; break;\n"
            "}"
        )
        _run_code(fresh_interp, code)
        assert _get_int(fresh_interp, "result") == 7

    def test_switch_nested_loop_break_only_exits_loop(self, fresh_interp):
        code = (
            "int result = 0;\n"
            "switch (1) {\n"
            "    case 1:\n"
            "        while (1) { result += 1; break; }\n"
            "        result += 10;\n"
            "        break;\n"
            "    default: result = 99;\n"
            "}"
        )
        _run_code(fresh_interp, code)
        assert _get_int(fresh_interp, "result") == 11

    def test_switch_inside_loop_continue_targets_loop(self, fresh_interp):
        code = (
            "int i;\n"
            "int sum = 0;\n"
            "for (i = 0; i < 3; i = i + 1) {\n"
            "    switch (i) {\n"
            "        case 1: continue;\n"
            "        default: sum += i;\n"
            "    }\n"
            "}"
        )
        _run_code(fresh_interp, code)
        assert _get_int(fresh_interp, "sum") == 2

    def test_for_loop_squares(self, fresh_interp, capsys):
        _run_code(fresh_interp, "int i;")
        _run_code(
            fresh_interp,
            'for (i = 1; i <= 9; i = i + 1) { printf("%d * %d = %d\\n", i, i, i * i); }'
        )
        out = _filter_debug(capsys.readouterr().out)
        expected = [
            "1 * 1 = 1", "2 * 2 = 4", "3 * 3 = 9",
            "4 * 4 = 16", "5 * 5 = 25", "6 * 6 = 36",
            "7 * 7 = 49", "8 * 8 = 64", "9 * 9 = 81",
        ]
        for line in expected:
            assert line in out


class TestInterpreterFunctions:
    """測試使用者定義函式、參數傳遞、return 值、遞迴。"""

    def test_simple_function_return_value(self, fresh_interp):
        _run_code(fresh_interp, "int add(int a, int b) { return a + b; }")
        _run_code(fresh_interp, "int result = add(3, 4);")
        assert _get_int(fresh_interp, "result") == 7

    def test_void_function_call(self, fresh_interp, capsys):
        _run_code(fresh_interp, 'void greet() { printf("hi"); }')
        _run_code(fresh_interp, "greet();")
        out = _filter_debug(capsys.readouterr().out)
        assert "hi" in out

    def test_recursive_factorial(self, fresh_interp, capsys):
        factorial_code = (
            "int factorial(int n) {\n"
            "    if (n <= 1) { return 1; }\n"
            "    return n * factorial(n - 1);\n"
            "}"
        )
        _run_code(fresh_interp, factorial_code)
        _run_code(fresh_interp, 'printf("%d", factorial(5));')
        out = _filter_debug(capsys.readouterr().out)
        assert "120" in out

    def test_function_local_variable_isolation(self, fresh_interp):
        _run_code(fresh_interp, "int x = 10;")
        _run_code(fresh_interp, "void modify() { int x = 999; }")
        _run_code(fresh_interp, "modify();")
        assert _get_int(fresh_interp, "x") == 10

    def test_function_parameter_pass_by_value(self, fresh_interp):
        _run_code(fresh_interp, "int val = 5;")
        _run_code(fresh_interp, "void double_it(int n) { n = n * 2; }")
        _run_code(fresh_interp, "double_it(val);")
        assert _get_int(fresh_interp, "val") == 5

    def test_multiple_functions_defined(self, fresh_interp, capsys):
        _run_code(fresh_interp, 'void say_hello() { printf("hello"); }')
        _run_code(fresh_interp, 'void say_world() { printf("world"); }')
        _run_code(fresh_interp, "say_hello();")
        _run_code(fresh_interp, "say_world();")
        out = _filter_debug(capsys.readouterr().out)
        assert "hello" in out
        assert "world" in out

    def test_function_with_array_parameter(self, fresh_interp, capsys):
        sum_arr_code = (
            "int sum_arr(int a[], int n) {\n"
            "    int total = 0;\n"
            "    int i = 0;\n"
            "    while (i < n) {\n"
            "        total = total + a[i];\n"
            "        i = i + 1;\n"
            "    }\n"
            "    return total;\n"
            "}"
        )
        _run_code(fresh_interp, sum_arr_code)
        _run_code(fresh_interp, "int arr[3] = {10, 20, 30};")
        _run_code(fresh_interp, 'printf("%d", sum_arr(arr, 3));')
        out = _filter_debug(capsys.readouterr().out)
        assert "60" in out


class TestInterpreterArrays:
    """測試陣列宣告、元素讀寫、初始化列表、字串初始化。"""

    def test_array_declare_and_write(self, fresh_interp):
        _run_code(fresh_interp, "int arr[5];\narr[0] = 10;")
        sym = fresh_interp.symtable.lookup_var("arr")
        assert fresh_interp.memory.array_read(sym.addr, 0, "int") == 10

    def test_array_init_list(self, fresh_interp):
        _run_code(fresh_interp, "int arr[3] = {10, 20, 30};")
        sym = fresh_interp.symtable.lookup_var("arr")
        assert fresh_interp.memory.array_read(sym.addr, 0, "int") == 10
        assert fresh_interp.memory.array_read(sym.addr, 1, "int") == 20
        assert fresh_interp.memory.array_read(sym.addr, 2, "int") == 30

    def test_char_array_string_init(self, fresh_interp):
        _run_code(fresh_interp, 'char s[6] = "Hello";')
        sym = fresh_interp.symtable.lookup_var("s")
        assert fresh_interp.memory.array_read(sym.addr, 0, "char") == ord('H')
        assert fresh_interp.memory.array_read(sym.addr, 4, "char") == ord('o')
        assert fresh_interp.memory.array_read(sym.addr, 5, "char") == 0

    def test_array_all_elements_correct(self, fresh_interp):
        _run_code(fresh_interp, "int arr[5] = {1, 2, 3, 4, 5};")
        sym = fresh_interp.symtable.lookup_var("arr")
        for i in range(5):
            assert fresh_interp.memory.array_read(sym.addr, i, "int") == i + 1

    def test_array_as_pointer_decay(self, fresh_interp):
        _run_code(fresh_interp, "int arr[3] = {10, 20, 30};\nint* p = arr;")
        sym_arr = fresh_interp.symtable.lookup_var("arr")
        sym_p = fresh_interp.symtable.lookup_var("p")
        ptr_val = fresh_interp.memory.get_ptr(sym_p.addr)
        assert ptr_val == sym_arr.addr

    def test_array_scenario_09_indexed_write_read_and_output(self, fresh_interp, capsys):
        code = (
            "int arr[10];\n"
            "int i;\n"
            "for (i = 0; i < 10; i = i + 1) {\n"
            "    arr[i] = (i + 1) * 10;\n"
            "}\n"
            "for (i = 0; i < 10; i = i + 1) {\n"
            '    printf("arr[%d] = %d\\n", i, arr[i]);\n'
            "}"
        )
        _run_code(fresh_interp, code)

        out = _filter_debug(capsys.readouterr().out)
        expected_values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]

        for index, value in enumerate(expected_values):
            assert f"arr[{index}] = {value}" in out

        sym = fresh_interp.symtable.lookup_var("arr")
        for index, value in enumerate(expected_values):
            assert fresh_interp.memory.array_read(sym.addr, index, "int") == value

        assert _get_int(fresh_interp, "i") == 10


class TestInterpreterPointers:
    """測試指標宣告、取址、解參考、指標算術。"""

    def test_address_of_and_dereference(self, fresh_interp):
        _run_code(fresh_interp, "int x = 5;\nint* p = &x;\n*p = 99;")
        assert _get_int(fresh_interp, "x") == 99

    def test_pointer_arithmetic_add(self, fresh_interp):
        _run_code(fresh_interp, "int arr[3] = {10, 20, 30};\nint* p = arr;\nint val = *(p + 1);")
        assert _get_int(fresh_interp, "val") == 20

    def test_char_pointer_to_string(self, fresh_interp, capsys):
        _run_code(fresh_interp, 'char* s = "hello";\nprintf("%s", s);')
        out = _filter_debug(capsys.readouterr().out)
        assert "hello" in out


class TestInterpreterPrintf:
    """測試 printf 格式化輸出（用 capsys 捕捉，用 _filter_debug 去除 debug 行）。"""

    def test_printf_d_positive(self, fresh_interp, capsys):
        _run_code(fresh_interp, 'printf("%d", 42);')
        out = _filter_debug(capsys.readouterr().out)
        assert out.strip() == "42"

    def test_printf_d_negative(self, fresh_interp, capsys):
        _run_code(fresh_interp, 'printf("%d", -5);')
        out = _filter_debug(capsys.readouterr().out)
        assert out.strip() == "-5"

    def test_printf_s_char_array(self, fresh_interp, capsys):
        _run_code(fresh_interp, 'char msg[6] = "hello";\nprintf("%s", msg);')
        out = _filter_debug(capsys.readouterr().out)
        assert "hello" in out

    def test_printf_c_format(self, fresh_interp, capsys):
        _run_code(fresh_interp, 'printf("%c", 65);')
        out = _filter_debug(capsys.readouterr().out)
        assert out.strip() == "A"

    def test_printf_x_format(self, fresh_interp, capsys):
        _run_code(fresh_interp, 'printf("%x", 255);')
        out = _filter_debug(capsys.readouterr().out)
        assert out.strip() == "ff"

    def test_printf_percent_literal(self, fresh_interp, capsys):
        _run_code(fresh_interp, 'printf("100%%");')
        out = _filter_debug(capsys.readouterr().out)
        assert "100%" in out

    def test_printf_newline_escape(self, fresh_interp, capsys):
        _run_code(fresh_interp, 'printf("a\\nb");')
        raw_out = capsys.readouterr().out
        exact_lines = [l for l in raw_out.split("\n") if l in ("a", "b")]
        assert exact_lines == ["a", "b"]

    def test_printf_mixed_format(self, fresh_interp, capsys):
        _run_code(fresh_interp, 'printf("%d + %d = %d", 1, 2, 3);')
        out = _filter_debug(capsys.readouterr().out)
        assert "1 + 2 = 3" in out

    def test_puts_outputs_string(self, fresh_interp, capsys):
        _run_code(fresh_interp, 'char msg[6] = "hello";\nputs(msg);')
        out = _filter_debug(capsys.readouterr().out)
        assert "hello" in out


class TestInterpreterErrors:
    """測試執行期錯誤是否正確拋出且包含適當訊息。"""

    def test_division_by_zero_raises(self, fresh_interp):
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, "int x = 5 / 0;")
        assert "zero" in str(exc.value).lower()

    def test_undefined_variable_raises(self, fresh_interp):
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, "int y = z + 1;")
        assert "Undefined" in str(exc.value) or "undefined" in str(exc.value).lower()

    def test_redeclare_variable_raises(self, fresh_interp):
        _run_code(fresh_interp, "int x = 1;")
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, "int x = 2;")
        assert "already" in str(exc.value).lower()

    def test_cannot_assign_to_array_raises(self, fresh_interp):
        _run_code(fresh_interp, "int arr[3] = {1, 2, 3};")
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, "arr = 0;")
        assert "Cannot assign" in str(exc.value) or "assign" in str(exc.value).lower()

    def test_pointer_init_with_integer_raises(self, fresh_interp):
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, "int* p = 5;")
        assert "pointer" in str(exc.value).lower() or "Cannot initialize" in str(exc.value)

    def test_builtin_fixed_argument_count_too_few_raises(self, fresh_interp):
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, "putchar();")
        message = str(exc.value)
        assert "putchar" in message
        assert "expects 1 arguments" in message
        assert "got 0" in message

    def test_builtin_fixed_argument_count_too_many_raises(self, fresh_interp):
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, "getchar(1);")
        message = str(exc.value)
        assert "getchar" in message
        assert "expects 0 arguments" in message
        assert "got 1" in message

    def test_builtin_variadic_argument_count_too_few_raises(self, fresh_interp):
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, "printf();")
        message = str(exc.value)
        assert "printf" in message
        assert "expects at least 1 arguments" in message
        assert "got 0" in message

    def test_builtin_return_type_mismatch_raises(self, fresh_interp):
        # scanf 目前尚未實作，builtins.py 會回傳 None；外層簽名檢查應抓出 int 回傳型別不符。
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, 'scanf("%d");')
        message = str(exc.value)
        assert "scanf" in message
        assert "must return int" in message

    def test_user_function_argument_count_raises(self, fresh_interp):
        _run_code(fresh_interp, "int add(int a, int b) { return a + b; }")
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, "add(1);")
        message = str(exc.value)
        assert "add" in message
        assert "expects 2 arguments" in message
        assert "got 1" in message

    def test_void_user_function_returning_value_raises(self, fresh_interp):
        _run_code(fresh_interp, "void bad() { return 1; }")
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, "bad();")
        message = str(exc.value)
        assert "Void function 'bad'" in message
        assert "should not return a value" in message

    def test_nonvoid_user_function_empty_return_raises(self, fresh_interp):
        _run_code(fresh_interp, "int bad() { return; }")
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, "bad();")
        message = str(exc.value)
        assert "bad" in message
        assert "must return int" in message

    def test_nonvoid_user_function_wrong_return_type_raises(self, fresh_interp):
        _run_code(fresh_interp, 'int bad() { return "x"; }')
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, "bad();")
        message = str(exc.value)
        assert "return from 'bad'" in message
        assert "as int" in message

    def test_case_outside_switch_raises(self, fresh_interp):
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, "case 1: ;")
        assert "case" in str(exc.value)
        assert "switch" in str(exc.value)

    def test_default_outside_switch_raises(self, fresh_interp):
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, "default: ;")
        assert "default" in str(exc.value)
        assert "switch" in str(exc.value)

    def test_switch_duplicate_case_raises(self, fresh_interp):
        code = (
            "int n = 1;\n"
            "switch (n) {\n"
            "    case 1: break;\n"
            "    case 1: break;\n"
            "}"
        )
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, code)
        assert "Duplicate case" in str(exc.value)

    def test_switch_duplicate_default_raises(self, fresh_interp):
        code = (
            "int n = 1;\n"
            "switch (n) {\n"
            "    default: break;\n"
            "    default: break;\n"
            "}"
        )
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, code)
        assert "Duplicate default" in str(exc.value)

    def test_switch_case_nonconstant_label_raises(self, fresh_interp):
        code = (
            "int n = 1;\n"
            "int x = 1;\n"
            "switch (n) {\n"
            "    case x: break;\n"
            "}"
        )
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, code)
        assert "integer constant expression" in str(exc.value)

    def test_switch_case_function_call_label_raises(self, fresh_interp):
        code = (
            "int value() { return 1; }\n"
            "int n = 1;\n"
            "switch (n) {\n"
            "    case value(): break;\n"
            "}"
        )
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, code)
        assert "integer constant expression" in str(exc.value)

    def test_switch_case_string_label_raises(self, fresh_interp):
        code = (
            "int n = 1;\n"
            "switch (n) {\n"
            "    case \"x\": break;\n"
            "}"
        )
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, code)
        assert "integer constant expression" in str(exc.value)

    def test_switch_case_array_index_label_raises(self, fresh_interp):
        code = (
            "int n = 1;\n"
            "int arr[1] = {1};\n"
            "switch (n) {\n"
            "    case arr[0]: break;\n"
            "}"
        )
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, code)
        assert "integer constant expression" in str(exc.value)

    def test_switch_case_division_by_zero_constant_raises(self, fresh_interp):
        code = (
            "int n = 1;\n"
            "switch (n) {\n"
            "    case 1 / 0: break;\n"
            "}"
        )
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, code)
        assert "Division by zero" in str(exc.value)

    def test_switch_case_negative_left_shift_raises_syntax_error(self, fresh_interp):
        code = (
            "int n = 1;\n"
            "switch (n) {\n"
            "    case 1 << -1: break;\n"
            "}"
        )
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, code)
        assert "Negative shift count" in str(exc.value)

    def test_switch_case_negative_right_shift_raises_syntax_error(self, fresh_interp):
        code = (
            "int n = 1;\n"
            "switch (n) {\n"
            "    case 1 >> -1: break;\n"
            "}"
        )
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, code)
        assert "Negative shift count" in str(exc.value)

    def test_switch_rejects_statement_before_first_case(self, fresh_interp):
        code = (
            "int n = 1;\n"
            "int result = 0;\n"
            "switch (n) {\n"
            "    result = 1;\n"
            "    case 1: result = 7; break;\n"
            "}"
        )
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, code)
        assert "Expected 'case' or 'default'" in str(exc.value)

    def test_switch_expression_non_int_raises(self, fresh_interp):
        with pytest.raises(Exception) as exc:
            _run_code(fresh_interp, 'switch ("x") { default: ; }')
        message = str(exc.value)
        assert "switch expression" in message
        assert "int" in message
