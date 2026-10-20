"""
绩效报告模块

生成回测绩效报告，支持 HTML 输出
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import json
import os


class PerformanceReport:
    """
    绩效报告生成器
    
    基于回测结果生成绩效分析报告。
    
    支持输出：
    - 控制台摘要
    - HTML 报告
    - JSON 数据
    """
    
    def __init__(self, output_dir: str = './output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate(self, backtest_result: Dict, title: str = "策略回测报告") -> str:
        """
        生成完整报告
        
        Args:
            backtest_result: 回测引擎输出结果
            title: 报告标题
        
        Returns:
            报告文件路径
        """
        metrics = backtest_result.get('metrics', {})
        equity_curve = backtest_result.get('equity_curve', pd.Series())
        trades = backtest_result.get('trades', pd.DataFrame())
        
        # 生成 HTML 报告
        html_path = self._generate_html(backtest_result, metrics, equity_curve, trades, title)
        
        # 生成 JSON 报告
        json_path = self._generate_json(metrics, trades)
        
        print(f"[报告] HTML 报告: {html_path}")
        print(f"[报告] JSON 数据: {json_path}")
        
        return html_path
    
    def _generate_html(self, backtest_result: Dict, metrics: Dict, equity_curve: pd.Series,
                       trades: pd.DataFrame, title: str) -> str:
        """生成 HTML 报告"""
        
        # 构建指标表格
        metrics_rows = self._build_metrics_rows(metrics)
        
        # 构建交易统计
        trade_stats = metrics.get('trade_stats', {})
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               background: #0f172a; color: #e2e8f0; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #f59e0b; margin-bottom: 8px; font-size: 28px; }}
        .subtitle {{ color: #94a3b8; margin-bottom: 30px; font-size: 14px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .card {{ background: #1e293b; border-radius: 12px; padding: 24px; border: 1px solid #334155; }}
        .card h3 {{ color: #f59e0b; font-size: 14px; text-transform: uppercase; margin-bottom: 16px; letter-spacing: 1px; }}
        .metric {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #334155; }}
        .metric:last-child {{ border-bottom: none; }}
        .metric-label {{ color: #94a3b8; font-size: 14px; }}
        .metric-value {{ color: #f1f5f9; font-weight: 600; font-size: 14px; }}
        .positive {{ color: #22c55e; }}
        .negative {{ color: #ef4444; }}
        .highlight {{ font-size: 36px; font-weight: 700; margin: 8px 0; }}
        .chart-placeholder {{ background: #1e293b; border-radius: 12px; padding: 40px; text-align: center; 
                              border: 1px solid #334155; margin-bottom: 20px; }}
        .chart-placeholder pre {{ text-align: left; font-size: 12px; color: #94a3b8; overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        th {{ background: #334155; padding: 10px 12px; text-align: left; color: #f59e0b; font-weight: 600; }}
        td {{ padding: 8px 12px; border-bottom: 1px solid #334155; }}
        tr:hover {{ background: #1e293b; }}
        .footer {{ text-align: center; color: #64748b; margin-top: 40px; padding-top: 20px; border-top: 1px solid #334155; font-size: 12px; }}
        .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }}
        .badge-green {{ background: #22c55e20; color: #22c55e; }}
        .badge-red {{ background: #ef444420; color: #ef4444; }}
        .badge-yellow {{ background: #f59e0b20; color: #f59e0b; }}
    </style>
</head>
<body>
<div class="container">
    <h1>📊 {title}</h1>
    <p class="subtitle">策略: {metrics.get('strategy_name', backtest_result.get('strategy_name', 'N/A'))} | 
    回测期间: {metrics.get('start_date', 'N/A')} ~ {metrics.get('end_date', 'N/A')}</p>
    
    <div class="grid">
        <div class="card">
            <h3>📈 收益概览</h3>
            <div class="metric">
                <span class="metric-label">总收益率</span>
                <span class="metric-value {'positive' if metrics.get('total_return', 0) >= 0 else 'negative'}">
                    {metrics.get('total_return', 0):.2%}
                </span>
            </div>
            <div class="metric">
                <span class="metric-label">年化收益率</span>
                <span class="metric-value {'positive' if metrics.get('annual_return', 0) >= 0 else 'negative'}">
                    {metrics.get('annual_return', 0):.2%}
                </span>
            </div>
            <div class="metric">
                <span class="metric-label">初始资金</span>
                <span class="metric-value">¥{metrics.get('initial_capital', 0):,.2f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">最终资金</span>
                <span class="metric-value">¥{metrics.get('final_capital', 0):,.2f}</span>
            </div>
        </div>
        
        <div class="card">
            <h3>⚡ 风险指标</h3>
            <div class="metric">
                <span class="metric-label">夏普比率</span>
                <span class="metric-value">{metrics.get('sharpe_ratio', 0):.4f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Sortino 比率</span>
                <span class="metric-value">{metrics.get('sortino_ratio', 0):.4f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">Calmar 比率</span>
                <span class="metric-value">{metrics.get('calmar_ratio', 0):.4f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">波动率</span>
                <span class="metric-value">{metrics.get('volatility', 0):.2%}</span>
            </div>
        </div>
        
        <div class="card">
            <h3>🛡️ 回撤控制</h3>
            <div class="metric">
                <span class="metric-label">最大回撤</span>
                <span class="metric-value negative">{metrics.get('max_drawdown', 0):.2%}</span>
            </div>
            <div class="metric">
                <span class="metric-label">回撤持续期</span>
                <span class="metric-value">{metrics.get('max_drawdown_duration', 0)} 天</span>
            </div>
        </div>
        
        <div class="card">
            <h3>🎯 交易统计</h3>
            <div class="metric">
                <span class="metric-label">总交易次数</span>
                <span class="metric-value">{trade_stats.get('total_trades', 0)}</span>
            </div>
            <div class="metric">
                <span class="metric-label">胜率</span>
                <span class="metric-value">
                    <span class="badge {'badge-green' if trade_stats.get('win_rate', 0) >= 0.5 else 'badge-red'}">
                        {trade_stats.get('win_rate', 0):.1%}
                    </span>
                </span>
            </div>
            <div class="metric">
                <span class="metric-label">盈亏比</span>
                <span class="metric-value">{trade_stats.get('profit_factor', 0):.4f}</span>
            </div>
            <div class="metric">
                <span class="metric-label">总盈亏</span>
                <span class="metric-value {'positive' if trade_stats.get('total_pnl', 0) >= 0 else 'negative'}">
                    ¥{trade_stats.get('total_pnl', 0):,.2f}
                </span>
            </div>
        </div>
    </div>
    
    <div class="chart-placeholder">
        <h3 style="color: #f59e0b; margin-bottom: 16px;">📉 权益曲线 (ASCII)</h3>
        <pre>{self._ascii_chart(equity_curve)}</pre>
    </div>
    
    <div class="card" style="margin-bottom: 20px;">
        <h3>📋 最近交易记录</h3>
        {self._generate_trade_table(trades)}
    </div>
    
    <div class="footer">
        <p>量化交易策略库 v1.0 | 生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>本报告仅供参考，不构成投资建议</p>
    </div>
</div>
</body>
</html>"""
        
        filepath = os.path.join(self.output_dir, 'backtest_report.html')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return filepath
    
    def _build_metrics_rows(self, metrics: Dict) -> str:
        """构建指标 HTML 行"""
        rows = ""
        for key, value in metrics.items():
            if isinstance(value, (int, float)) and key not in ['trade_stats']:
                label = key.replace('_', ' ').title()
                if isinstance(value, float):
                    val_str = f"{value:.4f}"
                else:
                    val_str = str(value)
                rows += f'<div class="metric"><span class="metric-label">{label}</span><span class="metric-value">{val_str}</span></div>\n'
        return rows
    
    def _ascii_chart(self, series: pd.Series, width: int = 80, height: int = 20) -> str:
        """生成 ASCII 图表"""
        if len(series) == 0:
            return "无数据"
        
        # 降采样到 width 个数据点
        if len(series) > width:
            indices = np.linspace(0, len(series) - 1, width).astype(int)
            values = series.iloc[indices].values
        else:
            values = series.values
        
        # 归一化到 0-height
        min_val = np.min(values)
        max_val = np.max(values)
        
        if max_val == min_val:
            normalized = np.full_like(values, height // 2)
        else:
            normalized = ((values - min_val) / (max_val - min_val) * (height - 1)).astype(int)
        
        # 构建字符图
        lines = []
        for row in range(height - 1, -1, -1):
            line = ""
            for col in range(len(normalized)):
                if normalized[col] == row:
                    line += "█"
                elif normalized[col] > row and (col == 0 or normalized[col-1] <= row):
                    line += "▄"
                else:
                    line += " "
            lines.append(line)
        
        # 添加标签
        lines.append(f"{'':─<{width}}")
        lines.append(f" ¥{min_val:>10,.0f}{'':>{width-30}}¥{max_val:>10,.0f}")
        
        return "\n".join(lines)
    
    def _generate_trade_table(self, trades: pd.DataFrame, max_rows: int = 20) -> str:
        """生成交易表格 HTML"""
        if len(trades) == 0:
            return "<p style='color: #94a3b8;'>暂无交易记录</p>"
        
        # 取最近 N 条
        recent = trades.tail(max_rows)
        
        rows = ""
        for _, trade in recent.iterrows():
            action = trade.get('action', '')
            pnl = trade.get('pnl', 0)
            pnl_class = 'positive' if pnl >= 0 else 'negative'
            
            rows += f"""<tr>
                <td>{trade.get('timestamp', '')}</td>
                <td>{trade.get('symbol', '')}</td>
                <td><span class="badge {'badge-green' if action in ['BUY', 'SHORT'] else 'badge-red'}">{action}</span></td>
                <td>{trade.get('quantity', 0):.4f}</td>
                <td>¥{trade.get('price', 0):.2f}</td>
                <td class="{pnl_class}">¥{pnl:.2f}</td>
            </tr>"""
        
        return f"""<table>
            <thead><tr>
                <th>时间</th><th>标的</th><th>操作</th><th>数量</th><th>价格</th><th>盈亏</th>
            </tr></thead>
            <tbody>{rows}</tbody>
        </table>"""
    
    def _generate_json(self, metrics: Dict, trades: pd.DataFrame) -> str:
        """生成 JSON 报告"""
        # 处理不可 JSON 序列化的字段
        clean_metrics = {}
        for key, value in metrics.items():
            if isinstance(value, (int, float, str, bool)):
                clean_metrics[key] = value
            elif isinstance(value, dict):
                clean_metrics[key] = {k: v for k, v in value.items() if isinstance(v, (int, float, str, bool))}
        
        report = {
            'metrics': clean_metrics,
            'trade_count': len(trades),
        }
        
        filepath = os.path.join(self.output_dir, 'backtest_report.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        return filepath
    
    def print_summary(self, metrics: Dict):
        """打印控制台摘要"""
        print(f"\n{'='*60}")
        print(f"  📊 绩效报告摘要")
        print(f"{'='*60}")
        print(f"  总收益率:     {metrics.get('total_return', 0):.2%}")
        print(f"  年化收益率:   {metrics.get('annual_return', 0):.2%}")
        print(f"  夏普比率:     {metrics.get('sharpe_ratio', 0):.4f}")
        print(f"  最大回撤:     {metrics.get('max_drawdown', 0):.2%}")
        print(f"  Sortino:      {metrics.get('sortino_ratio', 0):.4f}")
        print(f"  Calmar:       {metrics.get('calmar_ratio', 0):.4f}")
        
        ts = metrics.get('trade_stats', {})
        if ts:
            print(f"\n  交易统计:")
            print(f"    总交易: {ts.get('total_trades', 0)}")
            print(f"    胜率:   {ts.get('win_rate', 0):.1%}")
            print(f"    盈亏比: {ts.get('profit_factor', 0):.2f}")
        print(f"{'='*60}\n")
