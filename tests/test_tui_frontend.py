import asyncio

import pytest

pytest.importorskip("textual")
pytest.importorskip("tree_sitter")
pytest.importorskip("tree_sitter_c")

from textual.widgets import Input, TextArea

from main_tui import SmallCTuiApp


def test_tui_accepts_check_and_run_commands():
    asyncio.run(run_tui_smoke())


def test_tui_f6_runs_check_even_when_editor_is_focused():
    asyncio.run(run_f6_smoke())


def test_tui_repl_buffer_commands_update_editor():
    asyncio.run(run_buffer_command_smoke())


def test_tui_repl_multiline_buffer_modes_update_editor():
    asyncio.run(run_multiline_buffer_mode_smoke())


def test_tui_command_line_executes_small_c_without_buffering():
    asyncio.run(run_inline_command_smoke())


async def run_tui_smoke():
    app = SmallCTuiApp()
    async with app.run_test() as pilot:
        editor = app.query_one("#editor", TextArea)
        command = app.query_one("#command", Input)

        assert editor.language == "smallc"
        editor.load_text("int main() {\n    return 7;\n}")
        await pilot.pause()

        command.value = "CHECK"
        await pilot.press("enter")
        command.value = "RUN"
        await pilot.press("enter")
        await pilot.pause()

        assert app.runtime is not None


async def run_f6_smoke():
    app = SmallCTuiApp()
    calls = []

    original_check = app.check_program

    def wrapped_check():
        calls.append("check")
        original_check()

    app.check_program = wrapped_check

    async with app.run_test() as pilot:
        editor = app.query_one("#editor", TextArea)
        editor.load_text("int main() {\n    return 0;\n}")
        editor.focus()
        await pilot.pause()

        await pilot.press("f6")
        await pilot.pause()

        assert calls == ["check"]


async def run_buffer_command_smoke():
    app = SmallCTuiApp()
    async with app.run_test() as pilot:
        editor = app.query_one("#editor", TextArea)
        command = app.query_one("#command", Input)

        for value in [
            "APPEND int main() {",
            "APPEND     return 0;",
            "APPEND }",
            "INSERT 2     int x = 1;",
            "EDIT 3     return x;",
            "DELETE 4",
            "LIST 1-3",
            "HELP LIST",
            "ABOUT",
        ]:
            command.value = value
            await pilot.press("enter")
            await pilot.pause()

        assert editor.text.splitlines() == [
            "int main() {",
            "    int x = 1;",
            "    return x;",
        ]


async def run_multiline_buffer_mode_smoke():
    app = SmallCTuiApp()
    async with app.run_test() as pilot:
        editor = app.query_one("#editor", TextArea)
        command = app.query_one("#command", Input)

        for value in [
            "APPEND",
            "int main() {",
            "    int x = 1;",
            "}",
            ".",
            "INSERT 3",
            "    return x;",
            ".",
            "EDIT 2     int x = 2;",
        ]:
            command.value = value
            await pilot.press("enter")
            await pilot.pause()

        assert editor.text.splitlines() == [
            "int main() {",
            "    int x = 2;",
            "    return x;",
            "}",
        ]


async def run_inline_command_smoke():
    app = SmallCTuiApp()
    async with app.run_test() as pilot:
        editor = app.query_one("#editor", TextArea)
        command = app.query_one("#command", Input)

        for value in ["int x = 3;", "x = x + 4;"]:
            command.value = value
            await pilot.press("enter")
            await pilot.pause()

        symbol = app.runtime.symtable.lookup_var("x")
        assert app.runtime.memory.get_int(symbol.addr) == 7
        assert editor.text == ""
