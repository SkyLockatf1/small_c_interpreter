import textwrap

import main


def run_check(source: str, capsys):
    buffer = textwrap.dedent(source).strip().splitlines()
    try:
        main.check_program_buffer(buffer, {})
    except Exception as exc:
        return str(exc)
    return capsys.readouterr().out


def test_check_accepts_valid_program(capsys):
    out = run_check(
        """
        int add(int a, int b) {
            return a + b;
        }

        int main() {
            int x = add(1, 2);
            return x;
        }
        """,
        capsys,
    )

    assert "No errors found." in out


def test_check_does_not_execute_program(capsys):
    out = run_check(
        """
        int main() {
            printf("CHECK should not print this\\n");
            return 0;
        }
        """,
        capsys,
    )

    assert "No errors found." in out
    assert "CHECK should not print this" not in out


def test_check_reports_undefined_variable(capsys):
    out = run_check(
        """
        int main() {
            x = 1;
            return 0;
        }
        """,
        capsys,
    )

    assert "Error at line 2: undefined variable 'x'." in out
    assert "1 error(s) found." in out


def test_check_reports_undefined_function(capsys):
    out = run_check(
        """
        int main() {
            foo();
            return 0;
        }
        """,
        capsys,
    )

    assert "Error at line 2: undefined function 'foo'." in out


def test_check_reports_assignment_type_error(capsys):
    out = run_check(
        """
        int main() {
            int *p;
            int x;
            x = p;
            return 0;
        }
        """,
        capsys,
    )

    assert "Error at line 4: cannot use value of type int* as int for assignment." in out


def test_check_reports_function_argument_count(capsys):
    out = run_check(
        """
        int add(int a, int b) {
            return a + b;
        }

        int main() {
            return add(1);
        }
        """,
        capsys,
    )

    assert "function 'add' expects 2 arguments, got 1." in out


def test_check_reports_function_argument_type(capsys):
    out = run_check(
        """
        int first(int *p) {
            return *p;
        }

        int main() {
            int x;
            return first(x);
        }
        """,
        capsys,
    )

    assert "cannot use value of type int as int* for parameter 1 'p' of 'first'." in out


def test_check_reports_missing_return(capsys):
    out = run_check(
        """
        int main() {
            if (1) {
                return 1;
            }
        }
        """,
        capsys,
    )

    assert "function 'main' may end without returning int." in out


def test_check_reports_void_return_value(capsys):
    out = run_check(
        """
        void main() {
            return 1;
        }
        """,
        capsys,
    )

    assert "void function 'main' should not return a value." in out


def test_check_reports_invalid_main_signature(capsys):
    out = run_check(
        """
        int main(int argc) {
            return 0;
        }
        """,
        capsys,
    )

    assert "main function must not have parameters." in out


def test_check_reports_continue_outside_loop(capsys):
    out = run_check(
        """
        int main() {
            continue;
            return 0;
        }
        """,
        capsys,
    )

    assert "continue" in out
    assert "only allowed inside a loop" in out


def test_check_accepts_array_pointer_decay(capsys):
    out = run_check(
        """
        int first(int arr[]) {
            return arr[0];
        }

        int main() {
            int values[2];
            values[0] = 7;
            return first(values);
        }
        """,
        capsys,
    )

    assert "No errors found." in out


def test_check_accepts_switch_when_all_cases_and_default_return(capsys):
    out = run_check(
        """
        int main() {
            int x = 2;
            switch (x) {
            case 1:
                return 1;
            case 2:
                return 2;
            default:
                return 0;
            }
        }
        """,
        capsys,
    )

    assert "No errors found." in out


def test_check_keeps_switch_without_default_conservative(capsys):
    out = run_check(
        """
        int main() {
            int x = 2;
            switch (x) {
            case 1:
                return 1;
            case 2:
                return 2;
            }
        }
        """,
        capsys,
    )

    assert "function 'main' may end without returning int." in out


def test_check_keeps_switch_with_break_conservative(capsys):
    out = run_check(
        """
        int main() {
            int x = 2;
            switch (x) {
            case 1:
                break;
            default:
                return 0;
            }
        }
        """,
        capsys,
    )

    assert "function 'main' may end without returning int." in out


def test_check_accepts_deref_array_as_lvalue(capsys):
    out = run_check(
        """
        int main() {
            int arr[3];
            *arr = 10;
            return *arr;
        }
        """,
        capsys,
    )

    assert "No errors found." in out


def test_check_accepts_deref_char_array_as_lvalue(capsys):
    out = run_check(
        """
        int main() {
            char buf[8];
            *buf = 'A';
            return 0;
        }
        """,
        capsys,
    )

    assert "No errors found." in out
