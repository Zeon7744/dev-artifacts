#!/usr/bin/env python3
"""
Stock Analyzer MCP Server - 将金融分析工具包装为 MCP 协议兼容服务
"""

import json
import sys
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("警告: mcp 包未安装，请运行: pip install mcp")

sys.path.insert(0, str(Path(__file__).parent))
from tools import FinancialAnalyzer


def register_tools(mcp: "FastMCP") -> None:
    """注册金融分析工具"""
    
    @mcp.tool()
    def analyze_stock(symbol: str, period: str = "1y") -> str:
        """分析指定股票，返回完整分析报告（含 MLP 预测）
        
        Args:
            symbol: 股票代码，如 AAPL, 000001.SZ, 600519.SH
            period: 数据周期，默认 1y
        """
        try:
            analyzer = FinancialAnalyzer(symbol=symbol, period=period)
            report = analyzer.generate_report()
            return json.dumps(report, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    @mcp.tool()
    def save_analysis_report(symbol: str, output_path: str = None) -> str:
        """保存股票分析报告到文件
        
        Args:
            symbol: 股票代码
            output_path: 输出路径（可选）
        """
        try:
            analyzer = FinancialAnalyzer(symbol=symbol)
            path = analyzer.save_report(output_path)
            return json.dumps({"success": True, "path": path}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    @mcp.tool()
    def generate_stock_charts(symbol: str, output_dir: str = "charts") -> str:
        """生成股票分析图表
        
        Args:
            symbol: 股票代码
            output_dir: 输出目录
        """
        try:
            analyzer = FinancialAnalyzer(symbol=symbol)
            charts = analyzer.generate_charts(output_dir)
            return json.dumps({"success": True, "charts": charts}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    @mcp.tool()
    def get_stock_price(symbol: str) -> str:
        """获取股票实时价格
        
        Args:
            symbol: 股票代码
        """
        try:
            analyzer = FinancialAnalyzer(symbol=symbol)
            price_info = analyzer.get_price_info()
            return json.dumps(price_info, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    @mcp.tool()
    def compare_stocks(symbols: str) -> str:
        """比较多只股票的技术指标
        
        Args:
            symbols: 逗号分隔的股票代码列表，如 AAPL,GOOGL,MSFT
        """
        try:
            symbol_list = [s.strip().upper() for s in symbols.split(",")]
            results = []
            for sym in symbol_list:
                analyzer = FinancialAnalyzer(symbol=sym)
                price = analyzer.get_price_info()
                indicators = analyzer.calculate_indicators()
                results.append({
                    "symbol": sym,
                    "price": price,
                    "indicators": indicators
                })
            return json.dumps({"comparison": results}, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    return mcp


def run_server():
    """运行 MCP 服务器"""
    if not MCP_AVAILABLE:
        print("错误: 请先安装 mcp 包: pip install mcp")
        sys.exit(1)
    
    mcp = FastMCP("stock-analyzer")
    register_tools(mcp)
    mcp.run()


if __name__ == "__main__":
    run_server()
