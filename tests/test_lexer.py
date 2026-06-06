"""
test_lexer.py - 測試 Lexer 的錯誤處理
涵蓋浮點數、未閉合字串/字元、非法字元等 Syntax Error。
"""
import pytest
import lexer as lexer_mod


class TestLexerKeywords:
    """測試新增控制流程關鍵字是否會被辨識為 keyword。"""

    def test_switch_case_default_are_keywords(self):
        tokens = lexer_mod.lexer("switch (x) { case 1: default: ; }\n", {}).tokenize()
        keyword_values = [token.value for token in tokens if token.type == lexer_mod.token_type.keyword]
        assert "switch" in keyword_values
        assert "case" in keyword_values
        assert "default" in keyword_values


class TestLexerErrors:
    """測試 Lexer 在非法輸入時拋出含描述訊息的例外。"""

    def _tokenize(self, code: str):
        return lexer_mod.lexer(code + "\n", {}).tokenize()

    def test_float_constant_raises(self):
        with pytest.raises(Exception) as exc:
            self._tokenize("int x = 1.5;")
        assert "Floating-point" in str(exc.value) or "float" in str(exc.value).lower()

    def test_unterminated_string_raises(self):
        with pytest.raises(Exception) as exc:
            self._tokenize('"hello')
        assert "Unterminated string" in str(exc.value) or "unterminated" in str(exc.value).lower()

    def test_unterminated_char_literal_raises(self):
        with pytest.raises(Exception) as exc:
            self._tokenize("'a")
        assert "Unterminated character" in str(exc.value) or "unterminated" in str(exc.value).lower()

    def test_multichar_char_literal_raises(self):
        with pytest.raises(Exception) as exc:
            self._tokenize("'ab'")
        assert "character literal" in str(exc.value).lower() or "Invalid character" in str(exc.value)

    def test_unexpected_character_raises(self):
        with pytest.raises(Exception) as exc:
            self._tokenize("@")
        assert "Unexpected character" in str(exc.value) or "unexpected" in str(exc.value).lower()

    def test_unterminated_block_comment_raises(self):
        with pytest.raises(Exception) as exc:
            self._tokenize("/* unclosed")
        assert "Unterminated multi-line comment" in str(exc.value) or "comment" in str(exc.value).lower()
