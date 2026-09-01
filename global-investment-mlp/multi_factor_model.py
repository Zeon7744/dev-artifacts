#!/usr/bin/env python3
"""
Multi-Factor Quantitative Model - 多因子量化模型

因子类别：
1. 价值因子 (Value)
2. 成长因子 (Growth)  
3. 动量因子 (Momentum)
4. 质量因子 (Quality)
5. 低波动因子 (Low Volatility)
6. 流动性因子 (Liquidity)
7. 宏观经济因子 (Macro)
8. 另类数据因子 (Alternative)

支持多市场：美股、A股、港股、欧洲、新兴市场
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.ensemble import GradientBoostingClassifier
import logging
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class MultiFactorModel:
    """多因子量化模型"""
    
    def __init__(self, 
                 factors: List[str] = None,
                 optimization_method: str = 'ic_weighting',
                 rebalance_frequency: str = 'quarterly'):
        """
        初始化多因子模型
        
        Args:
            factors: 因子列表
            optimization_method: 优化方法 ('ic_weighting', 'ml_ranking', 'optimization')
            rebalance_frequency: 调仓频率
        """
        self.factors = factors or self._get_default_factors()
        self.optimization_method = optimization_method
        self.rebalance_frequency = rebalance_frequency
        
        # 模型组件
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=0.95)
        self.factor_weights: Dict[str, float] = {}
        self.factor_ic: Dict[str, float] = {}
        
        # 回测结果
        self.backtest_results: Dict = {}
        
        logger.info(f"多因子模型初始化: {len(self.factors)}个因子")
    
    def _get_default_factors(self) -> List[str]:
        """获取默认因子列表"""
        return [
            # 价值因子
            'PB', 'PE', 'PS', 'PCF', 'EV_EBITDA', 'Dividend_Yield',
            # 成长因子
            'Revenue_Growth', 'Earnings_Growth', 'EBITDA_Growth', 'FCF_Growth',
            # 动量因子
            'Momentum_1M', 'Momentum_3M', 'Momentum_6M', 'Momentum_12M',
            # 质量因子
            'ROE', 'ROA', 'Gross_Margin', 'Net_Margin', 'Debt_to_Equity',
            # 低波动因子
            'Volatility_20D', 'Beta', 'Downside_Risk',
            # 流动性因子
            'Turnover_Ratio', 'Amihud_illiquidity',
            # 宏观因子
            'GDP_Growth', 'Inflation', 'Interest_Rate', 'Currency_Return'
        ]
    
    def prepare_data(self, df: pd.DataFrame, target_col: str = 'return_future_1m') -> Tuple:
        """
        准备因子数据
        
        Returns:
            (X_factors, y_target, feature_names)
        """
        # 选择因子列
        factor_cols = [c for c in self.factors if c in df.columns]
        
        if len(factor_cols) < 5:
            raise ValueError(f"可用因子不足: 需要至少5个，当前只有{len(factor_cols)}个")
        
        X = df[factor_cols].copy()
        
        # 处理缺失值
        X = X.fillna(X.median())
        X = X.replace([np.inf, -np.inf], 0)
        
        # 标准化
        X_scaled = self.scaler.fit_transform(X)
        
        # 提取目标变量
        y = df[target_col].values if target_col in df.columns else None
        
        return X_scaled, y, factor_cols
    
    def calculate_factor_ic(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        计算因子IC（Information Coefficient）
        
        IC = 因子值与未来收益的相关系数
        """
        ic_values = {}
        
        for i, factor in enumerate(self.factors):
            if i >= len(X[0]):
                break
            factor_values = X[:, i]
            
            # 计算Rank IC
            from scipy.stats import spearmanr
            ic, p_value = spearmanr(factor_values, y)
            ic_values[factor] = float(ic)
        
        self.factor_ic = ic_values
        return ic_values
    
    def optimize_weights(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        优化因子权重
        
        方法：
        1. IC加权：基于因子IC绝对值加权
        2. ML排名：基于梯度提升模型
        3. 组合优化：基于马科维茨组合优化
        """
        # 计算IC
        ic_values = self.calculate_factor_ic(X, y)
        
        if self.optimization_method == 'ic_weighting':
            # IC加权法
            abs_ic = {k: abs(v) for k, v in ic_values.items()}
            total_abs_ic = sum(abs_ic.values())
            
            if total_abs_ic > 0:
                self.factor_weights = {k: v/total_abs_ic for k, v in abs_ic.items()}
            else:
                # 均等权重
                self.factor_weights = {k: 1/len(ic_values) for k in ic_values}
        
        elif self.optimization_method == 'ml_ranking':
            # 机器学习方法
            model = GradientBoostingClassifier(n_estimators=100, random_state=42)
            model.fit(X, y)
            
            importances = model.feature_importances_
            total = importances.sum()
            self.factor_weights = {
                self.factors[i]: float(importances[i] / total) 
                for i in range(len(self.factors))
            }
        
        elif self.optimization_method == 'optimization':
            # 组合优化（简化版）
            # 最大化信息比率
            cov_matrix = np.cov(X.T)
            mean_returns = np.mean(y)
            
            # 随机搜索最优权重
            best_score = -np.inf
            best_weights = None
            
            for _ in range(1000):
                weights = np.random.dirichlet(np.ones(len(self.factors)))
                port_return = weights @ X.mean(axis=0)
                port_risk = np.sqrt(weights @ cov_matrix @ weights)
                score = port_return / (port_risk + 1e-10)
                
                if score > best_score:
                    best_score = score
                    best_weights = weights
            
            if best_weights is not None:
                self.factor_weights = {
                    self.factors[i]: float(best_weights[i])
                    for i in range(len(self.factors))
                }
        
        logger.info(f"因子权重优化完成: {self.optimization_method}")
        return self.factor_weights
    
    def calculate_factor_score(self, X: np.ndarray, weights: Dict[str, float] = None) -> np.ndarray:
        """
        计算综合因子得分
        
        Returns:
            因子得分数组
        """
        if weights is None:
            weights = self.factor_weights
        
        # 加权求和
        scores = np.zeros(X.shape[0])
        for i, factor in enumerate(self.factors):
            if i < len(X[0]) and factor in weights:
                scores += X[:, i] * weights[factor]
        
        # 标准化得分
        scores = (scores - scores.mean()) / (scores.std() + 1e-10)
        
        return scores
    
    def generate_rankings(self, X: np.ndarray) -> pd.DataFrame:
        """
        生成排名榜单
        
        Returns:
            DataFrame with scores and ranks
        """
        scores = self.calculate_factor_score(X)
        
        rankings = pd.DataFrame({
            'factor_score': scores,
            'rank': pd.Series(scores).rank(ascending=False).astype(int)
        })
        
        # 分档
        n_quintiles = 5
        rankings['quintile'] = pd.qcut(rankings['factor_score'], n_quintiles, labels=False, duplicates='drop') + 1
        
        return rankings
    
    def backtest(self, X: np.ndarray, y: np.ndarray, 
                 top_quintile_ret: bool = True) -> Dict:
        """
        回测多因子策略
        
        Args:
            top_quintile_ret: 是否只计算 Top 20% 收益
        """
        rankings = self.generate_rankings(X)
        
        # 分组收益
        quintile_returns = {}
        for q in range(1, 6):
            mask = rankings['quintile'] == q
            if top_quintile_ret and q > 3:
                quintile_returns[f'Q{q}'] = 0
            else:
                quintile_returns[f'Q{q}'] = y[mask].mean() if mask.sum() > 0 else 0
        
        # 多空策略收益
        long_return = quintile_returns.get('Q1', 0)
        short_return = quintile_returns.get('Q5', 0)
        long_short_return = long_return - short_return
        
        # 计算夏普比率
        excess_returns = y - 0.02 / 12  # 假设无风险利率2%
        sharpe = np.mean(excess_returns) / (np.std(excess_returns) + 1e-10) * np.sqrt(12)
        
        self.backtest_results = {
            'quintile_returns': quintile_returns,
            'long_short_return': long_short_return,
            'sharpe_ratio': sharpe,
            'ic_mean': np.mean([abs(v) for v in self.factor_ic.values()]),
            'n_factors': len(self.factors),
            'n_samples': len(y)
        }
        
        return self.backtest_results
    
    def get_factor_contribution(self) -> Dict[str, float]:
        """获取各因子贡献度"""
        contributions = {}
        total = sum(self.factor_weights.values())
        
        for factor, weight in self.factor_weights.items():
            ic = abs(self.factor_ic.get(factor, 0))
            contributions[factor] = weight * ic
        
        # 归一化
        total_contrib = sum(contributions.values())
        if total_contrib > 0:
            contributions = {k: v/total_contrib for k, v in contributions.items()}
        
        return contributions


class SectorRotationModel:
    """行业轮动模型"""
    
    def __init__(self):
        self.sector_momentum = {}
        self.sector_correlation = {}
        self.rotation_signal = None
    
    def analyze_momentum(self, sector_returns: Dict[str, pd.Series]) -> Dict:
        """
        分析行业动量
        
        Args:
            sector_returns: {sector_name: returns_series}
        """
        momentum_scores = {}
        
        for sector, returns in sector_returns.items():
            # 多时间窗口动量
            mom_1m = returns.tail(21).mean()
            mom_3m = returns.tail(63).mean()
            mom_6m = returns.tail(126).mean()
            
            # 综合动量得分
            score = 0.2 * mom_1m + 0.3 * mom_3m + 0.5 * mom_6m
            
            momentum_scores[sector] = {
                'momentum_1m': mom_1m,
                'momentum_3m': mom_3m,
                'momentum_6m': mom_6m,
                'composite_score': score
            }
        
        self.sector_momentum = momentum_scores
        return momentum_scores
    
    def detect_rotation(self, market_regime: str = 'expansion') -> Dict:
        """
        检测行业轮动信号
        
        Args:
            market_regime: 市场状态 ('expansion', 'late_cycle', 'recession', 'early_cycle')
        """
        if not self.sector_momentum:
            return {'signal': 'neutral', 'sectors': {}}
        
        # 根据市场周期推荐行业
        rotation_map = {
            'early_cycle': ['Technology', 'Consumer Discretionary', 'Industrials'],
            'expansion': ['Technology', 'Healthcare', 'Financials'],
            'late_cycle': ['Energy', 'Materials', 'Utilities'],
            'recession': ['Consumer Staples', 'Healthcare', 'Utilities']
        }
        
        recommended = rotation_map.get(market_regime, [])
        
        # 匹配实际动量
        sorted_sectors = sorted(
            self.sector_momentum.items(),
            key=lambda x: x[1]['composite_score'],
            reverse=True
        )
        
        signal = {
            'regime': market_regime,
            'recommended_sectors': recommended,
            'top_momentum_sectors': [s[0] for s in sorted_sectors[:5]],
            'rotation_strength': abs(sorted_sectors[0][1]['composite_score'] - sorted_sectors[-1][1]['composite_score'])
        }
        
        self.rotation_signal = signal
        return signal


def main():
    """测试多因子模型"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("="*70)
    print("多因子量化模型测试")
    print("="*70)
    
    # 生成模拟数据
    np.random.seed(42)
    n_samples = 500
    n_factors = 20
    
    X = np.random.randn(n_samples, n_factors)
    y = np.random.choice([0, 1], size=n_samples, p=[0.6, 0.4])
    
    # 创建模型
    model = MultiFactorModel(
        factors=[f'factor_{i}' for i in range(n_factors)],
        optimization_method='ic_weighting'
    )
    
    # 优化权重
    weights = model.optimize_weights(X, y)
    
    print(f"\n因子权重 (Top 5):")
    sorted_weights = sorted(weights.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
    for factor, weight in sorted_weights:
        print(f"  {factor}: {weight:.3f}")
    
    # 回测
    results = model.backtest(X, y)
    
    print(f"\n回测结果:")
    print(f"  IC均值: {results['ic_mean']:.3f}")
    print(f"  多空收益: {results['long_short_return']:.3f}")
    print(f"  夏普比率: {results['sharpe_ratio']:.2f}")
    
    print("\n" + "="*70)


if __name__ == '__main__':
    main()
