"""Crypto MLP Analyzer 测试"""
import unittest


class TestCryptoAnalyzer(unittest.TestCase):
    """加密货币分析器测试"""

    def test_import(self):
        """测试导入"""
        from ..analyzer import CryptoAnalyzer
        self.assertIsNotNone(CryptoAnalyzer)

    def test_initialization(self):
        """测试初始化"""
        from ..analyzer import CryptoAnalyzer
        analyzer = CryptoAnalyzer(symbol="BTC")
        self.assertEqual(analyzer.symbol, "BTC")


if __name__ == "__main__":
    unittest.main()
