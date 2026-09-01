#!/usr/bin/env python3
"""
Report Generator - 投资分析报告生成器

生成专业格式的投资分析报告，包括：
- 市场概览
- 热点分析
- 基金排名
- 配置建议
- 风险提示
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class InvestmentReportGenerator:
    """投资分析报告生成器"""
    
    def __init__(self, output_dir: str = './reports'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_comprehensive_report(
        self,
        analysis_result: Dict,
        risk_metrics: Dict = None,
        factor_analysis: Dict = None,
        pressure_tests: Dict = None
    ) -> str:
        """
        生成综合投资分析报告
        
        Returns:
            报告文件路径
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = self.output_dir / f'investment_report_{timestamp}.html'
        
        # 生成HTML报告
        html_content = self._generate_html(analysis_result, risk_metrics, factor_analysis, pressure_tests)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"报告已生成: {report_path}")
        return str(report_path)
    
    def _generate_html(self, result: Dict, risk: Dict, factors: Dict, stress: Dict) -> str:
        """生成HTML报告内容"""
        
        # 提取关键数据
        hotspots = result.get('hotspots', [])
        recommendations = result.get('recommendations', [])
        market_summary = result.get('market_summary', {})
        fund_analysis = result.get('fund_analysis', [])
        
        # 生成热点表格
        hotspot_rows = ''
        for i, h in enumerate(hotspots[:10], 1):
            hotspot_rows += f'''
            <tr>
                <td>{i}</td>
                <td><strong>{h['sector']}</strong></td>
                <td>{h['score']:.0f}</td>
                <td>{h['expected_return']:.1%}</td>
                <td><span class="risk-{h['risk_level']}">{h['risk_level']}</span></td>
                <td>{', '.join(h['key_themes'][:3])}</td>
                <td>{h['timeframe']}</td>
            </tr>
            '''
        
        # 生成配置建议表格
        alloc_rows = ''
        for r in recommendations[:8]:
            action_class = 'overweight' if r['action'] == 'overweight' else ('underweight' if r['action'] == 'underweight' else 'neutral')
            alloc_rows += f'''
            <tr>
                <td>{r['target_weight']:.1%}</td>
                <td>{r['current_weight']:.1%}</td>
                <td><span class="action-{action_class}">{r['action'].upper()}</span></td>
                <td>{r['confidence']:.0%}</td>
                <td>{r['rationale']}</td>
                <td>{r['risk_adjusted_return']:.2%}</td>
            </tr>
            '''
        
        # 生成基金分析表格
        fund_rows = ''
        for f in fund_analysis[:10]:
            fund_rows += f'''
            <tr>
                <td>{f.get('name', 'N/A')}</td>
                <td>{f.get('fund_type', 'N/A')}</td>
                <td>${f.get('aum_usd_billion', 0):.1f}B</td>
                <td>{f.get('returns_1y', 0):.1%}</td>
                <td>{f.get('sharpe_ratio', 0):.2f}</td>
                <td>{f.get('max_drawdown', 0):.1%}</td>
            </tr>
            '''
        
        # 生成风险指标
        risk_html = ''
        if risk:
            for metric, value in risk.items():
                if isinstance(value, float):
                    risk_html += f'<tr><td>{metric}</td><td>{value:.4f}</td></tr>'
                else:
                    risk_html += f'<tr><td>{metric}</td><td>{value}</td></tr>'
        
        # 生成压力测试结果
        stress_html = ''
        if stress:
            for scenario, result in stress.items():
                stress_html += f'''
                <tr>
                    <td><strong>{result['scenario']}</strong></td>
                    <td>${result['var_95']:,.0f}</td>
                    <td>${result['cvar_95']:,.0f}</td>
                    <td>${result['max_loss']:,.0f}</td>
                    <td>{result['prob_5pct_loss']:.1f}%</td>
                </tr>
                '''
        
        # 生成因子分析
        factor_html = ''
        if factors:
            sorted_factors = sorted(factors.items(), key=lambda x: abs(x[1]), reverse=True)[:10]
            for factor, weight in sorted_factors:
                factor_html += f'<tr><td>{factor}</td><td>{weight:.4f}</td></tr>'
        
        report_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>全球资本投资分析报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
        .header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header .subtitle {{ opacity: 0.9; font-size: 1.1em; }}
        .card {{ 
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .card h2 {{ 
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
        }}
        .metrics-grid {{ 
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .metric-box {{ 
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .metric-value {{ 
            font-size: 1.8em;
            font-weight: bold;
            color: #667eea;
        }}
        .metric-label {{ font-size: 0.9em; color: #666; margin-top: 5px; }}
        table {{ 
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{ 
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        th {{ 
            background: #f8f9fa;
            font-weight: 600;
            color: #555;
        }}
        tr:hover {{ background: #f8f9fa; }}
        .risk-very_low {{ color: #28a745; }}
        .risk-low {{ color: #20c997; }}
        .risk-medium {{ color: #ffc107; }}
        .risk-high {{ color: #fd7e14; }}
        .risk-very_high {{ color: #dc3545; }}
        .action-overweight {{ color: #28a745; font-weight: bold; }}
        .action-underweight {{ color: #dc3545; }}
        .action-neutral {{ color: #6c757d; }}
        .summary-box {{ 
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .footer {{ 
            text-align: center;
            padding: 30px;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>全球资本投资分析报告</h1>
            <div class="subtitle">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        
        <div class="card">
            <h2>市场概览</h2>
            <div class="metrics-grid">
                <div class="metric-box">
                    <div class="metric-value">{market_summary.get('total_funds_analyzed', 0)}</div>
                    <div class="metric-label">分析基金数</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{market_summary.get('avg_return_1y', 0):.1%}</div>
                    <div class="metric-label">平均收益率(1年)</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{market_summary.get('avg_sharpe', 0):.2f}</div>
                    <div class="metric-label">平均夏普比率</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{market_summary.get('market_sentiment', 'neutral').upper()}</div>
                    <div class="metric-label">市场情绪</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>投资热点 Top 10</h2>
            <table>
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>赛道</th>
                        <th>得分</th>
                        <th>预期收益</th>
                        <th>风险等级</th>
                        <th>核心主题</th>
                        <th>投资周期</th>
                    </tr>
                </thead>
                <tbody>
                    {hotspot_rows}
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <h2>资产配置建议</h2>
            <table>
                <thead>
                    <tr>
                        <th>目标权重</th>
                        <th>当前权重</th>
                        <th>操作</th>
                        <th>置信度</th>
                        <th>理由</th>
                        <th>风险调整收益</th>
                    </tr>
                </thead>
                <tbody>
                    {alloc_rows}
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <h2>基金表现分析</h2>
            <table>
                <thead>
                    <tr>
                        <th>基金名称</th>
                        <th>类型</th>
                        <th>规模(亿美元)</th>
                        <th>1年收益</th>
                        <th>夏普比率</th>
                        <th>最大回撤</th>
                    </tr>
                </thead>
                <tbody>
                    {fund_rows}
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <h2>风险指标</h2>
            <table>
                <thead>
                    <tr>
                        <th>指标</th>
                        <th>数值</th>
                    </tr>
                </thead>
                <tbody>
                    {risk_html if risk else '<tr><td colspan="2">暂无数据</td></tr>'}
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <h2>压力测试结果</h2>
            <table>
                <thead>
                    <tr>
                        <th>情景</th>
                        <th>VaR(95%)</th>
                        <th>CVaR(95%)</th>
                        <th>最坏损失</th>
                        <th>5%概率损失</th>
                    </tr>
                </thead>
                <tbody>
                    {stress_html if stress else '<tr><td colspan="5">暂无数据</td></tr>'}
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <h2>因子分析</h2>
            <table>
                <thead>
                    <tr>
                        <th>因子</th>
                        <th>权重</th>
                    </tr>
                </thead>
                <tbody>
                    {factor_html if factors else '<tr><td colspan="2">暂无数据</td></tr>'}
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p>本报告由全球资本投资分析系统自动生成</p>
            <p>数据来源：Yahoo Finance、模拟数据 | 分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
    </div>
</body>
</html>'''
        
        return report_html
    
    def generate_summary_json(self, result: Dict) -> str:
        """生成JSON摘要"""
        summary = {
            'generated_at': datetime.now().isoformat(),
            'market_summary': result.get('market_summary', {}),
            'top_hotspots': [h['sector'] for h in result.get('hotspots', [])[:5]],
            'key_recommendations': [
                {
                    'sector': h['sector'],
                    'action': 'overweight' if h['score'] > 70 else 'neutral',
                    'expected_return': h['expected_return']
                }
                for h in result.get('hotspots', [])[:5]
            ],
            'risk_level': 'medium'
        }
        
        output_path = self.output_dir / f'summary_{datetime.now().strftime("%Y%m%d")}.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        return str(output_path)


def main():
    """测试报告生成"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("="*70)
    print("报告生成器测试")
    print("="*70)
    
    generator = InvestmentReportGenerator()
    
    # 模拟分析结果
    mock_result = {
        'hotspots': [
            {'sector': 'AI/ML', 'score': 85, 'expected_return': 0.25, 'risk_level': 'high', 'key_themes': ['大模型', 'Agent', 'AIGC'], 'timeframe': 'long_term'},
            {'sector': 'Clean Energy', 'score': 78, 'expected_return': 0.18, 'risk_level': 'medium', 'key_themes': ['储能', '氢能'], 'timeframe': 'medium_term'},
            {'sector': 'Biotech', 'score': 72, 'expected_return': 0.22, 'risk_level': 'high', 'key_themes': ['基因编辑', 'mRNA'], 'timeframe': 'long_term'},
        ],
        'recommendations': [
            {'target_weight': 0.15, 'current_weight': 0.05, 'action': 'overweight', 'confidence': 0.85, 'rationale': '高景气赛道', 'risk_adjusted_return': 0.30},
            {'target_weight': 0.10, 'current_weight': 0.12, 'action': 'neutral', 'confidence': 0.70, 'rationale': '平衡配置', 'risk_adjusted_return': 0.18},
        ],
        'market_summary': {
            'total_funds_analyzed': 50,
            'avg_return_1y': 0.12,
            'avg_sharpe': 1.2,
            'market_sentiment': 'bullish'
        },
        'fund_analysis': [
            {'name': 'Sequoia Capital', 'fund_type': 'VC', 'aum_usd_billion': 85.5, 'returns_1y': 0.28, 'sharpe_ratio': 1.8, 'max_drawdown': -0.15},
        ]
    }
    
    # 生成报告
    report_path = generator.generate_comprehensive_report(mock_result)
    print(f"\n报告已生成: {report_path}")
    
    summary_path = generator.generate_summary_json(mock_result)
    print(f"摘要已生成: {summary_path}")
    
    print("\n" + "="*70)


if __name__ == '__main__':
    main()
