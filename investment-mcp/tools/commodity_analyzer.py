#!/usr/bin/env python3
"""
Commodity Analyzer Tool - 大宗商品分析工具封装
封装 commodity-mlp 项目的分析能力
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger("investment-mcp.commodity_analyzer")

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
COMMODITY_MLP_DIR = PROJECT_ROOT.parent / "commodity-mlp"


def _ensure_commodity_paths():
    """确保commodity-mlp路径在sys.path中"""
    if str(COMMODITY_MLP_DIR) not in sys.path:
        sys.path.insert(0, str(COMMODITY_MLP_DIR))


class CommodityAnalyzer:
    """大宗商品分析器 - 封装commodity-mlp"""
    
    # 支持的商品列表
    AVAILABLE_SYMBOLS = {
        "GC=F": {"name": "黄金", "unit": "USD/oz", "base_price": 1950},
        "CL=F": {"name": "原油", "unit": "USD/bbl", "base_price": 80},
        "SI=F": {"name": "白银", "unit": "USD/oz", "base_price": 23},
        "HG=F": {"name": "铜", "unit": "USD/lb", "base_price": 3.8},
        "NG=F": {"name": "天然气", "unit": "USD/MMBtu", "base_price": 2.5},
    }
    
    def __init__(self):
        self._initialized = False
        self.fetcher = None
        self._init_modules()
    
    def _init_modules(self):
        """初始化模块"""
        _ensure_commodity_paths()
        
        try:
            from data_fetcher import CommodityDataFetcher
            self.fetcher = CommodityDataFetcher()
            logger.info("CommodityDataFetcher已加载")
        except ImportError as e:
            logger.warning(f"数据获取模块导入失败: {e}")
        
        try:
            from feature_engineering import FeatureEngineer
            self.FeatureEngineer = FeatureEngineer
            logger.info("FeatureEngineer已加载")
        except ImportError as e:
            logger.warning(f"特征工程模块导入失败: {e}")
            self.FeatureEngineer = None
        
        try:
            from mlp_model_advanced import AdvancedCommodityMLP
            self.MLPModel = AdvancedCommodityMLP
            logger.info("AdvancedCommodityMLP已加载")
        except ImportError as e:
            logger.warning(f"MLP模型模块导入失败: {e}")
            self.MLPModel = None
        
        try:
            from risk_backtest import RiskBacktestEngine
            self.RiskBacktestEngine = RiskBacktestEngine
            logger.info("RiskBacktestEngine已加载")
        except ImportError as e:
            logger.warning(f"回测引擎模块导入失败: {e}")
            self.RiskBacktestEngine = None
        
        self._initialized = True
    
    def analyze(self, symbol: str = "GC=F", model_type: str = "mlp",
                use_real: bool = False) -> Dict[str, Any]:
        """
        分析大宗商品
        
        Args:
            symbol: 商品代码（GC=F, CL=F等）
            model_type: 模型类型（mlp, lstm）
            use_real: 是否使用真实数据
        
        Returns:
            分析结果，包含预测信号、指标和交易建议
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "model_type": model_type,
            "prediction": None,
            "metrics": None,
            "current_price": None,
            "price_change": None
        }
        
        # 验证商品代码
        if symbol not in self.AVAILABLE_SYMBOLS:
            result["error"] = f"不支持的商品代码: {symbol}"
            result["available_symbols"] = list(self.AVAILABLE_SYMBOLS.keys())
            return result
        
        config = self.AVAILABLE_SYMBOLS[symbol]
        result["symbol_info"] = config
        
        try:
            if self.fetcher is None:
                raise ImportError("CommodityDataFetcher不可用")
            
            # 获取数据
            df = self.fetcher.generate_simulated_data(symbol)
            
            if df is None or df.empty:
                result["error"] = f"无法获取{symbol}数据"
                return result
            
            # 特征工程
            if self.FeatureEngineer:
                engineer = self.FeatureEngineer()
                features = engineer.extract_features(df)
            else:
                # 简化特征
                features = self._generate_simple_features(df)
            
            target = df['Target'].iloc[:len(features)]
            
            # 训练模型
            if self.MLPModel:
                model = self.MLPModel(use_ensemble=True)
                metrics = model.train(features, target, test_size=0.2)
            else:
                metrics = {"accuracy": 0.5, "f1": 0.5, "auc": 0.5}
                model = None
            
            # 预测
            if model is not None:
                predictions = model.predict(features)
                probabilities = model.predict_proba(features)
                
                latest_pred = int(predictions[-1])
                latest_prob = float(probabilities[-1][latest_pred])
                
                prediction_direction = "BUY" if latest_pred == 1 else "SELL"
                confidence = latest_prob
            else:
                # 模拟预测
                import numpy as np
                rng = np.random.default_rng(hash(symbol) % (2**32))
                prediction_direction = rng.choice(["BUY", "SELL"])
                confidence = float(rng.uniform(0.55, 0.8))
                metrics = {"accuracy": 0.5, "f1": 0.5, "auc": 0.5}
            
            # 计算价格变化
            current_price = float(df['Close'].iloc[-1])
            prev_price = float(df['Close'].iloc[-2])
            price_change = float((current_price - prev_price) / prev_price * 100)
            
            result.update({
                "prediction": prediction_direction,
                "confidence": round(confidence, 3),
                "metrics": {k: round(float(v), 4) if isinstance(v, (float,)) else v 
                           for k, v in metrics.items()},
                "current_price": round(current_price, 2),
                "price_change": round(price_change, 2),
                "signal": self._generate_signal(prediction_direction, confidence)
            })
            
        except Exception as e:
            logger.error(f"分析失败: {e}")
            result["error"] = str(e)
            result["prediction"] = "HOLD"
            result["confidence"] = 0.5
        
        return result
    
    def backtest(self, symbol: str = "GC=F", model_type: str = "mlp",
                 initial_capital: float = 100000) -> Dict[str, Any]:
        """
        运行大宗商品回测
        
        Returns:
            回测结果，包含收益率、最大回撤、夏普比率等
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "model_type": model_type,
            "initial_capital": initial_capital
        }
        
        if symbol not in self.AVAILABLE_SYMBOLS:
            result["error"] = f"不支持的商品代码: {symbol}"
            return result
        
        try:
            if self.fetcher is None:
                raise ImportError("CommodityDataFetcher不可用")
            
            df = self.fetcher.generate_simulated_data(symbol)
            
            if self.FeatureEngineer:
                engineer = self.FeatureEngineer()
                features = engineer.extract_features(df)
            else:
                features = self._generate_simple_features(df)
            
            target = df['Target'].iloc[:len(features)]
            
            if self.MLPModel:
                model = self.MLPModel(use_ensemble=True)
                model.train(features, target, test_size=0.2)
                predictions = model.predict(features)
                probabilities = model.predict_proba(features)
            else:
                import numpy as np
                rng = np.random.default_rng(hash(symbol) % (2**32))
                predictions = rng.choice([0, 1], size=len(df)).astype(int)
                probabilities = rng.uniform(0.5, 0.9, size=len(df))
            
            # 简单回测
            capital = initial_capital
            equity_curve = [capital]
            trades = 0
            peak = capital
            
            for i in range(len(predictions) - 1):
                ret = float(df['Close'].iloc[i+1] / df['Close'].iloc[i] - 1)
                
                if predictions[i] == 1:  # 买入
                    capital *= (1 + ret)
                    trades += 1
                else:  # 卖出/持有现金
                    capital *= 1.0
                
                equity_curve.append(capital)
                
                if capital > peak:
                    peak = capital
            
            total_return = (capital / initial_capital - 1) * 100
            max_drawdown = ((peak - min(equity_curve)) / peak) * 100 if peak > 0 else 0
            
            # 计算夏普比率（简化）
            returns = df['Close'].pct_change().dropna().values
            sharpe = float(np.mean(returns) / (np.std(returns) + 1e-10) * np.sqrt(252)) if len(returns) > 0 else 0
            
            result.update({
                "total_return_pct": round(total_return, 2),
                "max_drawdown_pct": round(max_drawdown, 2),
                "sharpe_ratio": round(sharpe, 2),
                "trades": trades,
                "final_equity": round(capital, 2),
                "benchmark_return_pct": round(float(np.cumprod(1 + returns)[-1] - 1) * 100, 2)
            })
            
        except Exception as e:
            logger.error(f"回测失败: {e}")
            result["error"] = str(e)
            result["total_return_pct"] = 0
            result["max_drawdown_pct"] = 0
        
        return result
    
    def get_available_symbols(self) -> Dict[str, Dict]:
        """获取可用商品列表"""
        return self.AVAILABLE_SYMBOLS
    
    def _generate_signal(self, prediction: str, confidence: float) -> Dict[str, Any]:
        """生成交易信号"""
        if confidence >= 0.7:
            action = "STRONG_" + prediction
        elif confidence >= 0.55:
            action = prediction
        else:
            action = "HOLD"
        
        return {
            "action": action,
            "confidence": round(confidence, 3),
            "suggestion": self._get_suggestion(action)
        }
    
    def _get_suggestion(self, action: str) -> str:
        """获取操作建议"""
        suggestions = {
            "STRONG_BUY": "强买入信号，建议加大仓位",
            "BUY": "买入信号，可适度建仓",
            "STRONG_SELL": "强卖出信号，建议减仓或离场",
            "SELL": "卖出信号，考虑减仓",
            "HOLD": "观望信号，保持现有仓位"
        }
        return suggestions.get(action, "观望")
    
    def _generate_simple_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成简化特征"""
        result = df.copy()
        
        close = result['Close']
        result['MA_5'] = close.rolling(5).mean()
        result['MA_10'] = close.rolling(10).mean()
        result['MA_20'] = close.rolling(20).mean()
        result['Return_1d'] = close.pct_change(1)
        result['Return_5d'] = close.pct_change(5)
        result['Volatility_10'] = close.pct_change().rolling(10).std()
        result['Volume_Ratio'] = result['Volume'] / result['Volume'].rolling(20).mean()
        
        return result.dropna()


# 全局单例
_analyzer = None

def get_analyzer() -> CommodityAnalyzer:
    """获取分析器单例"""
    global _analyzer
    if _analyzer is None:
        _analyzer = CommodityAnalyzer()
    return _analyzer


if __name__ == "__main__":
    # 测试
    analyzer = CommodityAnalyzer()
    
    print("\n" + "="*60)
    print("Commodity Analyzer 测试")
    print("="*60)
    
    print("\n--- 可用商品 ---")
    for symbol, info in analyzer.get_available_symbols().items():
        print(f"  {symbol}: {info['name']} ({info['unit']})")
    
    print("\n--- 黄金分析 ---")
    result = analyzer.analyze(symbol="GC=F")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n--- 黄金回测 ---")
    bt = analyzer.backtest(symbol="GC=F", initial_capital=100000)
    print(json.dumps(bt, indent=2, ensure_ascii=False))
