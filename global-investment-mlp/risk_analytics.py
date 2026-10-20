#!/usr/bin/env python3
"""
Risk Analytics Engine - 风险分析引擎

功能：
- VaR计算 (Value at Risk)
- 压力测试
- 相关性分析
- 组合风险分解
- 风险预警
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Optional
import logging
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class RiskMetrics:
    """风险指标计算"""
    
    @staticmethod
    def calculate_var(returns: np.ndarray, confidence: float = 0.95, 
                      method: str = 'historical') -> float:
        """
        计算VaR
        
        Args:
            returns: 收益率序列
            confidence: 置信水平
            method: 计算方法 ('historical', 'parametric', 'monte_carlo')
        """
        if method == 'historical':
            var = np.percentile(returns, (1 - confidence) * 100)
        elif method == 'parametric':
            mu, sigma = returns.mean(), returns.std()
            var = mu + stats.norm.ppf(1 - confidence) * sigma
        elif method == 'monte_carlo':
            simulated = np.random.normal(returns.mean(), returns.std(), 10000)
            var = np.percentile(simulated, (1 - confidence) * 100)
        else:
            var = np.percentile(returns, (1 - confidence) * 100)
        
        return abs(var)
    
    @staticmethod
    def calculate_cvar(returns: np.ndarray, confidence: float = 0.95) -> float:
        """计算CVaR (Conditional VaR / Expected Shortfall)"""
        var = RiskMetrics.calculate_var(returns, confidence)
        cvar = returns[returns <= -var].mean()
        return abs(cvar)
    
    @staticmethod
    def calculate_max_drawdown(returns: np.ndarray) -> Dict:
        """计算最大回撤"""
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        
        max_dd = drawdown.min()
        max_dd_idx = drawdown.argmin()
        
        # 找到回撤起始点
        peak_idx = np.argmax(cumulative[:max_dd_idx+1])
        
        return {
            'max_drawdown': float(max_dd),
            'peak_date': int(peak_idx),
            'trough_date': int(max_dd_idx),
            'recovery_periods': None  # 需要更多数据
        }
    
    @staticmethod
    def calculate_sharpe(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """计算夏普比率"""
        excess_return = returns - risk_free_rate / 252
        sharpe = np.sqrt(252) * excess_return.mean() / (excess_return.std() + 1e-10)
        return float(sharpe)
    
    @staticmethod
    def calculate_sortino(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
        """计算索提诺比率"""
        excess_return = returns - risk_free_rate / 252
        downside_returns = excess_return[excess_return < 0]
        
        if len(downside_returns) == 0:
            return float('inf')
        
        downside_std = np.sqrt(np.mean(downside_returns ** 2))
        sortino = np.sqrt(252) * excess_return.mean() / (downside_std + 1e-10)
        return float(sortino)
    
    @staticmethod
    def calculate_calmar(returns: np.ndarray, max_drawdown: float) -> float:
        """计算Calmar比率"""
        annual_return = (1 + returns.mean()) ** 252 - 1
        calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        return float(calmar)


class CorrelationAnalyzer:
    """相关性分析"""
    
    def __init__(self):
        self.correlation_matrix = None
        self.clustering_result = None
    
    def analyze(self, returns_matrix: np.ndarray, 
                asset_names: List[str] = None) -> Dict:
        """
        分析资产相关性
        
        Returns:
            相关性矩阵、聚类结果、分散化评分
        """
        df = pd.DataFrame(returns_matrix, columns=asset_names or [f'Asset_{i}' for i in range(len(returns_matrix[0]))])
        
        # 相关性矩阵
        corr_matrix = df.corr().values
        self.correlation_matrix = corr_matrix
        
        # 平均相关性
        n_assets = len(corr_matrix)
        avg_corr = (corr_matrix.sum() - np.diag(corr_matrix).sum()) / (n_assets * (n_assets - 1))
        
        # 集中度指标
        corr_concentration = np.linalg.norm(corr_matrix) / (n_assets * n_assets)
        
        # 分散化评分 (0-100，越高越好)
        diversification_score = max(0, min(100, (1 - avg_corr) * 100))
        
        return {
            'average_correlation': float(avg_corr),
            'correlation_concentration': float(corr_concentration),
            'diversification_score': float(diversification_score),
            'n_assets': n_assets,
            'corr_matrix': corr_matrix
        }
    
    def detect_regime_change(self, recent_corr: np.ndarray, 
                             historical_corr: np.ndarray, 
                             window: int = 60) -> bool:
        """检测相关性 regime 变化"""
        # 计算差异
        diff = np.abs(recent_corr - historical_corr)
        # 排除对角线
        np.fill_diagonal(diff, 0)
        
        # 判断是否显著变化
        threshold = 0.15
        change_detected = diff.mean() > threshold
        
        return bool(change_detected), float(diff.mean())


class StressTester:
    """压力测试"""
    
    SCENARIOS = {
        '2008_crisis': {
            'name': '2008年金融危机',
            'equity shock': -0.50,
            'credit_spread_widen': 300,
            'volatility_spike': 2.5,
            'correlation_increase': 0.3
        },
        '2020_covid': {
            'name': '2020年新冠疫情',
            'equity shock': -0.35,
            'credit_spread_widen': 200,
            'volatility_spike': 2.0,
            'correlation_increase': 0.25
        },
        'gradual_rise_rates': {
            'name': '利率缓慢上升',
            'equity shock': -0.15,
            'credit_spread_widen': 50,
            'volatility_spike': 1.2,
            'correlation_increase': 0.1
        },
        'sudden_rate_hike': {
            'name': '突然加息',
            'equity shock': -0.25,
            'credit_spread_widen': 150,
            'volatility_spike': 1.8,
            'correlation_increase': 0.2
        },
        'recession': {
            'name': '经济衰退',
            'equity shock': -0.30,
            'credit_spread_widen': 250,
            'volatility_spike': 1.5,
            'correlation_increase': 0.15
        }
    }
    
    def __init__(self):
        self.results = {}
    
    def stress_test(self, portfolio_value: float, 
                    asset_weights: np.ndarray,
                    asset_volatilities: np.ndarray,
                    correlation_matrix: np.ndarray,
                    scenario: str = '2008_crisis') -> Dict:
        """
        执行压力测试
        
        Returns:
            压力测试结果
        """
        if scenario not in self.SCENARIOS:
            raise ValueError(f"未知情景: {scenario}")
        
        s = self.SCENARIOS[scenario]
        
        # 模拟资产收益
        np.random.seed(42)
        n_assets = len(asset_weights)
        
        # 基础收益
        base_returns = np.random.multivariate_normal(
            mean=np.zeros(n_assets),
            cov=self._build_stress_cov(asset_volatilities, correlation_matrix, s),
            size=10000
        )
        
        # 应用冲击
        shock_returns = base_returns + np.array([s['equity shock']] * n_assets)
        
        # 组合收益
        portfolio_returns = shock_returns @ asset_weights
        
        # 计算损失（取绝对值，表示损失金额）
        var_95 = abs(np.percentile(portfolio_returns, 5))
        cvar_95 = abs(portfolio_returns[portfolio_returns <= -var_95].mean() if len(portfolio_returns[portfolio_returns <= -var_95]) > 0 else portfolio_returns.mean())
        
        max_loss = abs(portfolio_returns.min())
        p5_loss = portfolio_returns[portfolio_returns < -0.1].size / len(portfolio_returns) * 100
        
        result = {
            'scenario': s['name'],
            'scenario_key': scenario,
            'portfolio_value': portfolio_value,
            'var_95': float(var_95 * portfolio_value),
            'cvar_95': float(cvar_95 * portfolio_value),
            'max_loss': float(max_loss * portfolio_value),
            'prob_5pct_loss': float(p5_loss),
            'shock_parameters': s
        }
        
        self.results[scenario] = result
        return result
    
    def _build_stress_cov(self, vols: np.ndarray, corr: np.ndarray, 
                          scenario: Dict) -> np.ndarray:
        """构建压力协方差矩阵"""
        stressed_vols = vols * scenario['volatility_spike']
        stressed_corr = corr + scenario['correlation_increase']
        np.fill_diagonal(stressed_corr, 1)
        
        # 确保正定
        eigvals = np.linalg.eigvalsh(stressed_corr)
        if eigvals.min() < 0:
            stressed_corr += (-eigvals.min() + 0.01) * np.eye(len(stressed_corr))
        
        return np.outer(stressed_vols, stressed_vols) * stressed_corr
    
    def run_all_scenarios(self, portfolio_value: float,
                         asset_weights: np.ndarray,
                         asset_volatilities: np.ndarray,
                         correlation_matrix: np.ndarray) -> Dict:
        """运行所有压力测试情景"""
        all_results = {}
        
        for scenario in self.SCENARIOS.keys():
            result = self.stress_test(
                portfolio_value, asset_weights, asset_volatilities,
                correlation_matrix, scenario
            )
            all_results[scenario] = result
        
        return all_results


class RiskDashboard:
    """风险仪表盘"""
    
    def __init__(self):
        self.metrics = {}
        self.alerts = []
    
    def calculate_all(self, returns: np.ndarray, 
                      portfolio_value: float = 10000000) -> Dict:
        """计算所有风险指标"""
        metrics = {
            'var_95': RiskMetrics.calculate_var(returns, 0.95),
            'var_99': RiskMetrics.calculate_var(returns, 0.99),
            'cvar_95': RiskMetrics.calculate_cvar(returns, 0.95),
            'max_drawdown': RiskMetrics.calculate_max_drawdown(returns)['max_drawdown'],
            'sharpe_ratio': RiskMetrics.calculate_sharpe(returns),
            'sortino_ratio': RiskMetrics.calculate_sortino(returns),
            'volatility_annual': float(returns.std() * np.sqrt(252)),
            'skewness': float(pd.Series(returns).skew()),
            'kurtosis': float(pd.Series(returns).kurtosis()),
            'calmar_ratio': 0  # 需要max_drawdown
        }
        
        metrics['calmar_ratio'] = RiskMetrics.calculate_calmar(
            returns, metrics['max_drawdown']
        )
        
        self.metrics = metrics
        
        # 生成预警
        self._generate_alerts(metrics)
        
        return metrics
    
    def _generate_alerts(self, metrics: Dict):
        """生成风险预警"""
        self.alerts = []
        
        if metrics['var_95'] > 0.05:
            self.alerts.append({
                'type': 'high_var',
                'message': f'VaR(95%)过高: {metrics["var_95"]:.1%}',
                'severity': 'high'
            })
        
        if metrics['sharpe_ratio'] < 0.5:
            self.alerts.append({
                'type': 'low_sharpe',
                'message': f'夏普比率过低: {metrics["sharpe_ratio"]:.2f}',
                'severity': 'medium'
            })
        
        if metrics['max_drawdown'] < -0.20:
            self.alerts.append({
                'type': 'high_drawdown',
                'message': f'最大回撤过大: {metrics["max_drawdown"]:.1%}',
                'severity': 'critical'
            })
        
        if metrics['skewness'] < -1:
            self.alerts.append({
                'type': 'negative_skew',
                'message': '收益分布负偏，尾部风险高',
                'severity': 'medium'
            })
    
    def get_summary(self) -> Dict:
        """获取风险摘要"""
        return {
            'metrics': self.metrics,
            'alerts': self.alerts,
            'risk_level': self._assess_risk_level()
        }
    
    def _assess_risk_level(self) -> str:
        """评估整体风险等级"""
        if not self.metrics:
            return 'unknown'
        
        score = 0
        score += min(30, self.metrics.get('var_95', 0) * 500)
        score += min(30, abs(self.metrics.get('max_drawdown', 0)) * 100)
        score += max(0, 30 - self.metrics.get('sharpe_ratio', 0) * 15)
        
        if score < 30:
            return 'low'
        elif score < 60:
            return 'medium'
        else:
            return 'high'


def main():
    """测试风险分析引擎"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("="*70)
    print("风险分析引擎测试")
    print("="*70)
    
    # 模拟投资组合收益
    np.random.seed(42)
    n_days = 500
    returns = np.random.normal(0.0005, 0.015, n_days)
    
    # 计算风险指标
    dashboard = RiskDashboard()
    metrics = dashboard.calculate_all(returns)
    
    print(f"\n风险指标:")
    print(f"  VaR(95%): {metrics['var_95']:.2%}")
    print(f"  CVaR(95%): {metrics['cvar_95']:.2%}")
    print(f"  最大回撤: {metrics['max_drawdown']:.2%}")
    print(f"  夏普比率: {metrics['sharpe_ratio']:.2f}")
    print(f"  索提诺比率: {metrics['sortino_ratio']:.2f}")
    print(f"  Calmar比率: {metrics['calmar_ratio']:.2f}")
    print(f"  年化波动率: {metrics['volatility_annual']:.1%}")
    
    print(f"\n风险预警:")
    for alert in dashboard.alerts:
        print(f"  [{alert['severity'].upper()}] {alert['message']}")
    
    # 压力测试
    print("\n【压力测试】")
    tester = StressTester()
    
    n_assets = 10
    weights = np.ones(n_assets) / n_assets
    vols = np.random.uniform(0.15, 0.30, n_assets)
    corr = np.random.uniform(0.3, 0.7, (n_assets, n_assets))
    corr = (corr + corr.T) / 2
    np.fill_diagonal(corr, 1)
    
    stress_results = tester.run_all_scenarios(10000000, weights, vols, corr)
    
    for scenario, result in stress_results.items():
        print(f"\n  {result['scenario']}:")
        print(f"    VaR(95%): ${result['var_95']:,.0f}")
        print(f"    最坏情况: ${result['max_loss']:,.0f}")
    
    print("\n" + "="*70)


if __name__ == '__main__':
    main()
