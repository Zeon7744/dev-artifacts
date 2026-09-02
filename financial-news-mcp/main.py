#!/usr/bin/env python3
"""
金融新闻MCP服务器 v2.0
基于MCP 2026-07-28规范（无状态协议）

功能：
- 全球财经新闻采集（13+权威数据源 + 外部数据源扩展）
- 情感分析（正面/负面/中性）
- 趋势预测（期货/基金/股票）
- 投资建议生成
- 数据真实性验证
- API网关（RESTful + Webhook）
- 管理平台（用户分级 + 权限控制 + 计费）
"""

import json
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("financial-news-mcp")

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "tools"))
sys.path.insert(0, str(PROJECT_ROOT / "api_gateway"))
sys.path.insert(0, str(PROJECT_ROOT / "management"))

try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger.warning("mcp包未安装，部分功能可能受限")

from tools.news_collector import FinancialNewsCollector
from tools.sentiment_analyzer import SentimentAnalyzer
from tools.trend_predictor import TrendPredictor
from tools.investment_advisor import InvestmentAdvisor
from tools.data_validator import DataValidator
from tools.external_sources import ExternalSourceRegistry, DataAdapterRegistry

# API网关和管理平台（可选）
try:
    from api_gateway.gateway import APIGateway
    from management.manager import ManagementSystem
    EXTERNAL_SERVICES = True
except ImportError:
    EXTERNAL_SERVICES = False
    logger.warning("API网关或管理平台模块加载失败")

# MCP协议版本
MCP_PROTOCOL_VERSION = "2026-07-28"

# 服务器信息
SERVER_INFO = {
    "name": "financial-news-mcp",
    "version": "2.0.0",
    "description": "全球财经新闻数据采集、情感分析、趋势预测、投资建议 + API网关 + 管理平台"
}

# 初始化组件
news_collector = FinancialNewsCollector()
sentiment_analyzer = SentimentAnalyzer()
trend_predictor = TrendPredictor()
investment_advisor = InvestmentAdvisor()
data_validator = DataValidator()
external_sources = ExternalSourceRegistry()

# API网关和管理平台
api_gateway = None
management_system = None

if EXTERNAL_SERVICES:
    api_gateway = APIGateway()
    management_system = ManagementSystem()

if MCP_AVAILABLE:
    mcp = FastMCP("financial-news-mcp")


# ========== 工具定义 ==========

TOOLS_DEFINITION = [
    {
        "name": "collect_news",
        "title": "采集全球财经新闻",
        "description": """采集指定类别的全球财经新闻，支持多种数据源：

数据源：
- Reuters RSS: 路透社国际新闻（可信度 0.95）
- Bloomberg RSS: 彭博社财经新闻（可信度 0.93）
- FT RSS: 金融时报（可信度 0.92）
- WSJ RSS: 华尔街日报（可信度 0.91）
- CNBC RSS: 美国财经频道（可信度 0.88）
- MarketWatch RSS: （可信度 0.85）
- 东方财富: 中国财经门户（可信度 0.82）
- 财联社: （可信度 0.80）
- 第一财经: （可信度 0.80）
- yfinance: 实时行情数据

外部数据源：
- 支持动态注册自定义RSS/API/文件数据源

返回内容：
- 新闻标题、摘要、来源
- 发布时间、URL
- 分类标签
- 数据来源验证状态
- 质量评分

参数：
- category: 新闻类别（all/commodity/crypto/fund/stock/macro）
- sources: 指定数据源（逗号分隔）
- limit: 新闻数量限制（默认20）
- time_range: 时间范围（24h/7d/30d）
- min_credibility: 最低可信度（默认0.75）
""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "新闻类别",
                    "enum": ["all", "commodity", "crypto", "fund", "stock", "macro"],
                    "default": "all"
                },
                "sources": {
                    "type": "string",
                    "description": "数据源（逗号分隔）",
                    "default": ""
                },
                "limit": {
                    "type": "integer",
                    "description": "新闻数量限制",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100
                },
                "time_range": {
                    "type": "string",
                    "description": "时间范围",
                    "enum": ["24h", "7d", "30d"],
                    "default": "24h"
                },
                "min_credibility": {
                    "type": "number",
                    "description": "最低可信度",
                    "default": 0.75
                }
            },
            "required": []
        }
    },
    {
        "name": "analyze_sentiment",
        "title": "新闻情感分析",
        "description": """对财经新闻进行情感分析，评估市场情绪。

分析维度：
- 正面/负面/中性情感评分
- 情绪强度（0-1）
- 关键词提取
- 市场影响评估

支持批量分析，可传入新闻列表或URL。

参数：
- news_items: 新闻列表（标题+内容）
- news_urls: 新闻URL列表
- detail_level: 分析粒度（basic/advanced）
""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "news_items": {
                    "type": "array",
                    "description": "新闻列表（对象数组）",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "content": {"type": "string"},
                            "source": {"type": "string"}
                        }
                    }
                },
                "news_urls": {
                    "type": "array",
                    "description": "新闻URL列表",
                    "items": {"type": "string"}
                },
                "detail_level": {
                    "type": "string",
                    "description": "分析粒度",
                    "enum": ["basic", "advanced"],
                    "default": "basic"
                }
            },
            "required": []
        }
    },
    {
        "name": "predict_trend",
        "title": "市场趋势预测",
        "description": """基于新闻情绪和历史数据预测市场趋势。

预测模型：
- LLM集成：使用大语言模型分析新闻影响
- 情感加权：基于情绪指数调整预测
- 多因子：结合技术指标和基本面

预测目标：
- 大宗商品（黄金/原油/铜）
- 加密货币（BTC/ETH）
- 指数期货（标普500/恒生/沪深300）
- 基金表现

参数：
- asset_type: 资产类型
- symbol: 资产代码
- horizon: 预测周期（1d/1w/1m）
- use_news: 是否使用新闻数据
""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asset_type": {
                    "type": "string",
                    "description": "资产类型",
                    "enum": ["commodity", "crypto", "index", "fund", "stock"],
                    "default": "commodity"
                },
                "symbol": {
                    "type": "string",
                    "description": "资产代码",
                    "default": "GC=F"
                },
                "horizon": {
                    "type": "string",
                    "description": "预测周期",
                    "enum": ["1d", "1w", "1m"],
                    "default": "1w"
                },
                "use_news": {
                    "type": "boolean",
                    "description": "是否使用新闻数据",
                    "default": True
                }
            },
            "required": []
        }
    },
    {
        "name": "get_investment_advice",
        "title": "投资建议",
        "description": """基于新闻分析和市场预测，生成投资建议。

建议内容：
- 持仓建议（买入/卖出/持有）
- 仓位管理
- 风险等级评估
- 止损止盈位
- 配置比例建议

适用于：
- 期货市场
- 基金投资
- 股票配置
- 组合优化

参数：
- portfolio_value: 投资组合价值
- risk_tolerance: 风险偏好（保守/稳健/激进）
- target_return: 目标收益率
- assets: 指定资产列表
""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "portfolio_value": {
                    "type": "number",
                    "description": "投资组合价值（美元）",
                    "default": 100000
                },
                "risk_tolerance": {
                    "type": "string",
                    "description": "风险偏好",
                    "enum": ["conservative", "moderate", "aggressive"],
                    "default": "moderate"
                },
                "target_return": {
                    "type": "number",
                    "description": "目标年化收益率（%）",
                    "default": 15
                },
                "assets": {
                    "type": "array",
                    "description": "资产列表",
                    "items": {"type": "string"}
                }
            },
            "required": []
        }
    },
    {
        "name": "validate_data_source",
        "title": "数据源验证",
        "description": """验证新闻来源的真实性和可靠性。

验证项：
- 来源权威性评分
- 交叉验证（多源比对）
- 事实核查标记
- 时效性检查

返回验证结果和可信度评分。

参数：
- news_item: 新闻对象
- check_facts: 是否进行事实核查
- min_sources: 最低验证源数量
""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "news_item": {
                    "type": "object",
                    "description": "新闻对象",
                    "properties": {
                        "title": {"type": "string"},
                        "url": {"type": "string"},
                        "source": {"type": "string"},
                        "published_at": {"type": "string"}
                    }
                },
                "check_facts": {
                    "type": "boolean",
                    "description": "是否进行事实核查",
                    "default": True
                },
                "min_sources": {
                    "type": "integer",
                    "description": "最低验证源数量",
                    "default": 2
                }
            },
            "required": []
        }
    },
    {
        "name": "register_external_source",
        "title": "注册外部数据源",
        "description": """注册自定义外部数据源，扩展数据采集能力。

支持的类型：
- rss: RSS Feed（需提供URL）
- api: REST API（需提供endpoint）
- file: 本地文件（需提供路径）

参数：
- source_id: 数据源唯一标识
- name: 数据源名称
- type: 数据类型（rss/api/file）
- config: 配置参数
- category: 分类（news/commodity/crypto/fund）
- credibility: 可信度（0-1）
""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_id": {
                    "type": "string",
                    "description": "数据源唯一标识"
                },
                "name": {
                    "type": "string",
                    "description": "数据源名称"
                },
                "type": {
                    "type": "string",
                    "description": "数据类型",
                    "enum": ["rss", "api", "file"]
                },
                "config": {
                    "type": "object",
                    "description": "配置参数",
                    "properties": {
                        "url": {"type": "string"},
                        "endpoint": {"type": "string"},
                        "path": {"type": "string"},
                        "headers": {"type": "object"}
                    }
                },
                "category": {
                    "type": "string",
                    "description": "分类",
                    "default": "news"
                },
                "credibility": {
                    "type": "number",
                    "description": "可信度",
                    "default": 0.7
                }
            },
            "required": ["source_id", "name", "type"]
        }
    },
    {
        "name": "list_external_sources",
        "title": "列出外部数据源",
        "description": """列出所有已注册的外部数据源及其状态。

返回：
- 数据源列表（含状态、可信度、最后更新时间）
- 统计数据（总数、启用数、健康数）
""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "enabled_only": {
                    "type": "boolean",
                    "description": "仅显示启用的数据源",
                    "default": False
                }
            },
            "required": []
        }
    },
    {
        "name": "create_api_key",
        "title": "创建API密钥",
        "description": """创建新的API密钥，用于外部应用接入。

层级：
- free: 基础功能（每日100请求）
- premium: 高级功能（每日10000请求）
- enterprise: 企业功能（无限制 + Webhook）

参数：
- name: 密钥名称
- tier: 层级（free/premium/enterprise）
""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "密钥名称"
                },
                "tier": {
                    "type": "string",
                    "description": "层级",
                    "enum": ["free", "premium", "enterprise"],
                    "default": "free"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "register_user",
        "title": "注册用户",
        "description": """注册新用户到管理平台。

角色：
- viewer: 观察者（只读）
- analyst: 分析师（可分析）
- trader: 交易员（可交易）
- admin: 管理员（全部权限）

参数：
- user_id: 用户唯一标识
- name: 用户姓名
- email: 邮箱
- role: 角色
""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "用户唯一标识"
                },
                "name": {
                    "type": "string",
                    "description": "用户姓名"
                },
                "email": {
                    "type": "string",
                    "description": "邮箱"
                },
                "role": {
                    "type": "string",
                    "description": "角色",
                    "enum": ["viewer", "analyst", "trader", "admin"],
                    "default": "viewer"
                }
            },
            "required": ["user_id", "name"]
        }
    },
    {
        "name": "list_tools",
        "title": "列出所有工具",
        "description": """列出MCP服务器支持的所有工具及其详细信息。

返回工具列表，包括：
- 工具名称
- 工具描述
- 输入参数schema
- 缓存策略
""",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]


# ========== 工具处理器 ==========

def _handle_collect_news(args: Dict[str, Any]) -> Dict[str, Any]:
    """处理新闻采集请求"""
    category = args.get("category", "all")
    sources = args.get("sources", "").split(",") if args.get("sources") else []
    limit = args.get("limit", 20)
    time_range = args.get("time_range", "24h")
    min_credibility = args.get("min_credibility", 0.75)
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "category": category,
        "sources_requested": sources if sources else ["all"],
        "limit": limit,
        "time_range": time_range,
        "min_credibility": min_credibility
    }
    
    try:
        # 采集内置RSS新闻
        news_list = news_collector.collect_news(
            category=category,
            sources=sources if sources else None,
            limit=limit,
            time_range=time_range,
            min_credibility=min_credibility
        )
        
        # 采集外部数据源新闻
        external_news = []
        for source in external_sources.list_sources(enabled_only=True):
            if source["category"] == category or category == "all":
                from tools.external_sources import DataAdapterRegistry
                ext_source = external_sources.get_source(source["source_id"])
                if ext_source:
                    items = DataAdapterRegistry.fetch_from_source(ext_source)
                    external_news.extend(items)
        
        # 合并新闻
        all_news = news_list.get("news", []) + external_news
        
        # 重新排序和去重
        all_news = sorted(all_news, key=lambda x: x.get("published_at", ""), reverse=True)
        
        # 去重
        seen_titles = set()
        unique_news = []
        for news in all_news:
            title_key = news.get("title", "")[:30]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_news.append(news)
        
        # 限制数量
        if len(unique_news) > limit:
            unique_news = unique_news[:limit]
        
        result["news_count"] = len(unique_news)
        result["news"] = unique_news
        result["external_count"] = len(external_news)
        
        # 验证数据源
        validated_news = []
        for news in unique_news[:10]:  # 仅验证前10条
            validation = data_validator.validate_source(news)
            validated_news.append({
                **news,
                "validation": validation
            })
        
        result["validated_news"] = validated_news
        result["validation_summary"] = {
            "total_checked": len(validated_news),
            "high_reliability": sum(1 for n in validated_news if n["validation"]["reliability_score"] >= 0.8),
            "medium_reliability": sum(1 for n in validated_news if 0.5 <= n["validation"]["reliability_score"] < 0.8),
            "low_reliability": sum(1 for n in validated_news if n["validation"]["reliability_score"] < 0.5)
        }
        
        # 质量评分
        result["quality_score"] = news_list.get("quality_score", 0.0)
        
    except Exception as e:
        logger.error(f"新闻采集失败: {e}")
        result["error"] = str(e)
        result["news"] = []
        result["news_count"] = 0
    
    return result


def _handle_analyze_sentiment(args: Dict[str, Any]) -> Dict[str, Any]:
    """处理情感分析请求"""
    news_items = args.get("news_items", [])
    news_urls = args.get("news_urls", [])
    detail_level = args.get("detail_level", "basic")
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "detail_level": detail_level,
        "news_count": len(news_items) + len(news_urls)
    }
    
    try:
        # 如果有URL，先获取新闻内容
        if news_urls:
            for url in news_urls:
                news = news_collector.fetch_news_by_url(url)
                if news:
                    news_items.append(news)
        
        if not news_items:
            # 采集最新新闻进行分析
            news_items = news_collector.collect_news(limit=20)["news"]
        
        # 情感分析
        analysis_results = []
        for news in news_items:
            sentiment = sentiment_analyzer.analyze(
                news.get("title", ""),
                news.get("content", ""),
                detail=detail_level == "advanced"
            )
            analysis_results.append({
                "source": news.get("source", "unknown"),
                "title": news.get("title", ""),
                "sentiment": sentiment
            })
        
        # 聚合分析
        positive_count = sum(1 for r in analysis_results if r["sentiment"]["polarity"] == "positive")
        negative_count = sum(1 for r in analysis_results if r["sentiment"]["polarity"] == "negative")
        neutral_count = sum(1 for r in analysis_results if r["sentiment"]["polarity"] == "neutral")
        
        avg_sentiment = sum(r["sentiment"]["score"] for r in analysis_results) / len(analysis_results) if analysis_results else 0
        
        result.update({
            "results": analysis_results,
            "summary": {
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count,
                "average_score": round(avg_sentiment, 3),
                "market_sentiment": "bullish" if avg_sentiment > 0.2 else "bearish" if avg_sentiment < -0.2 else "neutral"
            }
        })
        
    except Exception as e:
        logger.error(f"情感分析失败: {e}")
        result["error"] = str(e)
        result["results"] = []
    
    return result


def _handle_predict_trend(args: Dict[str, Any]) -> Dict[str, Any]:
    """处理趋势预测请求"""
    asset_type = args.get("asset_type", "commodity")
    symbol = args.get("symbol", "GC=F")
    horizon = args.get("horizon", "1w")
    use_news = args.get("use_news", True)
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "asset_type": asset_type,
        "symbol": symbol,
        "horizon": horizon,
        "use_news": use_news
    }
    
    try:
        # 获取新闻数据
        news_data = []
        if use_news:
            news_data = news_collector.collect_news(
                category="all",
                limit=50,
                time_range="7d"
            ).get("news", [])
        
        # 分析新闻情感
        sentiment_scores = []
        for news in news_data:
            sentiment = sentiment_analyzer.analyze(news.get("title", ""), news.get("content", ""))
            sentiment_scores.append(sentiment["score"])
        
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        # 预测趋势
        prediction = trend_predictor.predict(
            asset_type=asset_type,
            symbol=symbol,
            horizon=horizon,
            news_sentiment=avg_sentiment,
            news_count=len(news_data)
        )
        
        result.update({
            "prediction": prediction,
            "news_sentiment": {
                "average": round(avg_sentiment, 3),
                "count": len(news_data),
                "influence_weight": 0.3 if use_news else 0.0
            },
            "models_used": ["LLM_NLP", "Sentiment_Weighted", "Technical_Factor"]
        })
        
    except Exception as e:
        logger.error(f"趋势预测失败: {e}")
        result["error"] = str(e)
        result["prediction"] = {"direction": "hold", "confidence": 0.5}
    
    return result


def _handle_get_investment_advice(args: Dict[str, Any]) -> Dict[str, Any]:
    """处理投资建议请求"""
    portfolio_value = args.get("portfolio_value", 100000)
    risk_tolerance = args.get("risk_tolerance", "moderate")
    target_return = args.get("target_return", 15)
    assets = args.get("assets", [])
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "portfolio_value": portfolio_value,
        "risk_tolerance": risk_tolerance,
        "target_return": target_return
    }
    
    try:
        # 获取当前市场状态
        current_news = news_collector.collect_news(limit=30, time_range="24h")
        sentiment_result = _handle_analyze_sentiment({
            "news_items": current_news.get("news", [])
        })
        
        avg_sentiment = sentiment_result.get("summary", {}).get("average_score", 0)
        
        # 预测各资产趋势
        predictions = {}
        if assets:
            for asset in assets[:5]:
                pred = _handle_predict_trend({"symbol": asset, "use_news": True})
                predictions[asset] = pred.get("prediction", {})
        else:
            # 默认预测主要资产
            default_assets = ["GC=F", "CL=F", "BTC-USD", "SPY", "QQQ"]
            for asset in default_assets:
                pred = _handle_predict_trend({"symbol": asset, "use_news": True})
                predictions[asset] = pred.get("prediction", {})
        
        # 生成建议
        advice = investment_advisor.generate_advice(
            portfolio_value=portfolio_value,
            risk_tolerance=risk_tolerance,
            target_return=target_return,
            predictions=predictions,
            market_sentiment=avg_sentiment
        )
        
        result.update({
            "advice": advice,
            "market_context": {
                "sentiment_score": round(avg_sentiment, 3),
                "sentiment_label": sentiment_result.get("summary", {}).get("market_sentiment", "neutral"),
                "news_volume": current_news.get("news_count", 0)
            }
        })
        
    except Exception as e:
        logger.error(f"投资建议生成失败: {e}")
        result["error"] = str(e)
        result["advice"] = {"recommendation": "hold", "reason": "分析失败"}
    
    return result


def _handle_validate_data_source(args: Dict[str, Any]) -> Dict[str, Any]:
    """处理数据源验证请求"""
    news_item = args.get("news_item", {})
    check_facts = args.get("check_facts", True)
    min_sources = args.get("min_sources", 2)
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "check_facts": check_facts,
        "min_sources": min_sources
    }
    
    try:
        if not news_item:
            # 验证最近采集的新闻
            news_list = news_collector.collect_news(limit=5)
            news_item = news_list.get("news", [{}])[0] if news_list.get("news") else {}
        
        if not news_item:
            result["error"] = "没有可验证的新闻数据"
            return result
        
        validation = data_validator.validate_source(
            news_item,
            check_facts=check_facts,
            min_sources=min_sources
        )
        
        result.update({
            "news_title": news_item.get("title", ""),
            "news_source": news_item.get("source", ""),
            "validation": validation
        })
        
    except Exception as e:
        logger.error(f"数据源验证失败: {e}")
        result["error"] = str(e)
        result["validation"] = {"reliability_score": 0, "status": "error"}
    
    return result


def _handle_register_external_source(args: Dict[str, Any]) -> Dict[str, Any]:
    """处理外部数据源注册"""
    source_id = args.get("source_id")
    name = args.get("name")
    type_ = args.get("type", "rss")
    config = args.get("config", {})
    category = args.get("category", "news")
    credibility = args.get("credibility", 0.7)
    
    if not source_id or not name:
        return {"error": "source_id和name为必填项"}
    
    result = external_sources.register_source(source_id, {
        "name": name,
        "type": type_,
        **config,  # 展开 config 到顶层，避免双重嵌套
        "category": category,
        "credibility": credibility,
        "enabled": True
    })
    
    return result


def _handle_list_external_sources(args: Dict[str, Any]) -> Dict[str, Any]:
    """处理外部数据源列表"""
    enabled_only = args.get("enabled_only", False)
    
    sources = external_sources.list_sources(enabled_only=enabled_only)
    
    return {
        "sources": sources,
        "total": len(sources),
        "enabled": sum(1 for s in sources if s.get("enabled")),
        "timestamp": datetime.now().isoformat()
    }


def _handle_create_api_key(args: Dict[str, Any]) -> Dict[str, Any]:
    """处理API密钥创建"""
    if not api_gateway:
        return {"error": "API网关未启用"}
    
    name = args.get("name")
    tier = args.get("tier", "free")
    
    if not name:
        return {"error": "name为必填项"}
    
    result = api_gateway.create_api_key(name, tier)
    
    return result


def _handle_register_user(args: Dict[str, Any]) -> Dict[str, Any]:
    """处理用户注册"""
    if not management_system:
        return {"error": "管理平台未启用"}
    
    user_id = args.get("user_id")
    name = args.get("name")
    email = args.get("email", "")
    role = args.get("role", "viewer")
    
    if not user_id or not name:
        return {"error": "user_id和name为必填项"}
    
    result = management_system.register_user(user_id, name, email, role)
    
    return result


# ========== MCP请求处理 ==========

def handle_mcp_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """处理MCP请求"""
    method = request.get("method", "")
    params = request.get("params", {})
    request_id = request.get("id", 1)
    
    logger.info(f"收到请求: method={method}")
    
    # server/discover - 发现服务器能力
    if method == "server/discover":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "resultType": "complete",
                "serverInfo": SERVER_INFO,
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {"listChanged": True}
                },
                "instructions": "使用 tools/list 获取工具列表，使用 tools/call 调用工具"
            }
        }
    
    # tools/list - 列出工具
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "resultType": "complete",
                "tools": TOOLS_DEFINITION,
                "ttlMs": 300000,
                "cacheScope": "public"
            }
        }
    
    # tools/call - 调用工具
    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        result = {
            "jsonrpc": "2.0",
            "id": request_id
        }
        
        try:
            handlers = {
                "collect_news": _handle_collect_news,
                "analyze_sentiment": _handle_analyze_sentiment,
                "predict_trend": _handle_predict_trend,
                "get_investment_advice": _handle_get_investment_advice,
                "validate_data_source": _handle_validate_data_source,
                "register_external_source": _handle_register_external_source,
                "list_external_sources": _handle_list_external_sources,
                "create_api_key": _handle_create_api_key,
                "register_user": _handle_register_user,
                "list_tools": lambda args: {"tools": TOOLS_DEFINITION, "count": len(TOOLS_DEFINITION)},
            }
            
            handler = handlers.get(tool_name)
            if handler:
                tool_result = handler(arguments)
            else:
                tool_result = {
                    "error": f"未知工具: {tool_name}",
                    "available_tools": [t["name"] for t in TOOLS_DEFINITION]
                }
            
            result["result"] = {
                "content": [{
                    "type": "text",
                    "text": json.dumps(tool_result, ensure_ascii=False, indent=2)
                }]
            }
            
        except Exception as e:
            logger.error(f"工具调用失败: {e}")
            result["error"] = {
                "code": -32000,
                "message": str(e)
            }
    
    else:
        result["error"] = {
            "code": -32601,
            "message": f"Method not found: {method}"
        }
    
    return result


def run_server():
    """运行 MCP 服务器"""
    print(f"📊 金融新闻MCP服务器 v2.0 启动...")
    print(f"📍 协议版本: {MCP_PROTOCOL_VERSION}")
    print(f"📍 工具数量: {len(TOOLS_DEFINITION)}")
    print(f"   - collect_news: 全球财经新闻采集")
    print(f"   - analyze_sentiment: 新闻情感分析")
    print(f"   - predict_trend: 市场趋势预测")
    print(f"   - get_investment_advice: 投资建议生成")
    print(f"   - validate_data_source: 数据源验证")
    print(f"   - register_external_source: 外部数据源注册")
    print(f"   - list_external_sources: 外部数据源列表")
    print(f"   - create_api_key: 创建API密钥")
    print(f"   - register_user: 注册用户")
    print(f"   - list_tools: 列出所有工具")
    
    if api_gateway:
        print(f"\n🌐 API网关已启用: http://localhost:8766")
        print(f"💰 管理平台已启用")
    
    print("-" * 50)
    
    if MCP_AVAILABLE:
        mcp.run()
    else:
        # 手动处理请求
        import sys
        for line in sys.stdin:
            try:
                request = json.loads(line.strip())
                response = handle_mcp_request(request)
                print(json.dumps(response, ensure_ascii=False))
            except Exception as e:
                print(json.dumps({"error": str(e)}))


if __name__ == "__main__":
    run_server()
