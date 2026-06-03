"""
test_helpers.py - 測試共用輔助函式
由各測試檔案 import 使用。
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lexer as lexer_mod
import parser as parser_mod
import interpreter as interp_mod


def _run_code(interp_instance, code: str):
    """在已有的 Interpreter 實例上執行一段 C 程式碼片段。"""
    tokens = lexer_mod.lexer(code + "\n", {}).tokenize()
    asts = parser_mod.parser(tokens).parse()
    for ast in asts:
        interp_instance.evaluate(ast)


def _get_int(interp_instance, name: str) -> int:
    """從 Interpreter 符號表讀取整數變數的當前值。"""
    sym = interp_instance.symtable.lookup_var(name)
    return interp_instance.memory.get_int(sym.addr)


def _get_char(interp_instance, name: str) -> int:
    """從 Interpreter 符號表讀取 char 變數的當前值（回傳整數碼）。"""
    sym = interp_instance.symtable.lookup_var(name)
    return interp_instance.memory.get_char(sym.addr)


def _filter_debug(text: str) -> str:
    """過濾 'func call:' debug 輸出（interpreter.py 的開發用 print）。"""
    return "\n".join(
        line for line in text.splitlines()
        if not line.startswith("func call:")
    )
