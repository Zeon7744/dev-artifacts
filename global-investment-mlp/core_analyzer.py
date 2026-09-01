#!/usr/bin/env python3
"""
Global Investment MLP - 全球资本投资分析系统

支持机构类型：
- 全球公募基金 (Mutual Funds)
- 对冲基金 (Hedge Funds)
- 风险投资基金 (VC Funds)
- 私募股权基金 (Private Equity)
- 天使投资基金 (Angel Funds)
- 主权财富基金 (Sovereign Wealth Funds)

核心功能：
- 多因子量化分析
- 投资热点追踪
- 组合风险评估
- 行业轮动预测
- 资产配置建议
"""

import numpy as np
import pandas as pd
from pathlib import Path
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class FundType(Enum):
    """基金类型枚举"""
    MUTUAL_FUND = "mutual_fund"
    HEDGE_FUND = "hedge_fund"
    VC_FUND = "vc_fund"
    PE_FUND = "pe_fund"
    ANGEL_FUND = "angel_fund"
    SOVEREIGN = "sovereign_wealth"
    ENDOWMENT = "endowment"
    PENSION = "pension_fund"


class InvestmentStage(Enum):
    """投资阶段"""
    SEED = "seed"
    EARLY_STAGE = "early_stage"
    GROWTH = "growth"
    LATE_STAGE = "late_stage"
    PRE_IPO = "pre_ipo"
    IPO = "ipo"
    POST_IPO = "post_ipo"


class RiskLevel(Enum):
    """风险等级"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class FundProfile:
    """基金档案"""
    fund_id: str
    name: str
    fund_type: FundType
    inception_date: str
    AUM: float  # 管理规模（亿美元）
    strategy: str
    benchmark: str
    managers: List[str]
    geography_focus: List[str]
    sector_focus: List[str]
    vintages: List[int]
    
    # 绩效数据
    nav_history: Optional[pd.DataFrame] = None
    returns_1y: float = 0.0
    returns_3y: float = 0.0
    returns_5y: float = 0.0
    returns_ytd: float = 0.0
    
    # 风险指标
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    volatility: float = 0.0
    
    # 持仓信息
    top_holdings: List[Dict] = field(default_factory=list)
    sector_allocation: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'fund_id': self.fund_id,
            'name': self.name,
            'fund_type': self.fund_type.value,
            'aum_usd_billion': self.AUM,
            'returns_1y': self.returns_1y,
            'returns_3y': self.returns_3y,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'top_sectors': list(self.sector_allocation.keys())[:5]
        }


@dataclass 
class SectorHotspot:
    """投资热点"""
    sector: str
    score: float  # 0-100
    momentum: float
    risk_level: str
    expected_return: float
    timeframe: str
    key_themes: List[str]
    top_funds: List[str]
    
    def to_dict(self) -> Dict:
        return {
            'sector': self.sector,
            'score': self.score,
            'momentum': self.momentum,
            'risk_level': self.risk_level,
            'expected_return': self.expected_return,
            'timeframe': self.timeframe,
            'key_themes': self.key_themes[:3],
            'top_funds': self.top_funds[:3]
        }


@dataclass
class AllocationRecommendation:
    """资产配置建议"""
    target_weight: float
    current_weight: float
    action: str  # overweight, neutral, underweight
    confidence: float
    rationale: str
    risk_adjusted_return: float
    
    def to_dict(self) -> Dict:
        return {
            'target_weight': self.target_weight,
            'current_weight': self.current_weight,
            'action': self.action,
            'confidence': self.confidence,
            'rationale': self.rationale,
            'risk_adjusted_return': self.risk_adjusted_return
        }


class GlobalInvestmentAnalyzer:
    """全球投资分析核心引擎"""
    
    def __init__(self, data_dir: str = './data'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 基金库
        self.fund_database: Dict[str, FundProfile] = {}
        
        # 行业数据
        self.sector_data: Dict[str, pd.DataFrame] = {}
        
        # 宏观经济指标
        self.macro_indicators: Dict[str, float] = {}
        
        # 热点追踪
        self.hotspots: List[SectorHotspot] = []
        
        # 配置建议
        self.recommendations: List[AllocationRecommendation] = []
    
    def add_fund(self, fund: FundProfile):
        """添加基金到数据库"""
        self.fund_database[fund.fund_id] = fund
        logger.info(f"添加基金: {fund.name} ({fund.fund_type.value})")
    
    def analyze_sector_performance(self, sector: str, period: str = '1y') -> Dict:
        """分析行业表现"""
        # 模拟分析逻辑
        analysis = {
            'sector': sector,
            'period': period,
            'returns': np.random.uniform(-0.1, 0.3),
            'volatility': np.random.uniform(0.15, 0.4),
            'sharpe': np.random.uniform(-0.5, 2.0),
            'correlation_with_market': np.random.uniform(0.3, 0.9),
            'momentum_score': np.random.uniform(0, 100)
        }
        return analysis
    
    def detect_hotspots(self) -> List[SectorHotspot]:
        """检测投资热点"""
        sectors = ['AI/ML', 'Clean Energy', 'Biotech', 'Fintech', 'Cybersecurity', 
                   'E-commerce', 'Semiconductors', 'Cloud Computing', 'EV', 'Space']
        
        hotspots = []
        for sector in sectors:
            perf = self.analyze_sector_performance(sector)
            
            hotspot = SectorHotspot(
                sector=sector,
                score=perf['momentum_score'],
                momentum=perf['returns'],
                risk_level=self._assess_risk(perf['volatility']),
                expected_return=perf['returns'] * 1.2,
                timeframe=self._get_timeframe(perf['momentum_score']),
                key_themes=self._get_themes(sector),
                top_funds=self._get_top_funds(sector)
            )
            hotspots.append(hotspot)
        
        # 排序
        hotspots.sort(key=lambda x: x.score, reverse=True)
        self.hotspots = hotspots
        
        return hotspots[:10]
    
    def _assess_risk(self, volatility: float) -> str:
        """评估风险等级"""
        if volatility < 0.2:
            return RiskLevel.LOW.value
        elif volatility < 0.3:
            return RiskLevel.MEDIUM.value
        elif volatility < 0.4:
            return RiskLevel.HIGH.value
        else:
            return RiskLevel.VERY_HIGH.value
    
    def _get_timeframe(self, score: float) -> str:
        """获取投资周期"""
        if score > 75:
            return 'short_term'
        elif score > 50:
            return 'medium_term'
        else:
            return 'long_term'
    
    def _get_themes(self, sector: str) -> List[str]:
        """获取主题关键词"""
        themes_map = {
            'AI/ML': ['大模型', 'Agent', 'AIGC', '垂直应用'],
            'Clean Energy': ['储能', '氢能', '碳交易', '新能源'],
            'Biotech': ['基因编辑', 'mRNA', '细胞治疗', 'AI制药'],
            'Fintech': ['DeFi', '支付', '区块链', '智能投顾'],
            'Cybersecurity': ['零信任', 'SASE', '数据安全', '云安全']
        }
        return themes_map.get(sector, ['新兴技术', '高增长', '政策支持'])
    
    def _get_top_funds(self, sector: str) -> List[str]:
        """获取该领域头部基金"""
        # 模拟数据
        return [f'{sector} Fund {i}' for i in range(1, 4)]
    
    def generate_allocation_recommendations(
        self, 
        investor_profile: Dict,
        target_return: float,
        risk_tolerance: float
    ) -> List[AllocationRecommendation]:
        """生成资产配置建议"""
        recommendations = []
        
        # 根据投资者画像和热点生成建议
        for hotspot in self.hotspots[:8]:
            # 计算目标权重（基于风险调整收益）
            risk_adj_return = hotspot.expected_return / (hotspot.score / 100 * risk_tolerance + 0.1)
            
            # 确定操作建议
            if risk_adj_return > target_return * 1.2:
                action = 'overweight'
                weight = min(0.25, hotspot.score / 400)
            elif risk_adj_return > target_return * 0.8:
                action = 'neutral'
                weight = hotspot.score / 500
            else:
                action = 'underweight'
                weight = max(0.02, hotspot.score / 800)
            
            recommendation = AllocationRecommendation(
                target_weight=weight,
                current_weight=np.random.uniform(0, 0.15),
                action=action,
                confidence=min(0.9, hotspot.score / 100),
                rationale=f"{hotspot.sector}处于{hotspot.timeframe}高景气期",
                risk_adjusted_return=risk_adj_return
            )
            recommendations.append(recommendation)
        
        # 归一化权重
        total_weight = sum(r.target_weight for r in recommendations)
        for r in recommendations:
            r.target_weight = r.target_weight / total_weight * 0.8  # 保留20%现金
        
        self.recommendations = recommendations
        return recommendations
    
    def run_comprehensive_analysis(
        self,
        fund_ids: Optional[List[str]] = None,
        focus_sectors: Optional[List[str]] = None
    ) -> Dict:
        """运行综合分析"""
        logger.info("开始综合分析...")
        
        # 1. 热点检测
        hotspots = self.detect_hotspots()
        
        # 2. 基金筛选
        if fund_ids:
            selected_funds = [self.fund_database[fid] for fid in fund_ids 
                            if fid in self.fund_database]
        else:
            selected_funds = list(self.fund_database.values())[:20]
        
        # 3. 生成配置建议（使用默认参数）
        recommendations = self.generate_allocation_recommendations(
            investor_profile={'type': 'institutional'},
            target_return=0.15,
            risk_tolerance=0.6
        )
        
        # 4. 汇总结果
        result = {
            'analysis_timestamp': pd.Timestamp.now().isoformat(),
            'hotspots': [h.to_dict() for h in hotspots],
            'fund_analysis': [f.to_dict() for f in selected_funds[:10]],
            'recommendations': [r.to_dict() for r in recommendations[:8]],
            'market_summary': {
                'total_funds_analyzed': len(selected_funds),
                'avg_return_1y': np.mean([f.returns_1y for f in selected_funds]) if selected_funds else 0,
                'avg_sharpe': np.mean([f.sharpe_ratio for f in selected_funds]) if selected_funds else 0,
                'market_sentiment': 'bullish' if hotspots[0].score > 60 else 'neutral'
            }
        }
        
        return result


def main():
    """主函数"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    analyzer = GlobalInvestmentAnalyzer()
    
    # 添加模拟基金数据
    fund_types = [
        (FundType.HEDGE_FUND, 'Bridgewater All Weather', 'RWR'),
        (FundType.VC_FUND, 'Sequoia Capital', 'SEQ'),
        (FundType.PE_FUND, 'Blackstone Group', 'BX'),
        (FundType.MUTUAL_FUND, 'Vanguard S&P 500', 'VOO'),
        (FundType.ANGEL_FUND, 'Y Combinator', 'YC'),
    ]
    
    for i, (ftype, name, ticker) in enumerate(fund_types):
        fund = FundProfile(
            fund_id=f'T{ticker}',
            name=name,
            fund_type=ftype,
            inception_date='2020-01-01',
            AUM=np.random.uniform(10, 1000),
            strategy='multi_strategy',
            benchmark='SPX',
            managers=['Manager A', 'Manager B'],
            geography_focus=['US', 'Europe', 'Asia'],
            sector_focus=['Tech', 'Healthcare', 'Finance'],
            vintages=[2020, 2021, 2022]
        )
        fund.returns_1y = np.random.uniform(-0.1, 0.4)
        fund.sharpe_ratio = np.random.uniform(0.5, 2.5)
        fund.max_drawdown = np.random.uniform(-0.2, -0.05)
        
        analyzer.add_fund(fund)
    
    # 运行分析
    result = analyzer.run_comprehensive_analysis()
    
    print("\n" + "="*70)
    print("全球资本投资分析报告")
    print("="*70)
    
    print(f"\n【市场概览】")
    summary = result['market_summary']
    print(f"分析基金数: {summary['total_funds_analyzed']}")
    print(f"平均收益率(1年): {summary['avg_return_1y']:.1%}")
    print(f"平均夏普比率: {summary['avg_sharpe']:.2f}")
    print(f"市场情绪: {summary['market_sentiment']}")
    
    print(f"\n【投资热点 Top 5】")
    for i, h in enumerate(result['hotspots'][:5], 1):
        print(f"  {i}. {h['sector']} (得分:{h['score']:.0f}, 预期收益:{h['expected_return']:.1%})")
    
    print(f"\n【配置建议】")
    for r in result['recommendations'][:5]:
        print(f"  [{r['action'].upper()}] {r['target_weight']:.1%} - {r['rationale']}")
    
    print("\n" + "="*70)


if __name__ == '__main__':
    main()
