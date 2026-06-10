import contextlib
import io
import os
from pathlib import Path

try:
    from textual import on
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.widgets import Footer, Header, Input, RichLog, Static, TextArea
except ImportError as exc:
    raise SystemExit(
        "Textual is required for the TUI frontend.\n"
        "Install it with: pip install textual\n"
        "Or run with: uv run --with textual python main_tui.py"
    ) from exc

import interpreter
import main as smallc_main
import parser


SMALL_C_HIGHLIGHT_QUERY = r"""
(primitive_type) @type
(identifier) @variable
(function_declarator declarator: (identifier) @function)
(call_expression function: (identifier) @function)
(number_literal) @number
(string_literal) @string
(char_literal) @string
(comment) @comment

[
  "if"
  "else"
  "while"
  "for"
  "do"
  "switch"
  "case"
  "default"
  "break"
  "continue"
  "return"
] @keyword

[
  "="
  "+="
  "-="
  "*="
  "/="
  "%="
  "+"
  "-"
  "*"
  "/"
  "%"
  "!"
  "~"
  "&"
  "|"
  "^"
  "&&"
  "||"
  "=="
  "!="
  "<"
  "<="
  ">"
  ">="
  "<<"
  ">>"
] @operator
"""


def create_smallc_editor() -> TextArea:
    editor = TextArea.code_editor(
        "",
        language=None,
        theme="monokai",
        id="editor",
        show_line_numbers=True,
        soft_wrap=False,
        tab_behavior="indent",
    )
    try:
        import tree_sitter_c
        from tree_sitter import Language

        editor.register_language(
            "smallc",
            Language(tree_sitter_c.language()),
            SMALL_C_HIGHLIGHT_QUERY,
        )
        editor.language = "smallc"
    except Exception:
        # Syntax highlighting is optional; the editor still works without tree-sitter-c.
        pass
    return editor


class SmallCTuiApp(App):
    """Textual frontend for the existing Small-C interpreter modules."""

    CSS = """
    Screen {
        background: #101418;
        color: #d7dde5;
    }

    #root {
        height: 1fr;
    }

    #workspace {
        height: 1fr;
    }

    #left-pane {
        width: 58%;
        height: 100%;
        border: tall #4f6f8f;
        padding: 0 1;
    }

    #right-pane {
        width: 42%;
        height: 100%;
        border: tall #6a7f5a;
        padding: 0 1;
    }

    #title-line {
        height: 1;
        color: #b8d7ff;
        text-style: bold;
    }

    #status {
        height: 1;
        color: #a8b3c4;
    }

    #editor {
        height: 1fr;
        background: #0b0f14;
        color: #e3e9f2;
    }

    #output {
        height: 1fr;
        background: #0b0f14;
        color: #d7dde5;
    }

    #command {
        dock: bottom;
        height: 3;
        border: tall #4f6f8f;
        background: #111923;
    }
    """

    BINDINGS = [
        ("f5", "run_program", "Run"),
        ("f6", "check_program", "Check"),
        ("ctrl+s", "save_prompt", "Save"),
        ("ctrl+o", "load_prompt", "Load"),
        ("ctrl+n", "new_buffer", "New"),
        ("ctrl+l", "clear_output", "Clear"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.macro_definitions = {}
        self.runtime = interpreter.Interpreter()
        self.trace_enabled = False
        self.current_file: str | None = None
        self.dirty = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="root"):
            yield Static("Small-C TUI  |  F5 RUN  F6 CHECK  Ctrl+S SAVE  Ctrl+O LOAD", id="title-line")
            with Horizontal(id="workspace"):
                with Vertical(id="left-pane"):
                    yield Static("BUFFER", classes="pane-title")
                    yield create_smallc_editor()
                with Vertical(id="right-pane"):
                    yield Static("OUTPUT", classes="pane-title")
                    yield RichLog(id="output", wrap=True, highlight=True, markup=True)
            yield Static("", id="status")
        yield Input(placeholder="Command: RUN, CHECK, LOAD file.sc, SAVE file.sc, TRACE ON/OFF, VARS, FUNCS, HELP", id="command")
        yield Footer()

    def on_mount(self) -> None:
        self.output.write("[bold #b8d7ff]Small-C Interactive Interpreter TUI[/]")
        self.output.write("Type HELP for commands. Edit code on the left, then press F5 or F6.")
        self.update_status()

    @property
    def editor(self) -> TextArea:
        return self.query_one("#editor", TextArea)

    @property
    def output(self) -> RichLog:
        return self.query_one("#output", RichLog)

    @property
    def command_input(self) -> Input:
        return self.query_one("#command", Input)

    def buffer(self) -> list[str]:
        text = self.editor.text
        if text == "":
            return []
        return text.splitlines()

    def set_buffer(self, lines: list[str]) -> None:
        self.editor.load_text("\n".join(lines))
        self.dirty = False
        self.update_status()

    def update_status(self) -> None:
        filename = self.current_file or "<untitled>"
        dirty = "modified" if self.dirty else "saved"
        trace = "on" if self.trace_enabled else "off"
        lines = len(self.buffer())
        self.query_one("#status", Static).update(
            f"file: {filename} | lines: {lines} | trace: {trace} | state: {dirty}"
        )

    def capture(self, func, *args, **kwargs):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            result = func(*args, **kwargs)
        return result, stream.getvalue()

    def write_output(self, text: str, style: str | None = None) -> None:
        if not text:
            return
        for line in text.rstrip("\n").splitlines():
            if style:
                self.output.write(f"[{style}]{line}[/]")
            else:
                self.output.write(line)

    def report_exception(self, exc: Exception) -> None:
        self.write_output(str(exc), "bold red")

    def action_run_program(self) -> None:
        self.run_program()

    def action_check_program(self) -> None:
        self.check_program()

    def action_save_prompt(self) -> None:
        self.command_input.value = "SAVE "
        self.command_input.focus()

    def action_load_prompt(self) -> None:
        self.command_input.value = "LOAD "
        self.command_input.focus()

    def action_new_buffer(self) -> None:
        self.set_buffer([])
        self.current_file = None
        self.runtime = interpreter.Interpreter()
        self.output.write("[bold yellow]New buffer created.[/]")
        self.update_status()

    def action_clear_output(self) -> None:
        self.output.clear()

    def check_program(self) -> None:
        try:
            _, text = self.capture(smallc_main.check_program_buffer, self.buffer(), self.macro_definitions)
            self.write_output(text, "green" if "No errors found." in text else None)
        except Exception as exc:
            self.report_exception(exc)
        self.update_status()

    def run_program(self) -> None:
        try:
            runtime, text = self.capture(
                smallc_main.run_program_buffer,
                self.buffer(),
                self.macro_definitions,
                self.trace_enabled,
            )
            if runtime is not None:
                self.runtime = runtime
            self.write_output(text)
        except Exception as exc:
            self.report_exception(exc)
        self.update_status()

    def load_file(self, filename: str) -> None:
        path = Path(filename)
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            self.report_exception(Exception(f"REPL error: Could not read '{filename}': {exc}"))
            return
        self.current_file = str(path)
        self.set_buffer(lines)
        self.output.write(f"[green]Loaded {len(lines)} lines from '{filename}'.[/]")

    def save_file(self, filename: str | None = None) -> None:
        target = filename or self.current_file
        if not target:
            self.output.write("[bold yellow]Usage: SAVE <filename>[/]")
            return
        lines = self.buffer()
        try:
            Path(target).write_text("\n".join(lines), encoding="utf-8")
        except OSError as exc:
            self.report_exception(Exception(f"REPL error: Could not write '{target}': {exc}"))
            return
        self.current_file = target
        self.dirty = False
        self.output.write(f"[green]Saved {len(lines)} lines to '{target}'.[/]")
        self.update_status()

    def list_buffer(self) -> None:
        lines = self.buffer()
        if not lines:
            self.output.write("[yellow]Program buffer is empty.[/]")
            return
        for index, line in enumerate(lines, start=1):
            self.output.write(f"{index:>4}: {line}")

    def show_vars(self) -> None:
        variables = list(self.runtime.symtable.iter_vars())
        vm = self.runtime.memory
        if not variables:
            self.output.write("No variables defined.")
            return
        for symbol in variables:
            if symbol.is_array:
                shown = min(symbol.array_length, 10)
                values = [str(vm.array_read(symbol.addr, i, symbol.var_type)) for i in range(shown)]
                if symbol.array_length > shown:
                    values.append("...")
                self.output.write(f"{symbol.var_type} {symbol.name}[{symbol.array_length}] = {{{', '.join(values)}}}")
            elif symbol.var_type == "int":
                self.output.write(f"int {symbol.name} = {vm.get_int(symbol.addr)}")
            elif symbol.var_type == "char":
                self.output.write(f"char {symbol.name} = {vm.get_char(symbol.addr)}")
            elif symbol.var_type in ("int*", "char*"):
                ptr = vm.get_ptr(symbol.addr)
                ptr_text = "NULL" if ptr == 0 else f"0x{ptr:04x}"
                self.output.write(f"{symbol.var_type} {symbol.name} = {ptr_text}")

    def show_funcs(self) -> None:
        functions = list(self.runtime.symtable.iter_functions())
        if not functions:
            self.output.write("No user functions loaded in the current runtime.")
        for function in functions:
            params = []
            for param in function.params:
                suffix = "[]" if param.is_array else ""
                params.append(f"{param.var_type} {param.name}{suffix}")
            self.output.write(f"{function.return_type} {function.name}({', '.join(params)}) line {function.line}")
        self.output.write("--- built-in functions ---")
        for name, signature in interpreter.BUILTIN_SIGNATURES.items():
            self.output.write(f"{signature['return_type']} {name}(...) [built-in]")

    def show_help(self) -> None:
        self.output.write("[bold]Commands[/]")
        self.output.write("RUN | CHECK | LOAD <file> | SAVE [file] | NEW | LIST | VARS | FUNCS")
        self.output.write("TRACE ON | TRACE OFF | CLEAR | HELP | QUIT")
        self.output.write("Hotkeys: F5 RUN, F6 CHECK, Ctrl+S SAVE, Ctrl+O LOAD, Ctrl+N NEW, Ctrl+L CLEAR")

    def execute_command(self, command_line: str) -> None:
        command_line = command_line.strip()
        if command_line == "":
            return
        command, _, args = command_line.partition(" ")
        command = command.upper()
        args = args.strip()

        if command == "RUN":
            self.run_program()
        elif command == "CHECK":
            self.check_program()
        elif command == "LOAD":
            if not args:
                self.output.write("[bold yellow]Usage: LOAD <filename>[/]")
            else:
                self.load_file(args)
        elif command == "SAVE":
            self.save_file(args or None)
        elif command == "NEW":
            self.action_new_buffer()
        elif command == "LIST":
            self.list_buffer()
        elif command == "VARS":
            self.show_vars()
        elif command == "FUNCS":
            self.show_funcs()
        elif command == "TRACE":
            if args.upper() == "ON":
                self.trace_enabled = True
                self.output.write("[green]Trace mode enabled.[/]")
            elif args.upper() == "OFF":
                self.trace_enabled = False
                self.output.write("[green]Trace mode disabled.[/]")
            else:
                self.output.write("[bold yellow]Usage: TRACE ON|OFF[/]")
            self.update_status()
        elif command == "CLEAR":
            self.output.clear()
        elif command == "HELP":
            self.show_help()
        elif command in ("QUIT", "EXIT"):
            self.exit()
        else:
            self.output.write(f"[bold red]Unknown command: {command_line}[/]")

    @on(Input.Submitted, "#command")
    def on_command_submitted(self, event: Input.Submitted) -> None:
        command_line = event.value
        self.output.write(f"[#8fb7ff]> {command_line}[/]")
        self.command_input.value = ""
        self.execute_command(command_line)

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if event.text_area is self.editor:
            self.dirty = True
            self.update_status()


if __name__ == "__main__":
    SmallCTuiApp().run()
