#!/usr/bin/env python3
"""
Crypto Predictor Tool - 加密货币预测工具封装
封装 crypto-mlp 项目的预测和状态检测能力
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("investment-mcp.crypto_predictor")

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
CRYPTO_MLP_DIR = PROJECT_ROOT.parent / "crypto-mlp"


def _ensure_crypto_paths():
    """确保crypto-mlp路径在sys.path中"""
    if str(CRYPTO_MLP_DIR) not in sys.path:
        sys.path.insert(0, str(CRYPTO_MLP_DIR))


class CryptoPredictor:
    """加密货币预测器 - 封装crypto-mlp"""
    
    def __init__(self):
        self.analyzer = None
        self.regime_detector = None
        self._init_modules()
    
    def _init_modules(self):
        """初始化模块"""
        _ensure_crypto_paths()
        
        try:
            from advanced_analyzer import CryptoAdvancedAnalyzer
            self.AnalyzerClass = CryptoAdvancedAnalyzer
            logger.info("使用CryptoAdvancedAnalyzer")
        except ImportError:
            try:
                from crypto_mlp import CryptoMLPAnalyzer
                self.AnalyzerClass = CryptoMLPAnalyzer
                logger.info("使用CryptoMLPAnalyzer")
            except ImportError:
                self.AnalyzerClass = None
                logger.warning("crypto-mlp模块导入失败，将使用模拟数据")
        
        try:
            from regime_detector import CryptoRegimeDetector
            self.regime_detector_class = CryptoRegimeDetector
            logger.info("CryptoRegimeDetector已加载")
        except ImportError:
            self.regime_detector_class = None
            logger.warning("regime_detector模块导入失败")
    
    def predict(self, coin: str = "BTC", exchange: str = "binance", 
                timeframe: str = "4h", account_balance: float = 10000) -> Dict[str, Any]:
        """
        预测加密货币走势
        
        Returns:
            预测结果字典，包含方向、置信度、建议等操作信号
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "coin": coin.upper(),
            "exchange": exchange,
            "timeframe": timeframe,
            "prediction": None,
            "signal": None,
            "risk_metrics": None,
            "market_regime": None
        }
        
        if self.AnalyzerClass is None:
            logger.warning("未加载crypto-mlp分析器，返回模拟结果")
            return self._generate_simulated_result(coin, timeframe)
        
        try:
            analyzer = self.AnalyzerClass(
                coin=coin.upper(),
                exchange=exchange.lower(),
                timeframe=timeframe
            )
            
            analysis = analyzer.analyze(account_balance=account_balance)
            
            result.update({
                "prediction": analysis.get("prediction", {}),
                "signal": analysis.get("signal", {}),
                "risk_metrics": analysis.get("risk_metrics", {}),
                "market_regime": analysis.get("market_regime", {}),
                "current_price": analysis.get("current_price"),
                "price_change_24h": analysis.get("price_change_24h"),
                "training_stats": analysis.get("training_stats", {})
            })
            
        except Exception as e:
            logger.error(f"预测失败: {e}")
            result["error"] = str(e)
            result["prediction"] = {"prediction": "hold", "confidence": 0.5}
        
        return result
    
    def detect_regime(self, coin: str = "BTC", lookback: int = 60) -> Dict[str, Any]:
        """
        检测市场状态
        
        返回状态包括:
        - trending_up: 明确上涨趋势
        - trending_down: 明确下跌趋势
        - range_bound: 区间震荡
        - high_volatility: 高波动期
        - low_volatility: 低波动期
        - accumulation: 吸筹阶段
        - distribution: 派发阶段
        - uncertain: 状态不确定
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "coin": coin.upper(),
            "lookback": lookback
        }
        
        if self.regime_detector_class is None:
            logger.warning("未加载CryptoRegimeDetector，返回模拟结果")
            return self._generate_simulated_regime(coin)
        
        try:
            from data_fetcher import CryptoDataFetcher
            fetcher = CryptoDataFetcher()
            df = fetcher.fetch_ohlcv(coin, "4h", limit=min(int(lookback * 1.5), 500))
            
            detector = self.regime_detector_class(lookback=lookback)
            regime_result = detector.detect_regime(df)
            
            result.update(regime_result)
            result["context"] = detector.get_regime_context(df)
            result["strategy_adjustments"] = detector.adapt_strategy(
                regime_result.get("regime", "unknown")
            )
            
        except Exception as e:
            logger.error(f"状态检测失败: {e}")
            result["error"] = str(e)
            result["regime"] = "uncertain"
            result["confidence"] = 0.0
        
        return result
    
    def get_available_coins(self) -> list:
        """获取支持的加密货币列表"""
        return ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", 
                "MATIC", "AVAX", "DOT", "LINK", "UNI", "LTC", "ATOM", "FIL"]
    
    def _generate_simulated_result(self, coin: str, timeframe: str) -> Dict[str, Any]:
        """生成模拟预测结果（fallback）"""
        np_random_state = hash(coin + timeframe) % (2**32)
        import numpy as np
        rng = np.random.default_rng(np_random_state)
        
        base_price = 52000 if coin == "BTC" else 2800 if coin == "ETH" else 100
        price_change = float(rng.uniform(-5, 5))
        direction = "up" if price_change > 0 else "down"
        confidence = float(rng.uniform(0.6, 0.85))
        
        return {
            "timestamp": datetime.now().isoformat(),
            "coin": coin.upper(),
            "exchange": "binance",
            "timeframe": timeframe,
            "prediction": {
                "prediction": direction,
                "confidence": confidence,
                "probability_up": confidence if direction == "up" else (1 - confidence),
                "probability_down": (1 - confidence) if direction == "up" else confidence
            },
            "signal": {
                "action": "BUY" if direction == "up" and confidence > 0.7 else 
                          ("SELL" if direction == "down" and confidence > 0.7 else "HOLD"),
                "reason": f"模拟信号 - {direction.upper()}趋势，置信度{confidence:.0%}"
            },
            "risk_metrics": {
                "var_95": round(float(rng.uniform(2, 5)), 2),
                "max_drawdown": round(float(rng.uniform(5, 15)), 2),
                "sharpe_ratio": round(float(rng.uniform(0.5, 1.5)), 2),
                "risk_level": "medium"
            },
            "current_price": round(base_price * (1 + price_change/100), 2),
            "price_change_24h": round(price_change, 2)
        }
    
    def _generate_simulated_regime(self, coin: str) -> Dict[str, Any]:
        """生成模拟市场状态（fallback）"""
        import numpy as np
        rng = np.random.default_rng(hash(coin) % (2**32))
        
        regimes = ["trending_up", "trending_down", "range_bound", 
                   "high_volatility", "low_volatility", "accumulation", "distribution"]
        regime = rng.choice(regimes)
        confidence = float(rng.uniform(0.5, 0.85))
        
        context_map = {
            "trending_up": "上升趋势中，建议顺势操作，注意回调风险",
            "trending_down": "下降趋势中，建议观望或做空，严格控制仓位",
            "range_bound": "区间震荡，低买高卖策略，关注突破信号",
            "high_volatility": "高波动期，降低仓位，避免追涨杀跌",
            "low_volatility": "低波动期，可适度放大仓位，等待突破",
            "accumulation": "吸筹阶段，主力可能在建仓，关注放量突破",
            "distribution": "派发阶段，主力可能在出货，警惕冲高回落"
        }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "coin": coin.upper(),
            "regime": regime,
            "confidence": confidence,
            "context": context_map.get(regime, "未知状态"),
            "scores": {
                "trend_strength": round(float(rng.uniform(0.2, 0.8)), 2),
                "volatility_regime": "normal",
                "volume_confirmation": round(float(rng.uniform(0.4, 0.9)), 2)
            }
        }


# 全局单例
_predictor = None

def get_predictor() -> CryptoPredictor:
    """获取预测器单例"""
    global _predictor
    if _predictor is None:
        _predictor = CryptoPredictor()
    return _predictor


if __name__ == "__main__":
    # 测试
    predictor = CryptoPredictor()
    
    print("\n" + "="*60)
    print("Crypto Predictor 测试")
    print("="*60)
    
    print("\n--- 预测测试 ---")
    result = predictor.predict(coin="BTC", timeframe="4h")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    print("\n--- 状态检测测试 ---")
    regime = predictor.detect_regime(coin="BTC")
    print(json.dumps(regime, indent=2, ensure_ascii=False))
    
    print("\n--- 可用币种 ---")
    print(predictor.get_available_coins())
