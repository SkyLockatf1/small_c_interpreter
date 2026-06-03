"""
conftest.py - pytest 共用 fixtures
自動被所有同目錄測試檔案載入。
"""
import sys
import os

# tests/ 的上一層才是專案根目錄（main.py、repl.py 等所在位置）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import interpreter as interp_mod


@pytest.fixture
def buffer():
    """每個測試獨享的空 buffer（list[str]）。"""
    return []


@pytest.fixture
def filled_buffer():
    """預填 5 行程式碼的 buffer，供需要有內容的測試使用。"""
    return [
        "int x = 1;",
        "int y = 2;",
        "int z = 3;",
        "int w = 4;",
        "int v = 5;",
    ]


@pytest.fixture
def fresh_interp():
    """
    每個測試獨立的全新 Interpreter 實例。
    使用 function scope 確保全域符號表在測試間不互相污染：
    同一實例中若重複宣告同名變數，interpreter 會拋出 'already defined' 例外。
    """
    return interp_mod.Interpreter()
