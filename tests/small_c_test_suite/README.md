# Small-C Test Suite

This folder contains standalone Small-C acceptance-style test programs.
Each `.sc` file has a matching `.expected` file with the expected output or expected error message.

## Coverage Map

| Category | Files |
|---|---|
| Basic arithmetic and variables | `01_arithmetic_precedence.sc`, `02_variables_compound.sc`, `16_prefix_postfix_increment.sc`, `17_lvalue_increment_array_pointer.sc` |
| Control structures | `03_control_if_for_while.sc`, `04_control_do_break_continue.sc` |
| Functions and recursion | `05_functions_calls.sc`, `06_recursion_factorial.sc` |
| Arrays and pointers | `07_arrays_strings.sc`, `08_pointers_swap.sc` |
| Switch/case extension | `09_switch_case.sc`, `10_switch_fallthrough.sc` |
| Error handling | `11_error_syntax_missing_semicolon.sc`, `12_error_runtime_division_by_zero.sc`, `13_error_pointer_null_deref.sc`, `14_error_pointer_out_of_bounds.sc`, `15_error_array_out_of_bounds.sc` |

Pointer boundary cases include null pointer dereference and pointer arithmetic outside an allocation.
