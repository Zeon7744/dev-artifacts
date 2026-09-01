"""
大宗商品MLP投资分析工具 - 风险管理回测引擎
集成风险管理的完整回测系统
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

from risk_manager import RiskManager


class RiskBacktestEngine:
    """集成风险管理的回测引擎"""
    
    def __init__(
        self,
        initial_capital: float = 100000,
        commission_rate: float = 0.001,
        slippage: float = 0.0005,
        risk_config: Optional[Dict] = None
    ):
        """
        初始化回测引擎
        
        参数:
            initial_capital: 初始资金
            commission_rate: 手续费率
            slippage: 滑点
            risk_config: 风险配置字典
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        
        # 初始化风险管理器
        self.risk_manager = RiskManager(**(risk_config or {}))
        
        self.trades = []
        self.equity_curve = []
        self.positions = []
        self.daily_pnl = []
        
    def run_backtest(
        self,
        df: pd.DataFrame,
        signals: pd.Series,
        probabilities: Optional[np.ndarray] = None,
        position_size: float = 0.3
    ) -> Dict:
        """
        运行回测
        
        参数:
            df: 包含价格数据的DataFrame
            signals: 交易信号序列（1=买入，-1=卖出，0=持有）
            probabilities: 预测概率数组（用于仓位调整）
            position_size: 基础仓位比例
            
        返回:
            回测结果字典
        """
        capital = self.initial_capital
        position = 0  # 当前持仓数量
        entry_price = 0
        trade_count = 0
        daily_start_capital = capital
        
        equity = [capital]
        trades_log = []
        
        # 确保signals是Series且长度匹配
        if isinstance(signals, np.ndarray):
            signals = pd.Series(signals, index=df.index[:len(signals)])
        elif len(signals) > len(df):
            signals = signals.iloc[:len(df)]
        
        for i in range(len(df)):
            current_price = df['Close'].iloc[i]
            current_date = df['Date'].iloc[i] if 'Date' in df.columns else i
            
            # 应用滑点
            buy_price = current_price * (1 + self.slippage)
            sell_price = current_price * (1 - self.slippage)
            
            signal = signals.iloc[i] if hasattr(signals, 'iloc') else signals[i]
            prob = probabilities[i] if probabilities is not None and i < len(probabilities) else 0.5
            
            # 风险管理检查
            volatility = df['High'].iloc[i] - df['Low'].iloc[i] if i > 0 else current_price * 0.02
            volatility_pct = volatility / current_price if current_price > 0 else 0.02
            
            risk_decision = self.risk_manager.should_trade(
                capital=capital,
                signal_confidence=prob,
                volatility=volatility_pct
            )
            
            # 执行交易逻辑
            if signal == 1 and position == 0 and risk_decision['should_trade']:
                # 买入开仓
                position_value = capital * position_size * risk_decision.get('position_size', 1)
                shares = position_value / buy_price
                cost = position_value * self.commission_rate
                
                capital -= (shares * buy_price + cost)
                position = shares
                entry_price = buy_price
                trade_count += 1
                
                trades_log.append({
                    'type': 'BUY',
                    'price': buy_price,
                    'shares': shares,
                    'capital': capital,
                    'date': current_date
                })
                
            elif signal == -1 and position > 0 and risk_decision['should_trade']:
                # 卖出平仓
                revenue = position * sell_price
                cost = revenue * self.commission_rate
                pnl = revenue - (position * entry_price) - cost
                
                capital += (revenue - cost)
                position = 0
                entry_price = 0
                trade_count += 1
                
                trades_log.append({
                    'type': 'SELL',
                    'price': sell_price,
                    'shares': position,
                    'pnl': pnl,
                    'capital': capital,
                    'date': current_date
                })
                
                # 更新风险管理器
                self.risk_manager.update_trades({
                    'pnl': pnl,
                    'trade_id': trade_count,
                    'date': current_date
                })
            
            # 检查止损止盈
            if position > 0:
                if self.risk_manager.check_stop_loss(entry_price, current_price):
                    # 触发止损
                    revenue = position * sell_price
                    cost = revenue * self.commission_rate
                    pnl = revenue - (position * entry_price) - cost
                    
                    capital += (revenue - cost)
                    position = 0
                    entry_price = 0
                    trade_count += 1
                    
                    trades_log.append({
                        'type': 'STOP_LOSS',
                        'price': sell_price,
                        'shares': position,
                        'pnl': pnl,
                        'capital': capital,
                        'date': current_date
                    })
                    
                    self.risk_manager.update_trades({
                        'pnl': pnl,
                        'trade_id': trade_count,
                        'date': current_date
                    })
                    
                elif self.risk_manager.check_take_profit(entry_price, current_price):
                    # 触发止盈
                    revenue = position * sell_price
                    cost = revenue * self.commission_rate
                    pnl = revenue - (position * entry_price) - cost
                    
                    capital += (revenue - cost)
                    position = 0
                    entry_price = 0
                    trade_count += 1
                    
                    trades_log.append({
                        'type': 'TAKE_PROFIT',
                        'price': sell_price,
                        'shares': position,
                        'pnl': pnl,
                        'capital': capital,
                        'date': current_date
                    })
                    
                    self.risk_manager.update_trades({
                        'pnl': pnl,
                        'trade_id': trade_count,
                        'date': current_date
                    })
            
            # 记录权益曲线
            current_equity = capital + (position * current_price) if position > 0 else capital
            equity.append(current_equity)
            
            # 每日结算
            if i > 0 and (i + 1) % 20 == 0:  # 每20天结算一次
                self.daily_pnl.append((current_equity - equity[-2]) / equity[-2] * 100)
        
        # 强制平仓（最后一天）
        if position > 0:
            revenue = position * current_price
            cost = revenue * self.commission_rate
            pnl = revenue - (position * entry_price) - cost
            capital += (revenue - cost)
            
        final_equity = capital
        
        # 计算回测指标
        results = self._calculate_metrics(equity, trades_log, final_equity)
        results['risk_summary'] = self.risk_manager.get_risk_summary()
        results['trades'] = trades_log[:50]  # 只保留前50笔交易记录
        
        return results
    
    def _calculate_metrics(self, equity: List[float], trades: List[Dict], final_capital: float) -> Dict:
        """计算回测指标"""
        equity_series = pd.Series(equity)
        
        # 收益率
        total_return = (final_capital - self.initial_capital) / self.initial_capital * 100
        
        # 每日收益率
        daily_returns = equity_series.pct_change().dropna()
        
        # 夏普比率
        sharpe_ratio = daily_returns.mean() / daily_returns.std() * np.sqrt(252) if daily_returns.std() > 0 else 0
        
        # 最大回撤
        running_max = equity_series.cummax()
        drawdown = (equity_series - running_max) / running_max * 100
        max_drawdown = drawdown.min()
        
        # 交易统计
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
        
        win_rate = len(winning_trades) / len(trades) * 100 if trades else 0
        
        # 盈亏比
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = abs(np.mean([t['pnl'] for t in losing_trades])) if losing_trades else 1
        profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
        
        return {
            'initial_capital': self.initial_capital,
            'final_capital': final_capital,
            'total_return_pct': total_return,
            'total_trades': len(trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'max_drawdown_pct': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'daily_returns_mean': daily_returns.mean() * 100,
            'daily_returns_std': daily_returns.std() * 100
        }
    
    def print_report(self, results: Dict):
        """打印回测报告"""
        print("\n" + "=" * 60)
        print("风险管理回测报告")
        print("=" * 60)
        print(f"初始资金:        ${results['initial_capital']:,.2f}")
        print(f"最终资金:        ${results['final_capital']:,.2f}")
        print(f"总收益率:        {results['total_return_pct']:+.2f}%")
        print(f"总交易次数:      {results['total_trades']}")
        print(f"盈利交易:        {results['winning_trades']}")
        print(f"亏损交易:        {results['losing_trades']}")
        print(f"胜率:            {results['win_rate']:.1f}%")
        print(f"盈亏比:          {results['profit_factor']:.2f}")
        print(f"最大回撤:        {results['max_drawdown_pct']:.2f}%")
        print(f"夏普比率:        {results['sharpe_ratio']:.3f}")
        print(f"日均收益率:      {results['daily_returns_mean']:.4f}%")
        print(f"日收益率标准差:  {results['daily_returns_std']:.4f}%")
        
        if 'risk_summary' in results:
            risk = results['risk_summary']
            print("\n风险管理状态:")
            print(f"  当前仓位:      {risk.get('position_size', 0):.2%}")
            print(f"  连续亏损:      {risk.get('consecutive_losses', 0)}次")
            print(f"  当日盈亏:      ${risk.get('daily_pnl', 0):.2f}")
        
        print("=" * 60)


if __name__ == '__main__':
    from data_fetcher_v2 import CommodityDataFetcher
    from feature_engineering import FeatureEngineer
    from mlp_model_advanced import AdvancedCommodityMLP
    
    print("=" * 60)
    print("风险管理回测引擎测试")
    print("=" * 60)
    
    # 获取数据
    fetcher = CommodityDataFetcher()
    engineer = FeatureEngineer()
    
    symbol = 'GC=F'
    df = fetcher.generate_simulated_data(symbol, days=500)
    features = engineer.extract_features(df)
    target = df['Target'].iloc[:len(features)]
    
    # 训练模型
    model = AdvancedCommodityMLP(use_ensemble=True, feature_selection=True)
    model.train(features, target, test_size=0.2)
    
    # 生成预测
    predictions = model.predict(features)
    probabilities = model.predict_proba(features)
    
    # 生成信号（从预测概率转换）
    signals = pd.Series(np.where(probabilities[:, 1] > 0.6, 1, 
                          np.where(probabilities[:, 0] > 0.6, -1, 0)))
    
    # 运行回测
    backtest = RiskBacktestEngine(
        initial_capital=100000,
        risk_config={'stop_loss_pct': 0.05, 'take_profit_pct': 0.15}
    )
    
    results = backtest.run_backtest(df.head(len(signals)), signals, probabilities[:len(signals)])
    backtest.print_report(results)
