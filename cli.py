#!/usr/bin/env python3
"""
Stock Analyzer CLI - 命令行入口
"""

import argparse
import json
import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from tools import FinancialAnalyzer


def main():
    parser = argparse.ArgumentParser(
        description="Stock Analyzer - MLP精准金融分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  stock-analyzer AAPL                    # 分析苹果股票
  stock-analyzer 000001.SZ              # 分析平安银行
  stock-analyzer AAPL --period 6m       # 分析最近6个月
  stock-analyzer AAPL --output report.json  # 保存报告
  stock-analyzer AAPL --charts          # 生成图表
        """
    )
    
    parser.add_argument("symbol", help="股票代码，如 AAPL, 000001.SZ, 600519.SH")
    parser.add_argument("--period", default="1y", help="数据周期 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)")
    parser.add_argument("--output", "-o", help="输出报告文件路径")
    parser.add_argument("--charts", "-c", action="store_true", help="生成图表")
    parser.add_argument("--json", "-j", action="store_true", help="以 JSON 格式输出")
    
    args = parser.parse_args()
    
    try:
        analyzer = FinancialAnalyzer(symbol=args.symbol, period=args.period)
        report = analyzer.generate_report()
        
        if args.output:
            path = analyzer.save_report(args.output)
            print(f"报告已保存到: {path}")
        
        if args.charts:
            charts = analyzer.generate_charts()
            print(f"图表已生成: {charts}")
        
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        else:
            print(f"\n{'='*50}")
            print(f"📊 {args.symbol} 股票分析报告")
            print(f"{'='*50}\n")
            
            # 价格信息
            price = report.get("price", {})
            print(f"当前价格: ${price.get('current', 'N/A')}")
            change = price.get('change_1d', 0)
            change_pct = price.get('change_pct', 0)
            color = "📈" if change >= 0 else "📉"
            print(f"日涨跌: {color} {change:+.2f} ({change_pct:+.2f}%)")
            print()
            
            # 技术指标
            indicators = report.get("indicators", {})
            print("📈 技术指标:")
            if "MA" in indicators:
                ma = indicators["MA"]
                print(f"   均线: MA5={ma.get('MA5', 'N/A'):.2f}, MA20={ma.get('MA20', 'N/A'):.2f}")
            if "RSI" in indicators:
                rsi = indicators["RSI"]
                status = "超买" if rsi > 70 else ("超卖" if rsi < 30 else "中性")
                print(f"   RSI: {rsi:.2f} ({status})")
            if "MACD" in indicators:
                macd = indicators["MACD"]
                print(f"   MACD: {macd:.4f}")
            if "BB" in indicators:
                bb = indicators["BB"]
                print(f"   布林带位置: {bb.get('position', 'N/A'):.2%}")
            print()
            
            # MLP预测
            ml = report.get("ml_prediction", {})
            if ml:
                print("🤖 MLP预测:")
                acc = ml.get("classifier_accuracy", 0)
                expected = ml.get("expected_5d_return_pct", 0)
                print(f"   预测准确率: {acc:.1%}")
                print(f"   5日预期收益: {expected:+.2f}%")
                print()
            
            # 投资建议
            advice = report.get("advice", {})
            if advice:
                print("💡 投资建议:")
                operation = advice.get("operation", "")
                risk = advice.get("risk_level", "")
                action_icon = "🟢" if operation == "买入" else ("🔴" if operation == "卖出" else "🟡")
                print(f"   操作建议: {action_icon} {operation}")
                print(f"   风险等级: {risk}")
                if advice.get("confidence"):
                    print(f"   置信度: {advice['confidence']:.1%}")
            print()
            
    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
