"""
分析师 Agent - 每日财经简报生成
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json

from .base_agent import BaseAgent, AgentContext

logger = logging.getLogger(__name__)


class AnalystAgent(BaseAgent):
    """
    分析师 Agent
    
    职责：
    - 采集每日财经新闻
    - 生成市场分析简报
    - 提取关键信号
    - 生成投资建议摘要
    """
    
    def __init__(self, **kwargs):
        super().__init__(
            name="AnalystAgent",
            description="每日财经简报生成专家",
            **kwargs
        )
        self._briefing_template = """
# 📊 财经简报 - {date}

## 市场概览
{market_overview}

## 热门事件
{hot_events}

## 情绪分析
- 整体情绪: {sentiment_label}
- 正面信号: {positive_signals}
- 负面信号: {negative_signals}

## 资产趋势
{asset_trends}

## 操作建议
{investment_advice}

---
*生成时间: {generated_at}*
"""
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行分析任务
        
        Args:
            input_data: {
                "type": "daily" | "weekly" | "custom",
                "date_range": {"start": ..., "end": ...},
                "focus_areas": ["commodity", "crypto", ...],
                "output_format": "briefing" | "raw"
            }
        """
        self._log_event("start", input_data)
        
        # 1. 数据采集
        news_data = await self._collect_news(input_data)
        
        # 2. 情感分析
        sentiment = await self._analyze_sentiment(news_data)
        
        # 3. 热点提取
        hot_events = await self._extract_hot_events(news_data)
        
        # 4. 资产趋势
        trends = await self._analyze_trends(news_data, sentiment)
        
        # 5. 生成简报
        if input_data.get("output_format") == "raw":
            result = {
                "news": news_data,
                "sentiment": sentiment,
                "events": hot_events,
                "trends": trends
            }
        else:
            result = self._generate_briefing(
                news_data, sentiment, hot_events, trends, input_data
            )
        
        self._log_event("complete", {"result_size": len(str(result))})
        
        return result
    
    async def _collect_news(self, input_data: Dict) -> List[Dict]:
        """采集新闻数据"""
        # 这里应该调用 news_collector
        # 暂时返回模拟数据
        from tools.news_collector import FinancialNewsCollector
        
        collector = FinancialNewsCollector()
        focus = input_data.get("focus_areas", ["all"])
        
        news = []
        for category in focus:
            if category == "all":
                category_news = collector.collect_news(limit=50, time_range="24h")
                news.extend(category_news.get("news", []))
            else:
                category_news = collector.collect_news(
                    category=category, limit=20, time_range="24h"
                )
                news.extend(category_news.get("news", []))
        
        # 去重
        seen = set()
        unique_news = []
        for n in news:
            key = n.get("title", "")[:30]
            if key not in seen:
                seen.add(key)
                unique_news.append(n)
        
        return unique_news[:100]
    
    async def _analyze_sentiment(self, news: List[Dict]) -> Dict:
        """分析市场情绪"""
        from tools.sentiment_analyzer import SentimentAnalyzer
        
        analyzer = SentimentAnalyzer()
        
        sentiments = []
        for item in news[:50]:  # 分析前50条
            sent = analyzer.analyze(
                item.get("title", ""),
                item.get("content", "")
            )
            sentiments.append(sent)
        
        # 聚合
        positive = sum(1 for s in sentiments if s["polarity"] == "positive")
        negative = sum(1 for s in sentiments if s["polarity"] == "negative")
        neutral = len(sentiments) - positive - negative
        
        avg_score = sum(s["score"] for s in sentiments) / len(sentiments) if sentiments else 0
        
        return {
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "average_score": round(avg_score, 3),
            "label": "bullish" if avg_score > 0.2 else "bearish" if avg_score < -0.2 else "neutral"
        }
    
    async def _extract_hot_events(self, news: List[Dict]) -> List[Dict]:
        """提取热门事件"""
        # 按来源和主题分组
        events = {}
        
        for item in news:
            source = item.get("source", "unknown")
            title = item.get("title", "")
            
            # 简单关键词匹配
            keywords = ["Fed", "利率", "加息", "降息", "CPI", "通胀", "美联储", 
                       "石油", "原油", "黄金", "比特币", "BTC", "股票", "股市"]
            
            for kw in keywords:
                if kw in title:
                    if kw not in events:
                        events[kw] = []
                    events[kw].append({
                        "title": title,
                        "source": source,
                        "time": item.get("published_at", "")
                    })
                    break
        
        # 转换为列表并排序
        hot_events = [
            {"keyword": kw, "count": len(items), "items": items[:3]}
            for kw, items in events.items()
            if len(items) >= 2
        ]
        
        hot_events.sort(key=lambda x: x["count"], reverse=True)
        
        return hot_events[:10]
    
    async def _analyze_trends(self, news: List[Dict], sentiment: Dict) -> Dict:
        """分析资产趋势"""
        from tools.trend_predictor import TrendPredictor
        
        predictor = TrendPredictor()
        
        trends = {}
        
        # 预测主要资产
        assets = [
            {"type": "commodity", "symbol": "GC=F", "name": "黄金"},
            {"type": "commodity", "symbol": "CL=F", "name": "原油"},
            {"type": "crypto", "symbol": "BTC-USD", "name": "比特币"},
            {"type": "index", "symbol": "SPY", "name": "标普500"},
            {"type": "index", "symbol": "QQQ", "name": "纳指100"},
        ]
        
        for asset in assets:
            pred = predictor.predict(
                asset_type=asset["type"],
                symbol=asset["symbol"],
                horizon="1w",
                news_sentiment=sentiment["average_score"]
            )
            
            trends[asset["symbol"]] = {
                "name": asset["name"],
                "direction": pred.get("direction", "hold"),
                "confidence": pred.get("confidence", 0.5),
                "prediction": pred.get("prediction", {})
            }
        
        return trends
    
    def _generate_briefing(
        self,
        news: List[Dict],
        sentiment: Dict,
        hot_events: List[Dict],
        trends: Dict,
        input_data: Dict
    ) -> Dict:
        """生成简报"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # 市场概览
        market_overview = f"""
今日共采集 {len(news)} 条财经新闻，来自多个权威数据源。
市场情绪指数: {sentiment['average_score']:.3f} ({sentiment['label']})
"""
        
        # 热门事件
        events_text = "\n".join([
            f"- **{e['keyword']}**: {e['count']}条相关报道"
            for e in hot_events[:5]
        ]) or "- 暂无显著热点"
        
        # 情绪信号
        positive_text = ", ".join([
            e["keyword"] for e in hot_events 
            if sentiment["positive"] > 0
        ][:3]) or "无显著正面信号"
        
        negative_text = ", ".join([
            e["keyword"] for e in hot_events
            if sentiment["negative"] > 0
        ][:3]) or "无显著负面信号"
        
        # 资产趋势
        trends_text = "\n".join([
            f"- {t['name']}({k}): {t['direction']} (置信度: {t['confidence']:.0%})"
            for k, t in trends.items()
        ])
        
        # 投资建议
        advice_text = self._generate_advice(sentiment, trends)
        
        briefing = self._briefing_template.format(
            date=date_str,
            market_overview=market_overview,
            hot_events=events_text,
            sentiment_label=sentiment["label"].upper(),
            positive_signals=positive_text,
            negative_signals=negative_text,
            asset_trends=trends_text,
            investment_advice=advice_text,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        return {
            "date": date_str,
            "type": "daily_briefing",
            "briefing_text": briefing,
            "summary": {
                "news_count": len(news),
                "sentiment": sentiment,
                "hot_topics": [e["keyword"] for e in hot_events[:5]],
                "top_trends": list(trends.keys())[:3]
            },
            "generated_at": datetime.now().isoformat()
        }
    
    def _generate_advice(self, sentiment: Dict, trends: Dict) -> str:
        """生成投资建议"""
        score = sentiment["average_score"]
        
        if score > 0.3:
            base_advice = "市场情绪偏乐观，可适度增配风险资产。"
        elif score < -0.3:
            base_advice = "市场情绪偏悲观，建议保持谨慎，增加防御性配置。"
        else:
            base_advice = "市场情绪中性，维持现有配置，关注结构性机会。"
        
        # 根据趋势调整
        bullish_count = sum(1 for t in trends.values() if t["direction"] == "up")
        bearish_count = sum(1 for t in trends.values() if t["direction"] == "down")
        
        if bullish_count > bearish_count:
            advice = base_advice + " 多数资产呈上涨趋势，可关注商品类机会。"
        elif bearish_count > bullish_count:
            advice = base_advice + " 多数资产呈下跌趋势，建议降低仓位。"
        else:
            advice = base_advice + " 资产走势分化，建议精选标的。"
        
        return advice
