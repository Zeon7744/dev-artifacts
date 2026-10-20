"""
大宗商品MLP投资分析工具 - 回测引擎
模拟历史交易并计算收益指标
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

class BacktestEngine:
    """回测引擎"""
    
    def __init__(
        self,
        initial_capital: float = 100000,
        commission_rate: float = 0.001,
        slippage: float = 0.0005
    ):
        """
        初始化回测引擎
        
        参数:
            initial_capital: 初始资金
            commission_rate: 手续费率
            slippage: 滑点
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        
        self.trades = []
        self.equity_curve = []
        self.positions = []
    
    def run_backtest(
        self,
        df: pd.DataFrame,
        signals,  # 接受array-like类型
        position_size: float = 1.0
    ) -> Dict:
        """
        运行回测
        
        参数:
            df: 包含价格数据的DataFrame
            signals: 预测信号序列（1=买入，0=卖出）- 支持array/pd.Series/np.ndarray
            position_size: 仓位比例（0-1）
            
        返回:
            回测结果字典
        """
        capital = self.initial_capital
        position = 0
        trade_count = 0
        
        equity = [capital]
        trades_log = []
        
        # 转换signals为pandas Series以兼容索引
        if isinstance(signals, np.ndarray):
            signals = pd.Series(signals, index=df.index[:len(signals)])
        
        for i in range(len(df)):
            current_price = df['Close'].iloc[i]
            
            # 应用滑点
            buy_price = current_price * (1 + self.slippage)
            sell_price = current_price * (1 - self.slippage)
            
            signal = signals.iloc[i]
            
            # 买入信号
            if signal == 1 and position == 0:
                # 开多仓
                position_value = capital * position_size
                shares = position_value / buy_price
                cost = position_value * self.commission_rate
                
                capital -= (position_value + cost)
                position = shares
                trade_count += 1
                
                trades_log.append({
                    'date': df.index[i] if hasattr(df.index, 'name') else i,
                    'type': 'BUY',
                    'price': buy_price,
                    'shares': shares,
                    'value': position_value,
                    'cost': cost,
                    'capital': capital
                })
            
            # 卖出信号或持仓到期
            elif signal == 0 and position > 0:
                # 平仓
                proceeds = position * sell_price
                cost = proceeds * self.commission_rate
                
                capital += (proceeds - cost)
                position = 0
                trade_count += 1
                
                trades_log.append({
                    'date': df.index[i] if hasattr(df.index, 'name') else i,
                    'type': 'SELL',
                    'price': sell_price,
                    'shares': position,
                    'value': proceeds,
                    'cost': cost,
                    'capital': capital,
                    'pnl': capital - trades_log[-2]['capital'] if len(trades_log) >= 2 else 0
                })
            
            # 记录权益
            total_equity = capital + (position * current_price)
            equity.append(total_equity)
        
        # 强制平仓
        if position > 0:
            final_price = df['Close'].iloc[-1] * (1 - self.slippage)
            proceeds = position * final_price
            cost = proceeds * self.commission_rate
            capital += (proceeds - cost)
            
            trades_log.append({
                'date': df.index[-1] if hasattr(df.index, 'name') else len(df) - 1,
                'type': 'FORCE_CLOSE',
                'price': final_price,
                'shares': position,
                'value': proceeds,
                'cost': cost,
                'capital': capital
            })
        
        final_equity = capital
        total_return = (final_equity - self.initial_capital) / self.initial_capital * 100
        
        # 计算绩效指标
        equity_series = pd.Series(equity)
        daily_returns = equity_series.pct_change().dropna()
        
        results = {
            'initial_capital': self.initial_capital,
            'final_capital': final_equity,
            'total_return_pct': total_return,
            'total_trades': trade_count,
            'winning_trades': len([t for t in trades_log if t.get('pnl', 0) > 0]),
            'losing_trades': len([t for t in trades_log if t.get('pnl', 0) < 0]),
            'win_rate': len([t for t in trades_log if t.get('pnl', 0) > 0]) / max(trade_count, 1) * 100,
            'max_equity': max(equity),
            'min_equity': min(equity),
            'max_drawdown_pct': (max(equity) - min(equity)) / max(equity) * 100,
            'sharpe_ratio': (daily_returns.mean() / daily_returns.std() * np.sqrt(252)) if daily_returns.std() > 0 else 0,
            'trades': trades_log,
            'equity_curve': equity
        }
        
        return results
    
    def run_backtest_from_predictions(
        self,
        df: pd.DataFrame,
        model,
        threshold: float = 0.6
    ) -> Dict:
        """
        从模型预测生成信号并运行回测
        
        参数:
            df: 原始数据
            model: 已训练的模型对象
            threshold: 置信度阈值
            
        返回:
            回测结果字典
        """
        # 生成预测
        predictions = model.predict(df)
        probas = model.predict_proba(df)
        
        # 生成信号
        signals = self.generate_signals_from_prediction(predictions, probas, threshold)
        
        # 运行回测
        return self.run_backtest(df, signals)
    
    def generate_signals_from_prediction(
        self,
        predictions: np.ndarray,
        probas: np.ndarray,
        threshold: float = 0.6
    ) -> pd.Series:
        """
        从预测结果生成交易信号
        
        参数:
            predictions: 预测结果数组
            probas: 预测概率数组
            threshold: 置信度阈值
            
        返回:
            交易信号序列（1=买入，0=持有/卖出）
        """
        signals = []
        for i in range(len(predictions)):
            if predictions[i] == 1 and probas[i][1] >= threshold:
                signals.append(1)
            elif predictions[i] == 0 and probas[i][0] >= threshold:
                signals.append(0)
            else:
                # 低置信度时持有现有仓位
                signals.append(signals[-1] if signals else 0)
        
        return pd.Series(signals)
    
    def print_report(self, results: Dict):
        """打印回测报告"""
        print("\n" + "=" * 60)
        print("回测结果报告")
        print("=" * 60)
        print(f"初始资金:     ${results['initial_capital']:,.2f}")
        print(f"最终资金:     ${results['final_capital']:,.2f}")
        print(f"总收益率:     {results['total_return_pct']:.2f}%")
        print(f"总交易次数:   {results['total_trades']}")
        print(f"盈利交易:     {results['winning_trades']}")
        print(f"亏损交易:     {results['losing_trades']}")
        print(f"胜率:         {results['win_rate']:.1f}%")
        print(f"最大回撤:     {results['max_drawdown_pct']:.2f}%")
        print(f"夏普比率:     {results['sharpe_ratio']:.3f}")
        print("=" * 60)


if __name__ == '__main__':
    # 测试回测引擎
    from data_fetcher import CommodityDataFetcher
    from feature_engineering import FeatureEngineer
    from mlp_model import CommodityMLPModel
    
    print("=" * 60)
    print("回测引擎测试")
    print("=" * 60)
    
    # 获取数据
    fetcher = CommodityDataFetcher()
    engineer = FeatureEngineer()
    model = CommodityMLPModel()
    
    symbol = 'GC=F'
    df = fetcher.generate_simulated_data(symbol, days=500)
    features = engineer.extract_features(df)
    target = df['Target'].iloc[:len(features)]
    
    # 训练模型
    model.train(features, target)
    
    # 生成预测
    predictions = model.predict(features)
    probas = model.predict_proba(features)
    
    # 生成信号
    signals = BacktestEngine().generate_signals_from_prediction(predictions, probas, threshold=0.7)
    
    # 运行回测
    backtest = BacktestEngine(initial_capital=100000)
    results = backtest.run_backtest(df.head(len(signals)), signals)
    
    # 打印报告
    backtest.print_report(results)
