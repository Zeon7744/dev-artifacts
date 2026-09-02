"""
监控 Agent - 异常预警和实时监测
"""
import logging
import asyncio
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime, timedelta
import json

from .base_agent import BaseAgent, AgentContext

logger = logging.getLogger(__name__)


class WatcherAgent(BaseAgent):
    """
    监控 Agent
    
    职责：
    - 实时监控市场异常
    - 预警系统触发
    - 定时任务调度
    - 告警通知
    """
    
    def __init__(self, **kwargs):
        super().__init__(
            name="WatcherAgent",
            description="市场异常监控与预警专家",
            **kwargs
        )
        self._monitors: List[Dict] = []
        self._alerts: List[Dict] = []
        self._callbacks: List[Callable] = []
        self._running = False
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行监控任务
        
        Args:
            input_data: {
                "mode": "once" | "continuous",
                "checks": [...],
                "thresholds": {...}
            }
        """
        self._log_event("start", input_data)
        
        mode = input_data.get("mode", "once")
        checks = input_data.get("checks", self._default_checks())
        thresholds = input_data.get("thresholds", self._default_thresholds())
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "checks_performed": len(checks),
            "alerts_generated": 0,
            "details": []
        }
        
        if mode == "once":
            # 一次性检查
            for check in checks:
                result = await self._perform_check(check, thresholds)
                results["details"].append(result)
                
                if result.get("alert"):
                    results["alerts_generated"] += 1
                    self._alerts.append(result)
                    
                    # 触发回调
                    await self._notify_alert(result)
        
        elif mode == "continuous":
            # 持续监控（简化实现）
            logger.info("持续监控模式启动（单次演示）")
            for _ in range(3):  # 演示：检查3轮
                for check in checks:
                    result = await self._perform_check(check, thresholds)
                    results["details"].append(result)
                    
                    if result.get("alert"):
                        results["alerts_generated"] += 1
                await asyncio.sleep(1)  # 间隔
            
            results["note"] = "持续监控演示完成"
        
        self._log_event("complete", results)
        
        return results
    
    async def _perform_check(self, check: Dict, thresholds: Dict) -> Dict:
        """执行单个检查项"""
        check_type = check.get("type", "sentiment")
        
        if check_type == "sentiment":
            return await self._check_sentiment(check, thresholds)
        elif check_type == "price":
            return await self._check_price(check, thresholds)
        elif check_type == "volume":
            return await self._check_volume(check, thresholds)
        elif check_type == "news_spike":
            return await self._check_news_spike(check, thresholds)
        else:
            return {"type": check_type, "alert": False, "message": f"未知检查类型: {check_type}"}
    
    async def _check_sentiment(self, check: Dict, thresholds: Dict) -> Dict:
        """检查市场情绪"""
        from tools.sentiment_analyzer import SentimentAnalyzer
        from tools.news_collector import FinancialNewsCollector
        
        collector = FinancialNewsCollector()
        analyzer = SentimentAnalyzer()
        
        news = collector.collect_news(limit=50, time_range="1h").get("news", [])
        
        if not news:
            return {
                "type": "sentiment",
                "alert": False,
                "message": "暂无新闻数据"
            }
        
        sentiments = []
        for item in news[:20]:
            sent = analyzer.analyze(item.get("title", ""), item.get("content", ""))
            sentiments.append(sent["score"])
        
        avg_score = sum(sentiments) / len(sentiments) if sentiments else 0
        
        alert_threshold = thresholds.get("sentiment_extreme", -0.5)
        is_alert = avg_score < alert_threshold
        
        return {
            "type": "sentiment",
            "alert": is_alert,
            "value": round(avg_score, 3),
            "threshold": alert_threshold,
            "message": f"情绪极端偏空 ({avg_score:.3f})" if is_alert else f"情绪正常 ({avg_score:.3f})",
            "sample_size": len(sentiments)
        }
    
    async def _check_price(self, check: Dict, thresholds: Dict) -> Dict:
        """检查价格异常"""
        symbol = check.get("symbol", "GC=F")
        threshold = thresholds.get("price_change_pct", 5.0)
        
        # 模拟价格变化检测
        # 实际应接入行情数据
        import random
        price_change = random.uniform(-threshold * 2, threshold * 2)
        
        is_alert = abs(price_change) > threshold
        
        return {
            "type": "price",
            "symbol": symbol,
            "alert": is_alert,
            "value": round(price_change, 2),
            "threshold": threshold,
            "message": f"{symbol} 涨跌幅 {price_change:.2f}%"
        }
    
    async def _check_volume(self, check: Dict, thresholds: Dict) -> Dict:
        """检查交易量异常"""
        # 模拟交易量检测
        import random
        volume_ratio = random.uniform(0.5, 3.0)
        threshold = thresholds.get("volume_ratio", 2.0)
        
        is_alert = volume_ratio > threshold
        
        return {
            "type": "volume",
            "alert": is_alert,
            "value": round(volume_ratio, 2),
            "threshold": threshold,
            "message": f"交易量倍数 {volume_ratio:.2f}x"
        }
    
    async def _check_news_spike(self, check: Dict, thresholds: Dict) -> Dict:
        """检查新闻量激增"""
        from tools.news_collector import FinancialNewsCollector
        
        collector = FinancialNewsCollector()
        
        recent = collector.collect_news(limit=100, time_range="1h").get("news", [])
        previous = collector.collect_news(limit=100, time_range="1h", offset="1h").get("news", [])
        
        current_count = len(recent)
        previous_count = len(previous)
        
        if previous_count == 0:
            ratio = float('inf')
        else:
            ratio = current_count / previous_count
        
        threshold = thresholds.get("news_spike_ratio", 2.0)
        is_alert = ratio > threshold
        
        return {
            "type": "news_spike",
            "alert": is_alert,
            "current_count": current_count,
            "previous_count": previous_count,
            "ratio": round(ratio, 2) if ratio != float('inf') else float('inf'),
            "threshold": threshold,
            "message": f"新闻量激增 {ratio:.1f}x" if is_alert else f"新闻量正常 ({ratio:.1f}x)"
        }
    
    def _default_checks(self) -> List[Dict]:
        """默认检查项"""
        return [
            {"type": "sentiment"},
            {"type": "news_spike"},
            {"type": "price", "symbol": "GC=F"},
            {"type": "price", "symbol": "CL=F"},
            {"type": "price", "symbol": "BTC-USD"}
        ]
    
    def _default_thresholds(self) -> Dict:
        """默认阈值"""
        return {
            "sentiment_extreme": -0.5,
            "price_change_pct": 5.0,
            "volume_ratio": 2.0,
            "news_spike_ratio": 2.0
        }
    
    async def _notify_alert(self, alert: Dict):
        """通知回调"""
        for callback in self._callbacks:
            try:
                await callback(alert)
            except Exception as e:
                logger.error(f"告警回调失败: {e}")
    
    def register_callback(self, callback: Callable):
        """注册告警回调"""
        self._callbacks.append(callback)
        logger.info(f"注册告警回调，当前回调数: {len(self._callbacks)}")
    
    def get_alerts(self, limit: int = 10) -> List[Dict]:
        """获取历史告警"""
        return self._alerts[-limit:]
    
    def clear_alerts(self):
        """清空告警历史"""
        self._alerts.clear()
        logger.info("告警历史已清空")
