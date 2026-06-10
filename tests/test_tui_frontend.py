import asyncio

import pytest

pytest.importorskip("textual")
pytest.importorskip("tree_sitter")
pytest.importorskip("tree_sitter_c")

from textual.widgets import Input, TextArea

from main_tui import SmallCTuiApp


def test_tui_accepts_check_and_run_commands():
    asyncio.run(run_tui_smoke())


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
