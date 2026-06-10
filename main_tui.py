import contextlib
import io
import os
from pathlib import Path

try:
    from textual import events, on
    from textual.app import App, ComposeResult
    from textual.binding import Binding
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
import repl


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


class TripleMega(App):
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

    #splitter {
        width: 1;
        height: 100%;
        background: #4f6f8f;
        color: #d7dde5;
    }

    #splitter:hover {
        background: #78a6d8;
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
        Binding("f5", "run_program", "Run", priority=True),
        Binding("f6", "check_program", "Check", priority=True),
        Binding("ctrl+s", "save_prompt", "Save", priority=True),
        Binding("ctrl+o", "load_prompt", "Load", priority=True),
        Binding("ctrl+n", "new_buffer", "New", priority=True),
        Binding("ctrl+l", "clear_output", "Clear", priority=True),
        Binding("ctrl+left", "narrow_editor", "Narrow", priority=True),
        Binding("ctrl+right", "widen_editor", "Widen", priority=True),
        Binding("ctrl+q", "quit", "Quit", priority=True),
    ]

    def __init__(self):
        super().__init__()
        self.macro_definitions = {}
        self.runtime = interpreter.Interpreter()
        self.trace_enabled = False
        self.current_file: str | None = None
        self.dirty = False
        self.buffer_input_mode: str | None = None
        self.buffer_insert_index = 0
        self.left_pane_ratio = 58
        self.dragging_splitter = False

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="root"):
            yield Static("Triple Mega TUI  |  F5 RUN  F6 CHECK  Ctrl+S SAVE  Ctrl+O LOAD", id="title-line")
            with Horizontal(id="workspace"):
                with Vertical(id="left-pane"):
                    yield Static("BUFFER", classes="pane-title")
                    yield create_smallc_editor()
                yield Static("│", id="splitter")
                with Vertical(id="right-pane"):
                    yield Static("OUTPUT", classes="pane-title")
                    yield RichLog(id="output", wrap=True, highlight=True, markup=True)
            yield Static("", id="status")
        yield Input(placeholder="sc> command or Small-C single line", id="command")
        yield Footer()

    def on_mount(self) -> None:
        self.output.write("[bold #b8d7ff]Triple Mega Small-C Interactive Interpreter TUI[/]")
        self.output.write("Type HELP for commands. Enter Small-C single lines at sc>; they are not added to BUFFER.")
        self.apply_pane_ratio()
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

    @property
    def left_pane(self) -> Vertical:
        return self.query_one("#left-pane", Vertical)

    @property
    def right_pane(self) -> Vertical:
        return self.query_one("#right-pane", Vertical)

    @property
    def splitter(self) -> Static:
        return self.query_one("#splitter", Static)

    def buffer(self) -> list[str]:
        text = self.editor.text
        if text == "":
            return []
        return text.splitlines()

    def set_buffer(self, lines: list[str], dirty: bool = False) -> None:
        self.editor.load_text("\n".join(lines))
        self.dirty = dirty
        self.update_status()

    def apply_pane_ratio(self) -> None:
        self.left_pane_ratio = max(25, min(75, self.left_pane_ratio))
        self.left_pane.styles.width = f"{self.left_pane_ratio}%"
        self.right_pane.styles.width = f"{100 - self.left_pane_ratio}%"

    def action_narrow_editor(self) -> None:
        self.left_pane_ratio -= 5
        self.apply_pane_ratio()

    def action_widen_editor(self) -> None:
        self.left_pane_ratio += 5
        self.apply_pane_ratio()

    def update_status(self) -> None:
        filename = self.current_file or "<untitled>"
        dirty = "modified" if self.dirty else "saved"
        trace = "on" if self.trace_enabled else "off"
        lines = len(self.buffer())
        mode = f" | mode: {self.buffer_input_mode}" if self.buffer_input_mode else ""
        self.query_one("#status", Static).update(
            f"file: {filename} | lines: {lines} | trace: {trace} | state: {dirty}{mode}"
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

    def on_mouse_down(self, event: events.MouseDown) -> None:
        if event.widget is self.splitter:
            self.dragging_splitter = True
            self.splitter.capture_mouse()
            event.stop()

    def on_mouse_move(self, event: events.MouseMove) -> None:
        if not self.dragging_splitter:
            return
        workspace = self.query_one("#workspace", Horizontal)
        width = max(1, workspace.size.width - 1)
        offset = max(0, min(width, int(event.screen_x - workspace.region.x)))
        self.left_pane_ratio = round((offset / width) * 100)
        self.apply_pane_ratio()
        event.stop()

    def on_mouse_up(self, event: events.MouseUp) -> None:
        if self.dragging_splitter:
            self.dragging_splitter = False
            self.splitter.release_mouse()
            event.stop()

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

    def run_inline_code(self, source_line: str) -> None:
        try:
            source = source_line.rstrip("\n") + "\n"
            program = smallc_main.analyze_program(source, self.macro_definitions, line_start=1)
            _, text = self.capture(self.evaluate_inline_program, program)
            self.write_output(text)
        except interpreter.ExitSignal as signal:
            self.output.write(f"Program exited with return value {signal.code}.")
        except Exception as exc:
            self.report_exception(exc)
        self.update_status()

    def evaluate_inline_program(self, program: list) -> None:
        for ast in program:
            self.runtime.evaluate(ast)

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

    def list_buffer(self, args: str = "") -> None:
        lines = self.buffer()
        if not lines:
            self.output.write("[yellow]Program buffer is empty.[/]")
            return
        try:
            selected = smallc_main.parse_line_args(args, "LIST", allow_empty=True, allow_range=True)
        except Exception as exc:
            self.report_exception(exc)
            return
        if len(selected) == 0:
            start, end = 1, len(lines)
        elif len(selected) == 1:
            start = end = selected[0]
        else:
            start, end = selected
        if start < 1 or end > len(lines) or start > end:
            self.output.write(f"[bold red]REPL error: Index out of bounds. Valid range is 1 to {len(lines)}[/]")
            return
        for index in range(start, end + 1):
            line = lines[index - 1]
            self.output.write(f"{index:>4}: {line}")

    def append_line(self, raw_args: str) -> None:
        if raw_args.strip() == "":
            self.start_append_mode()
            return
        lines = self.buffer()
        lines.append(raw_args)
        self.set_buffer(lines, dirty=True)
        self.output.write(f"[green]Appended line {len(lines)}.[/]")

    def start_append_mode(self) -> None:
        self.buffer_input_mode = "append"
        self.buffer_insert_index = len(self.buffer()) + 1
        self.command_input.placeholder = "APPEND mode: enter code lines, '.' to finish"
        self.output.write("[green]APPEND mode. Enter a single '.' to finish.[/]")
        self.output.write(f"{self.buffer_insert_index}> ")
        self.update_status()

    def start_insert_mode(self, line_number: int) -> None:
        lines = self.buffer()
        if line_number < 1 or line_number > len(lines) + 1:
            self.output.write(f"[bold red]REPL error: Index {line_number} out of bounds. Valid range is 1 to {len(lines) + 1}[/]")
            return
        self.buffer_input_mode = "insert"
        self.buffer_insert_index = line_number
        self.command_input.placeholder = "INSERT mode: enter code lines, '.' to finish"
        self.output.write(f"[green]INSERT mode before line {line_number}. Enter a single '.' to finish.[/]")
        self.output.write(f"{self.buffer_insert_index}> ")
        self.update_status()

    def finish_buffer_input_mode(self) -> None:
        mode = self.buffer_input_mode
        self.buffer_input_mode = None
        self.buffer_insert_index = 0
        self.command_input.placeholder = "sc> command or Small-C single line"
        self.output.write(f"[green]{mode.upper()} mode finished.[/]" if mode else "[green]Input mode finished.[/]")
        self.update_status()

    def handle_buffer_input_line(self, line: str) -> None:
        if line.strip() == ".":
            self.finish_buffer_input_mode()
            return
        lines = self.buffer()
        if self.buffer_input_mode == "append":
            lines.append(line)
            shown_line = len(lines)
            self.buffer_insert_index = len(lines) + 1
        elif self.buffer_input_mode == "insert":
            lines.insert(self.buffer_insert_index - 1, line)
            shown_line = self.buffer_insert_index
            self.buffer_insert_index += 1
        else:
            return
        self.set_buffer(lines, dirty=True)
        self.output.write(f"{shown_line}> {line}")
        self.output.write(f"{self.buffer_insert_index}> ")

    def insert_line(self, raw_args: str) -> None:
        line_text = raw_args.lstrip()
        line_number_text, sep, code = line_text.partition(" ")
        if not line_number_text.isdigit():
            self.output.write("[bold yellow]Usage: INSERT <n> [code][/]")
            return
        line_number = int(line_number_text)
        if not sep:
            self.start_insert_mode(line_number)
            return
        lines = self.buffer()
        if line_number < 1 or line_number > len(lines) + 1:
            self.output.write(f"[bold red]REPL error: Index {line_number} out of bounds. Valid range is 1 to {len(lines) + 1}[/]")
            return
        lines.insert(line_number - 1, code)
        self.set_buffer(lines, dirty=True)
        self.output.write(f"[green]Inserted line {line_number}.[/]")

    def edit_line(self, raw_args: str) -> None:
        line_text = raw_args.lstrip()
        line_number_text, sep, code = line_text.partition(" ")
        if not line_number_text.isdigit():
            self.output.write("[bold yellow]Usage: EDIT <n> [code][/]")
            return
        line_number = int(line_number_text)
        lines = self.buffer()
        if line_number < 1 or line_number > len(lines):
            self.output.write(f"[bold red]REPL error: Index {line_number} out of bounds. Valid range is 1 to {len(lines)}[/]")
            return
        if not sep:
            self.output.write(f"{line_number:>4}: {lines[line_number - 1]}")
            self.command_input.value = f"EDIT {line_number} {lines[line_number - 1]}"
            self.command_input.focus()
            return
        old = lines[line_number - 1]
        lines[line_number - 1] = code
        self.set_buffer(lines, dirty=True)
        self.output.write(f"[green]Edited line {line_number}.[/] {old} -> {code}")

    def delete_lines(self, args: str) -> None:
        lines = self.buffer()
        if not lines:
            self.output.write("[bold red]REPL error: Program buffer is empty.[/]")
            return
        try:
            selected = smallc_main.parse_line_args(args, "DELETE", allow_empty=False, allow_range=True)
        except Exception as exc:
            self.report_exception(exc)
            return
        start = selected[0]
        end = selected[-1]
        if start < 1 or end > len(lines) or start > end:
            self.output.write(f"[bold red]REPL error: Index out of bounds. Valid range is 1 to {len(lines)}[/]")
            return
        del lines[start - 1:end]
        self.set_buffer(lines, dirty=True)
        self.output.write(f"[green]Deleted line {start}.[/]" if start == end else f"[green]Deleted lines {start}-{end}.[/]")

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

    def show_help(self, args: str = "") -> None:
        if args:
            _, text = self.capture(repl.HELP, args)
            self.write_output(text)
            return
        self.output.write("[bold]Commands[/]")
        self.output.write("RUN | CHECK | LOAD <file> | SAVE [file] | NEW | LIST [n|n1-n2]")
        self.output.write("APPEND [code] | INSERT <n> [code] | EDIT <n> [code] | DELETE <n|n1-n2>")
        self.output.write("TRACE ON | TRACE OFF | VARS | FUNCS | ABOUT | CLEAR | HELP [cmd] | QUIT")
        self.output.write("Small-C single lines entered at sc> execute immediately and are not added to BUFFER.")
        self.output.write("Hotkeys: F5 RUN, F6 CHECK, Ctrl+S SAVE, Ctrl+O LOAD, Ctrl+N NEW, Ctrl+L CLEAR, Ctrl+Left/Right resize")

    def show_about(self) -> None:
        _, text = self.capture(repl.ABOUT)
        self.write_output(text)

    def is_environment_command(self, command: str) -> bool:
        return command in {
            "RUN",
            "CHECK",
            "LOAD",
            "SAVE",
            "NEW",
            "LIST",
            "APPEND",
            "INSERT",
            "EDIT",
            "DELETE",
            "VARS",
            "FUNCS",
            "TRACE",
            "CLEAR",
            "HELP",
            "ABOUT",
            "QUIT",
            "EXIT",
        }

    def execute_command(self, command_line: str) -> None:
        command_text = command_line.lstrip()
        if command_text.strip() == "":
            return
        command, _, raw_args = command_text.partition(" ")
        command = command.upper()
        args = raw_args.strip()

        if not self.is_environment_command(command):
            self.run_inline_code(command_line)
        elif command == "RUN":
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
            self.list_buffer(args)
        elif command == "APPEND":
            self.append_line(raw_args)
        elif command == "INSERT":
            self.insert_line(raw_args)
        elif command == "EDIT":
            self.edit_line(raw_args)
        elif command == "DELETE":
            self.delete_lines(args)
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
            self.show_help(args)
        elif command == "ABOUT":
            self.show_about()
        elif command in ("QUIT", "EXIT"):
            self.exit()

    @on(Input.Submitted, "#command")
    def on_command_submitted(self, event: Input.Submitted) -> None:
        command_line = event.value
        self.output.write(f"[#8fb7ff]sc> {command_line}[/]")
        self.command_input.value = ""
        if self.buffer_input_mode:
            self.handle_buffer_input_line(command_line)
            return
        self.execute_command(command_line)

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if event.text_area is self.editor:
            self.dirty = True
            self.update_status()


SmallCTuiApp = TripleMega


if __name__ == "__main__":
    TripleMega().run()
