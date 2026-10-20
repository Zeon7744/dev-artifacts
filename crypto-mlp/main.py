"""Crypto MLP 加密货币分析系统入口"""
import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Crypto MLP 加密货币分析系统")
    parser.add_argument("--symbol", default="BTC", help="交易对符号 (默认: BTC)")
    parser.add_argument("--days", type=int, default=30, help="预测天数 (默认: 30)")
    parser.add_argument("--model", default="ensemble", choices=["mlp", "lstm", "ensemble"], help="模型类型")
    args = parser.parse_args()
    
    print(f"Crypto MLP 系统启动")
    print(f"交易对: {args.symbol}")
    print(f"预测天数: {args.days}")
    print(f"模型: {args.model}")
    
    # 导入并运行分析器
    try:
        from .analyzer import CryptoAnalyzer
        analyzer = CryptoAnalyzer(symbol=args.symbol)
        print(f"分析器初始化成功")
    except ImportError as e:
        print(f"导入错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
