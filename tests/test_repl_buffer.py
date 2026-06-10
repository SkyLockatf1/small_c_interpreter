"""
test_repl_buffer.py - 測試 repl.py buffer 管理指令與 main.py handle_* 整合
涵蓋 LIST、DELETE、SAVE、APPEND、INSERT、EDIT、handle_list/delete/insert。
"""
import os
import pytest
import repl
import main


class TestReplList:
    """測試 repl.LIST 的輸出格式與邊界錯誤。"""

    def test_list_empty_buffer_raises(self, buffer):
        with pytest.raises(Exception) as exc:
            repl.LIST(buffer, [])
        assert "empty" in str(exc.value).lower()

    def test_list_all_shows_all_lines(self, filled_buffer, capsys):
        repl.LIST(filled_buffer, [])
        out = capsys.readouterr().out
        assert "[1]:" in out
        assert "[5]:" in out
        assert "int x = 1;" in out
        assert "int v = 5;" in out

    def test_list_all_format_has_brackets(self, filled_buffer, capsys):
        repl.LIST(filled_buffer, [])
        out = capsys.readouterr().out
        for i in range(1, 6):
            assert f"[{i}]:" in out

    def test_list_single_line(self, filled_buffer, capsys):
        repl.LIST(filled_buffer, [3])
        out = capsys.readouterr().out
        assert "[3]:" in out
        assert "int z = 3;" in out
        assert "[1]:" not in out
        assert "[5]:" not in out

    def test_list_range(self, filled_buffer, capsys):
        repl.LIST(filled_buffer, [2, 4])
        out = capsys.readouterr().out
        assert "[2]:" in out
        assert "[3]:" in out
        assert "[4]:" in out
        assert "[1]:" not in out
        assert "[5]:" not in out

    def test_list_range_same_start_end(self, filled_buffer, capsys):
        repl.LIST(filled_buffer, [2, 2])
        out = capsys.readouterr().out
        assert "[2]:" in out
        assert "[1]:" not in out
        assert "[3]:" not in out

    def test_list_index_zero_raises(self, filled_buffer):
        with pytest.raises(Exception) as exc:
            repl.LIST(filled_buffer, [0])
        assert "bounds" in str(exc.value).lower()

    def test_list_index_too_large_raises(self, filled_buffer):
        with pytest.raises(Exception):
            repl.LIST(filled_buffer, [6])

    def test_list_range_start_greater_than_end_raises(self, filled_buffer):
        with pytest.raises(Exception) as exc:
            repl.LIST(filled_buffer, [3, 1])
        assert "Start index" in str(exc.value) or "start" in str(exc.value).lower()

    def test_list_range_start_out_of_bounds_raises(self, filled_buffer):
        with pytest.raises(Exception):
            repl.LIST(filled_buffer, [0, 3])

    def test_list_range_end_out_of_bounds_raises(self, filled_buffer):
        with pytest.raises(Exception):
            repl.LIST(filled_buffer, [2, 6])

    def test_list_single_line_buffer(self, capsys):
        buf = ["int x = 42;"]
        repl.LIST(buf, [])
        out = capsys.readouterr().out
        assert "[1]:" in out
        assert "int x = 42;" in out


class TestReplDelete:
    """測試 repl.DELETE 的刪除行為與後續 buffer 狀態。"""

    def test_delete_empty_buffer_raises(self, buffer):
        with pytest.raises(Exception) as exc:
            repl.DELETE(buffer, [1])
        assert "empty" in str(exc.value).lower()

    def test_delete_no_args_raises(self, filled_buffer):
        with pytest.raises(Exception):
            repl.DELETE(filled_buffer, [])

    def test_delete_single_line(self, filled_buffer):
        original_third = filled_buffer[2]  # "int z = 3;"
        repl.DELETE(filled_buffer, [2])
        assert len(filled_buffer) == 4
        assert "int y = 2;" not in filled_buffer
        assert filled_buffer[1] == original_third  # 原第3行上移成為新第2行

    def test_delete_first_line(self, filled_buffer):
        repl.DELETE(filled_buffer, [1])
        assert len(filled_buffer) == 4
        assert filled_buffer[0] == "int y = 2;"

    def test_delete_last_line(self, filled_buffer):
        repl.DELETE(filled_buffer, [5])
        assert len(filled_buffer) == 4
        assert "int v = 5;" not in filled_buffer

    def test_delete_range(self, filled_buffer):
        repl.DELETE(filled_buffer, [2, 4])
        assert len(filled_buffer) == 2
        assert filled_buffer[0] == "int x = 1;"
        assert filled_buffer[1] == "int v = 5;"

    def test_delete_range_entire_buffer(self, filled_buffer):
        repl.DELETE(filled_buffer, [1, 5])
        assert len(filled_buffer) == 0

    def test_delete_range_single_element(self, filled_buffer):
        repl.DELETE(filled_buffer, [3, 3])
        assert len(filled_buffer) == 4
        assert "int z = 3;" not in filled_buffer

    def test_delete_index_zero_raises(self, filled_buffer):
        with pytest.raises(Exception):
            repl.DELETE(filled_buffer, [0])

    def test_delete_index_too_large_raises(self, filled_buffer):
        with pytest.raises(Exception):
            repl.DELETE(filled_buffer, [6])

    def test_delete_range_reversed_raises(self, filled_buffer):
        with pytest.raises(Exception) as exc:
            repl.DELETE(filled_buffer, [4, 2])
        assert "Start index" in str(exc.value) or "start" in str(exc.value).lower()

    def test_delete_preserves_remaining_content(self, filled_buffer):
        repl.DELETE(filled_buffer, [3])
        assert filled_buffer == ["int x = 1;", "int y = 2;", "int w = 4;", "int v = 5;"]


class TestReplSave:
    """測試 repl.SAVE 的檔案寫入行為（使用 pytest tmp_path，跨平台自動清理）。"""

    def test_save_creates_file(self, filled_buffer, tmp_path):
        filepath = str(tmp_path / "output.c")
        repl.SAVE(filled_buffer, filepath)
        assert os.path.exists(filepath)

    def test_save_file_content_newline_joined(self, filled_buffer, tmp_path):
        filepath = str(tmp_path / "output.c")
        repl.SAVE(filled_buffer, filepath)
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        assert content == "\n".join(filled_buffer)

    def test_save_single_line_buffer(self, tmp_path):
        buf = ["int x = 99;"]
        filepath = str(tmp_path / "single.c")
        repl.SAVE(buf, filepath)
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        assert content == "int x = 99;"

    def test_save_prints_success_message(self, filled_buffer, tmp_path, capsys):
        filepath = str(tmp_path / "output.c")
        repl.SAVE(filled_buffer, filepath)
        out = capsys.readouterr().out
        assert "5" in out
        assert "output.c" in out or filepath in out

    def test_save_empty_buffer_raises(self, buffer, tmp_path):
        filepath = str(tmp_path / "empty.c")
        with pytest.raises(Exception) as exc:
            repl.SAVE(buffer, filepath)
        assert "empty" in str(exc.value).lower()

    def test_save_empty_filename_raises(self, filled_buffer):
        with pytest.raises(Exception) as exc:
            repl.SAVE(filled_buffer, "")
        assert "filename" in str(exc.value).lower() or "SAVE" in str(exc.value)

    def test_save_whitespace_filename_raises(self, filled_buffer):
        with pytest.raises(Exception):
            repl.SAVE(filled_buffer, "   ")

    def test_save_overwrites_existing_file(self, tmp_path):
        filepath = str(tmp_path / "existing.c")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("old content")
        repl.SAVE(["int new = 1;"], filepath)
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        assert content == "int new = 1;"
        assert "old content" not in content


class TestReplAppend:
    """測試 repl.APPEND 透過 monkeypatch 模擬多行輸入直到 '.'。"""

    def test_append_single_line(self, buffer, monkeypatch):
        inputs = iter(["int x = 1;", "."])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
        repl.APPEND(buffer)
        assert buffer == ["int x = 1;"]

    def test_append_multiple_lines(self, buffer, monkeypatch):
        inputs = iter(["int a = 1;", "int b = 2;", "int c = 3;", "."])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
        repl.APPEND(buffer)
        assert buffer == ["int a = 1;", "int b = 2;", "int c = 3;"]

    def test_append_immediate_dot_no_change(self, buffer, monkeypatch):
        inputs = iter(["."])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
        repl.APPEND(buffer)
        assert buffer == []

    def test_append_to_existing_buffer(self, filled_buffer, monkeypatch):
        inputs = iter(["int new1 = 6;", "int new2 = 7;", "."])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
        repl.APPEND(filled_buffer)
        assert len(filled_buffer) == 7
        assert filled_buffer[-2] == "int new1 = 6;"
        assert filled_buffer[-1] == "int new2 = 7;"

    def test_append_preserves_order(self, buffer, monkeypatch):
        lines = ["line_a", "line_b", "line_c"]
        inputs = iter(lines + ["."])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
        repl.APPEND(buffer)
        assert buffer == lines

    def test_append_preserves_indentation(self, buffer, monkeypatch):
        inputs = iter(["  int x;  ", "."])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
        repl.APPEND(buffer)
        assert buffer == ["  int x;  "]

    def test_append_prompts_with_next_line_numbers(self, filled_buffer, monkeypatch):
        prompts = []
        inputs = iter(["int new1 = 6;", "int new2 = 7;", "."])

        def fake_input(prompt=""):
            prompts.append(prompt)
            return next(inputs)

        monkeypatch.setattr("builtins.input", fake_input)
        repl.APPEND(filled_buffer)
        assert prompts == ["6> ", "7> ", "8> "]


class TestReplInsert:
    """測試 repl.INSERT 的插入位置、多行順序與邊界錯誤。"""

    def test_insert_at_beginning(self, filled_buffer, monkeypatch):
        inputs = iter(["int zero = 0;", "."])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
        repl.INSERT(filled_buffer, 1)
        assert filled_buffer[0] == "int zero = 0;"
        assert filled_buffer[1] == "int x = 1;"

    def test_insert_at_middle(self, filled_buffer, monkeypatch):
        inputs = iter(["int mid = 99;", "."])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
        repl.INSERT(filled_buffer, 3)
        assert filled_buffer[2] == "int mid = 99;"
        assert filled_buffer[3] == "int z = 3;"

    def test_insert_at_end(self, filled_buffer, monkeypatch):
        inputs = iter(["int tail = 6;", "."])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
        repl.INSERT(filled_buffer, len(filled_buffer) + 1)
        assert filled_buffer[-1] == "int tail = 6;"

    def test_insert_multiple_lines_order(self, filled_buffer, monkeypatch):
        inputs = iter(["first", "second", "third", "."])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
        repl.INSERT(filled_buffer, 2)
        assert filled_buffer[1] == "first"
        assert filled_buffer[2] == "second"
        assert filled_buffer[3] == "third"
        assert filled_buffer[4] == "int y = 2;"

    def test_insert_immediate_dot_no_change(self, filled_buffer, monkeypatch):
        original = filled_buffer.copy()
        inputs = iter(["."])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
        repl.INSERT(filled_buffer, 2)
        assert filled_buffer == original

    def test_insert_index_zero_raises(self, filled_buffer):
        with pytest.raises(Exception):
            repl.INSERT(filled_buffer, 0)

    def test_insert_index_too_large_raises(self, filled_buffer):
        with pytest.raises(Exception):
            repl.INSERT(filled_buffer, len(filled_buffer) + 2)

    def test_insert_into_empty_buffer_at_1(self, buffer, monkeypatch):
        inputs = iter(["int x = 1;", "."])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
        repl.INSERT(buffer, 1)
        assert buffer == ["int x = 1;"]

    def test_insert_preserves_indentation(self, filled_buffer, monkeypatch):
        inputs = iter(["    int indented = 1;  ", "."])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
        repl.INSERT(filled_buffer, 2)
        assert filled_buffer[1] == "    int indented = 1;  "

    def test_insert_prompts_with_inserted_line_numbers(self, filled_buffer, monkeypatch):
        prompts = []
        inputs = iter(["first", "second", "."])

        def fake_input(prompt=""):
            prompts.append(prompt)
            return next(inputs)

        monkeypatch.setattr("builtins.input", fake_input)
        repl.INSERT(filled_buffer, 3)
        assert prompts == ["3> ", "4> ", "5> "]


class TestReplEdit:
    """測試 repl.EDIT 的一次性 input 行為與邊界錯誤。"""

    def test_edit_replaces_line(self, filled_buffer, monkeypatch):
        inputs = iter(["int x = 999;"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
        repl.EDIT(filled_buffer, 1)
        assert filled_buffer[0] == "int x = 999;"

    def test_edit_empty_input_cancels(self, filled_buffer, monkeypatch):
        original_line = filled_buffer[2]
        inputs = iter([""])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
        repl.EDIT(filled_buffer, 3)
        assert filled_buffer[2] == original_line

    def test_edit_preserves_indentation(self, filled_buffer, monkeypatch):
        inputs = iter(["    printf(\"hi\\n\");"])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
        repl.EDIT(filled_buffer, 2)
        assert filled_buffer[1] == "    printf(\"hi\\n\");"

    def test_edit_shows_current_line_before_input(self, filled_buffer, monkeypatch, capsys):
        inputs = iter([""])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
        repl.EDIT(filled_buffer, 2)
        out = capsys.readouterr().out
        assert "2" in out
        assert "int y = 2;" in out

    def test_edit_index_zero_raises(self, filled_buffer):
        with pytest.raises(Exception):
            repl.EDIT(filled_buffer, 0)

    def test_edit_index_too_large_raises(self, filled_buffer):
        with pytest.raises(Exception):
            repl.EDIT(filled_buffer, 6)

    def test_edit_empty_buffer_raises(self, buffer):
        with pytest.raises(Exception) as exc:
            repl.EDIT(buffer, 1)
        assert "empty" in str(exc.value).lower()


class TestHandleIntegration:
    """測試 main.handle_list / handle_delete / handle_insert 的整合行為。"""

    def test_handle_list_no_args(self, filled_buffer, capsys):
        main.handle_list(filled_buffer, "")
        out = capsys.readouterr().out
        assert "[1]:" in out
        assert "[5]:" in out

    def test_handle_list_single_arg(self, filled_buffer, capsys):
        main.handle_list(filled_buffer, "2")
        out = capsys.readouterr().out
        assert "[2]:" in out
        assert "[1]:" not in out

    def test_handle_list_range_arg(self, filled_buffer, capsys):
        main.handle_list(filled_buffer, "2-4")
        out = capsys.readouterr().out
        assert "[2]:" in out
        assert "[4]:" in out
        assert "[1]:" not in out
        assert "[5]:" not in out

    def test_handle_list_invalid_format_raises(self, filled_buffer):
        with pytest.raises(Exception):
            main.handle_list(filled_buffer, "1,3")

    def test_handle_delete_single(self, filled_buffer):
        main.handle_delete(filled_buffer, "2")
        assert len(filled_buffer) == 4
        assert "int y = 2;" not in filled_buffer

    def test_handle_delete_range(self, filled_buffer):
        main.handle_delete(filled_buffer, "2-4")
        assert len(filled_buffer) == 2

    def test_handle_delete_no_args_raises(self, filled_buffer):
        with pytest.raises(Exception):
            main.handle_delete(filled_buffer, "")

    def test_handle_insert_calls_repl_insert(self, filled_buffer, monkeypatch):
        inputs = iter(["int new = 0;", "."])
        monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
        main.handle_insert(filled_buffer, "2")
        assert filled_buffer[1] == "int new = 0;"

    def test_handle_insert_range_raises(self, filled_buffer):
        with pytest.raises(Exception):
            main.handle_insert(filled_buffer, "1-3")
