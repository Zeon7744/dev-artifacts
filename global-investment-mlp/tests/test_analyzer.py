"""Global Investment MLP Analyzer 测试"""
import unittest


class TestInvestmentAnalyzer(unittest.TestCase):
    """全球投资分析器测试"""

    def test_import(self):
        """测试导入"""
        from ..analyzer import InvestmentAnalyzer
        self.assertIsNotNone(InvestmentAnalyzer)

    def test_initialization(self):
        """测试初始化"""
        from ..analyzer import InvestmentAnalyzer
        analyzer = InvestmentAnalyzer(market="US")
        self.assertEqual(analyzer.market, "US")


if __name__ == "__main__":
    unittest.main()
