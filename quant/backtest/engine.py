"""
回测引擎

核心回测框架，支持策略在历史数据上的回测执行
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
from .portfolio import Portfolio
from .metrics import calculate_metrics
from ..strategies.base import BaseStrategy


class BacktestEngine:
    """
    回测引擎
    
    支持在历史数据上运行策略，计算绩效指标，生成交易记录。
    
    使用方式：
        engine = BacktestEngine(initial_capital=100000)
        result = engine.run(strategy=my_strategy, data=price_data)
    
    Attributes:
        initial_capital: 初始资金
        portfolio: 投资组合实例
        result: 回测结果
    """
    
    def __init__(self, initial_capital: float = 100000.0,
                 commission_rate: float = 0.001,
                 slippage: float = 0.0005):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金
            commission_rate: 手续费率
            slippage: 滑点比例
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        
        self.portfolio: Optional[Portfolio] = None
        self.result: Optional[Dict] = None
        self._callbacks: Dict[str, List] = {'on_trade': [], 'on_bar': []}
    
    def run(self, strategy: BaseStrategy, data: pd.DataFrame,
            params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        运行回测
        
        Args:
            strategy: 策略实例
            data: 市场数据 DataFrame（需包含 open, high, low, close, volume 列）
            params: 策略参数覆盖
        
        Returns:
            回测结果字典，包含：
            - equity_curve: 权益曲线
            - trades: 交易记录
            - metrics: 绩效指标
            - signals: 信号序列
        """
        # 数据验证
        self._validate_data(data)
        
        # 参数覆盖
        if params:
            strategy.set_parameters(**params)
        
        # 初始化投资组合
        self.portfolio = Portfolio(
            initial_capital=self.initial_capital,
            commission_rate=self.commission_rate,
            slippage=self.slippage
        )
        
        # 生成信号
        print(f"[回测引擎] 运行策略: {strategy.name}")
        signals_df = strategy.generate_signals(data.copy())
        
        # 验证信号
        if 'signal' not in signals_df.columns:
            raise ValueError("策略必须生成包含 'signal' 列的 DataFrame")
        
        # 执行交易
        print(f"[回测引擎] 执行回测...")
        self._execute_trades(signals_df, data)
        
        # 计算指标
        equity_curve = self.portfolio.get_equity_curve()
        trades_df = self.portfolio.get_trades_df()
        
        # 确定周期数
        if len(equity_curve) > 1:
            time_delta = equity_curve.index[-1] - equity_curve.index[0]
            if hasattr(time_delta, 'days') and time_delta.days > 0:
                periods_per_year = 252  # 日频数据
            else:
                periods_per_year = 252
        else:
            periods_per_year = 252
        
        metrics = calculate_metrics(
            equity_curve=equity_curve,
            trades=trades_df,
            periods_per_year=periods_per_year
        )
        
        self.result = {
            'strategy_name': strategy.name,
            'equity_curve': equity_curve,
            'trades': trades_df,
            'metrics': metrics,
            'signals': signals_df,
            'data': data,
        }
        
        # 打印摘要
        self._print_summary(metrics, strategy.name)
        
        return self.result
    
    def _validate_data(self, data: pd.DataFrame):
        """验证输入数据格式"""
        required_columns = ['close']
        missing = [col for col in required_columns if col not in data.columns]
        if missing:
            raise ValueError(f"数据缺少必要列: {missing}")
        
        if len(data) < 2:
            raise ValueError("数据至少需要 2 条记录")
    
    def _execute_trades(self, signals_df: pd.DataFrame, data: pd.DataFrame):
        """根据信号执行交易"""
        symbol = 'ASSET'
        current_position = 0
        
        for i in range(len(signals_df)):
            signal = signals_df['signal'].iloc[i]
            price = data['close'].iloc[i]
            timestamp = signals_df.index[i] if isinstance(signals_df.index, pd.DatetimeIndex) else i
            
            # 更新权益
            prices = {symbol: price}
            self.portfolio.update_equity(timestamp, prices)
            
            # 执行信号
            if signal == 1 and current_position <= 0:
                # 买入信号
                if current_position < 0:
                    # 先平空
                    pos = self.portfolio.get_position(symbol)
                    if pos:
                        self.portfolio.cover(symbol, pos['quantity'], price, timestamp)
                
                # 计算可买数量（使用 95% 资金）
                available = self.portfolio.cash * 0.95
                quantity = available / price
                if quantity > 0:
                    self.portfolio.buy(symbol, quantity, price, timestamp)
                    current_position = 1
                    self._trigger_callback('on_trade', 'BUY', symbol, quantity, price, timestamp)
            
            elif signal == -1 and current_position >= 0:
                # 卖出信号
                if current_position > 0:
                    pos = self.portfolio.get_position(symbol)
                    if pos:
                        self.portfolio.sell(symbol, pos['quantity'], price, timestamp)
                        current_position = 0
                        self._trigger_callback('on_trade', 'SELL', symbol, pos['quantity'], price, timestamp)
                
                # 做空（可选）
                if hasattr(self, '_allow_short') and self._allow_short:
                    available = self.portfolio.cash * 0.95
                    quantity = available / price
                    if quantity > 0:
                        self.portfolio.short(symbol, quantity, price, timestamp)
                        current_position = -1
            
            self._trigger_callback('on_bar', i, data.iloc[i])
    
    def _print_summary(self, metrics: Dict, strategy_name: str):
        """打印回测摘要"""
        print(f"\n{'='*50}")
        print(f"  回测结果 - {strategy_name}")
        print(f"{'='*50}")
        print(f"  总收益率:     {metrics['total_return']:.2%}")
        print(f"  年化收益率:   {metrics['annual_return']:.2%}")
        print(f"  夏普比率:     {metrics['sharpe_ratio']:.4f}")
        print(f"  最大回撤:     {metrics['max_drawdown']:.2%}")
        print(f"  Sortino 比率: {metrics['sortino_ratio']:.4f}")
        print(f"  Calmar 比率:  {metrics['calmar_ratio']:.4f}")
        print(f"  波动率:       {metrics['volatility']:.2%}")
        
        if 'trade_stats' in metrics:
            ts = metrics['trade_stats']
            print(f"\n  交易统计:")
            print(f"    总交易次数: {ts['total_trades']}")
            print(f"    胜率:       {ts['win_rate']:.2%}")
            print(f"    盈亏比:     {ts['profit_factor']:.4f}")
        print(f"{'='*50}\n")
    
    def on_trade(self, callback):
        """注册交易回调"""
        self._callbacks['on_trade'].append(callback)
    
    def on_bar(self, callback):
        """注册 bar 回调"""
        self._callbacks['on_bar'].append(callback)
    
    def _trigger_callback(self, event: str, *args):
        """触发回调"""
        for cb in self._callbacks.get(event, []):
            cb(*args)
    
    def optimize(self, strategy: BaseStrategy, data: pd.DataFrame,
                 param_grid: Dict[str, List], metric: str = 'sharpe_ratio') -> Dict:
        """
        参数优化
        
        Args:
            strategy: 策略实例
            data: 市场数据
            param_grid: 参数网格 {参数名: [候选值列表]}
            metric: 优化目标指标
        
        Returns:
            最优结果和所有尝试的参数组合
        """
        import itertools
        
        # 生成参数组合
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        combinations = list(itertools.product(*values))
        
        results = []
        
        for combo in combinations:
            params = dict(zip(keys, combo))
            try:
                result = self.run(strategy, data, params)
                result_params = params.copy()
                result_params[metric] = result['metrics'].get(metric, 0)
                results.append(result_params)
            except Exception as e:
                print(f"[优化] 参数 {params} 失败: {e}")
        
        # 找最优
        if not results:
            return {'best_params': {}, 'best_value': 0, 'all_results': []}
        
        results_df = pd.DataFrame(results)
        best_idx = results_df[metric].idxmax()
        best_result = results_df.loc[best_idx]
        
        return {
            'best_params': {k: best_result[k] for k in keys},
            'best_value': best_result[metric],
            'all_results': results_df.to_dict('records'),
        }
