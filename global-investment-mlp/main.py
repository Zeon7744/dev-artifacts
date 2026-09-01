#!/usr/bin/env python3
"""
Global Investment MLP - 主程序入口

运行完整的投资分析流程：
1. 数据获取
2. 热点检测
3. 多因子分析
4. 风险评估
5. 配置建议
6. 报告生成
"""

import argparse
import logging
import json
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd

# 导入模块
from core_analyzer import GlobalInvestmentAnalyzer, FundType
from multi_factor_model import MultiFactorModel, SectorRotationModel
from risk_analytics import RiskDashboard, StressTester, CorrelationAnalyzer
from data_fetcher import GlobalFundDataFetcher, generate_synthetic_portfolio
from report_generator import InvestmentReportGenerator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_analysis(args):
    """运行完整分析流程"""
    
    print("\n" + "="*70)
    print("  全球资本投资分析系统 v1.0")
    print("="*70)
    
    # 1. 初始化组件
    print("\n[1/6] 初始化分析引擎...")
    analyzer = GlobalInvestmentAnalyzer(data_dir='./data')
    factor_model = MultiFactorModel(optimization_method=args.factor_method)
    risk_dashboard = RiskDashboard()
    stress_tester = StressTester()
    report_gen = InvestmentReportGenerator()
    data_fetcher = GlobalFundDataFetcher()
    
    # 2. 获取数据
    print("\n[2/6] 获取市场数据...")
    
    # 获取市场指数
    markets = data_fetcher.get_all_market_data(
        markets=args.markets.split(',') if args.markets else ['US', 'CN', 'HK'],
        days=args.days
    )
    print(f"  获取市场数据: {list(markets.keys())}")
    
    # 生成基金数据
    fund_types = ['hedge', 'vc', 'pe', 'mutual']
    all_funds = []
    for ft in fund_types:
        funds = data_fetcher.generate_fund_data(ft, n_funds=args.n_funds)
        all_funds.extend(funds)
        print(f"  {ft}基金: {len(funds)}只")
    
    # 添加到分析器
    for fund_data in all_funds:
        from core_analyzer import FundProfile
        fund = FundProfile(
            fund_id=fund_data['fund_id'],
            name=fund_data['name'],
            fund_type={
                'hedge': FundType.HEDGE_FUND,
                'vc': FundType.VC_FUND,
                'pe': FundType.PE_FUND,
                'mutual': FundType.MUTUAL_FUND
            }.get(fund_data['type'], FundType.MUTUAL_FUND),
            inception_date=fund_data['inception_date'],
            AUM=fund_data['aum_billions'],
            strategy='multi_strategy',
            benchmark='SPX',
            managers=['Manager A', 'Manager B'],
            geography_focus=['US', 'Europe', 'Asia'],
            sector_focus=['Tech', 'Healthcare', 'Finance'],
            vintages=[2020, 2021, 2022]
        )
        fund.returns_1y = fund_data['returns']['1y']
        fund.sharpe_ratio = fund_data['risk_metrics']['sharpe']
        fund.max_drawdown = fund_data['risk_metrics']['max_drawdown']
        analyzer.add_fund(fund)
    
    # 3. 运行核心分析
    print("\n[3/6] 运行核心分析...")
    
    # 热点检测
    hotspots = analyzer.detect_hotspots()
    print(f"  发现 {len(hotspots)} 个投资热点")
    
    # 行业轮动分析
    sector_rotator = SectorRotationModel()
    sector_returns = {}
    for market, df in markets.items():
        if len(df) > 20:
            sector_returns[f'{market}_market'] = df['Close'].pct_change()
    
    if sector_returns:
        momentum_scores = sector_rotator.analyze_momentum(sector_returns)
        rotation_signal = sector_rotator.detect_rotation(market_regime=args.regime)
        print(f"  市场周期: {rotation_signal.get('regime', args.regime)}")
    else:
        rotation_signal = {'regime': args.regime, 'recommended_sectors': [], 'top_momentum_sectors': []}
        print(f"  市场周期: {args.regime} (无行业数据)")
    
    # 4. 风险与因子分析
    print("\n[4/6] 风险与因子分析...")
    
    # 生成合成投资组合
    portfolio_returns = generate_synthetic_portfolio(
        n_assets=args.n_assets,
        n_days=args.days
    )
    
    # 计算风险指标
    portfolio_daily_returns = portfolio_returns.mean(axis=1)
    risk_metrics = risk_dashboard.calculate_all(
        portfolio_daily_returns.values,
        portfolio_value=args.portfolio_value
    )
    print(f"  VaR(95%): {risk_metrics['var_95']:.2%}")
    print(f"  最大回撤: {risk_metrics['max_drawdown']:.2%}")
    print(f"  夏普比率: {risk_metrics['sharpe_ratio']:.2f}")
    
    # 压力测试
    n_assets = portfolio_returns.shape[1]
    weights = np.ones(n_assets) / n_assets
    vols = portfolio_returns.std().values
    corr = portfolio_returns.corr().values
    
    pressure_results = stress_tester.run_all_scenarios(
        args.portfolio_value, weights, vols, corr
    )
    
    # 多因子分析
    factor_df = pd.DataFrame({
        'PB': np.random.uniform(0.5, 15, args.days),
        'PE': np.random.uniform(5, 50, args.days),
        'Revenue_Growth': np.random.uniform(-0.2, 0.5, args.days),
        'ROE': np.random.uniform(0.05, 0.30, args.days),
        'Momentum_1M': portfolio_daily_returns.rolling(21).mean(),
        'Momentum_3M': portfolio_daily_returns.rolling(63).mean(),
        'Volatility_20D': portfolio_daily_returns.rolling(20).std() * np.sqrt(252),
    }).dropna()
    
    X_factors, y_target, feature_names = factor_model.prepare_data(
        factor_df, target_col='Momentum_3M'
    )
    factor_weights = factor_model.optimize_weights(X_factors, y_target[:len(X_factors)])
    factor_results = factor_model.backtest(X_factors, y_target[:len(X_factors)])
    
    print(f"  因子数: {len(factor_weights)}")
    print(f"  IC均值: {factor_results['ic_mean']:.3f}")
    
    # 5. 生成配置建议
    print("\n[5/6] 生成配置建议...")
    
    recommendations = analyzer.generate_allocation_recommendations(
        investor_profile={'type': 'institutional'},
        target_return=0.15,
        risk_tolerance=0.6
    )
    
    print(f"  生成 {len(recommendations)} 条配置建议")
    
    # 6. 生成报告
    print("\n[6/6] 生成分析报告...")
    
    analysis_result = analyzer.run_comprehensive_analysis()
    
    report_path = report_gen.generate_comprehensive_report(
        analysis_result,
        risk_metrics=risk_metrics,
        factor_analysis=factor_weights,
        pressure_tests=pressure_results
    )
    
    summary_path = report_gen.generate_summary_json(analysis_result)
    
    print(f"  HTML报告: {report_path}")
    print(f"  JSON摘要: {summary_path}")
    
    # 打印关键结论
    print("\n" + "="*70)
    print("  关键结论")
    print("="*70)
    
    print("\n【投资热点】")
    for i, h in enumerate(hotspots[:5], 1):
        print(f"  {i}. {h.sector} - 得分:{h.score:.0f}, 预期收益:{h.expected_return:.1%}")
    
    print("\n【配置建议】")
    for r in recommendations[:5]:
        print(f"  [{r.action.upper()}] {r.target_weight:.1%} - {r.rationale}")
    
    print("\n【风险预警】")
    for alert in risk_dashboard.alerts:
        print(f"  [{alert['severity'].upper()}] {alert['message']}")
    
    print("\n【压力测试】")
    for scenario, result in list(pressure_results.items())[:3]:
        print(f"  {result['scenario']}: VaR=${result['var_95']:,.0f}")
    
    print("\n" + "="*70)
    print("  分析完成!")
    print("="*70 + "\n")
    
    return {
        'report_path': report_path,
        'summary_path': summary_path,
        'hotspots': [h.to_dict() for h in hotspots],
        'recommendations': [r.to_dict() for r in recommendations],
        'risk_metrics': risk_metrics,
        'factor_weights': factor_weights
    }


def main():
    parser = argparse.ArgumentParser(description='全球资本投资分析系统')
    parser.add_argument('--markets', type=str, default='US,CN,HK', help='市场列表')
    parser.add_argument('--days', type=int, default=365, help='数据天数')
    parser.add_argument('--n-funds', type=int, default=5, help='每种基金类型数量')
    parser.add_argument('--n-assets', type=int, default=20, help='组合资产数')
    parser.add_argument('--portfolio-value', type=float, default=10000000, help='组合价值(美元)')
    parser.add_argument('--factor-method', type=str, default='ic_weighting', 
                       choices=['ic_weighting', 'ml_ranking', 'optimization'])
    parser.add_argument('--regime', type=str, default='expansion',
                       choices=['early_cycle', 'expansion', 'late_cycle', 'recession'])
    
    args = parser.parse_args()
    run_analysis(args)


if __name__ == '__main__':
    main()
