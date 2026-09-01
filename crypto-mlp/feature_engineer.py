#!/usr/bin/env python3
"""
Crypto Feature Engineer - 高级特征工程模块

特征类型:
1. 技术指标 (50+)
   - 趋势指标: MA, EMA, MACD, ADX
   - 动量指标: RSI, Stochastic, CCI
   - 波动率指标: Bollinger Bands, ATR, Keltner
   - 成交量指标: OBV, VWAP, MFI
   
2. 时序特征
   - 多时间窗口聚合
   - 滞后特征
   - 滚动统计
   
3. 市场结构特征
   - 支撑阻力位
   - 成交量分布
   - 价格结构
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import logging
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class CryptoFeatureEngineer:
    """加密货币特征工程师"""
    
    def __init__(self, include_sentiment: bool = False, include_onchain: bool = False):
        """
        初始化特征工程师
        
        Args:
            include_sentiment: 是否包含情感特征
            include_onchain: 是否包含链上特征
        """
        self.include_sentiment = include_sentiment
        self.include_onchain = include_onchain
        self.feature_names = []
    
    def create_features(self, df: pd.DataFrame, target_col: str = 'close', 
                       target_type: str = 'direction') -> pd.DataFrame:
        """
        创建特征矩阵
        
        Args:
            df: OHLCV数据
            target_col: 目标列名
            target_type: 目标类型 (direction/magnitude)
        
        Returns:
            特征DataFrame
        """
        result = df.copy()
        self.feature_names = []
        
        # 1. 基础技术指标
        result = self._add_technical_indicators(result)
        
        # 2. 多时间窗口特征
        result = self._add_multi_timeframe_features(result)
        
        # 3. 市场结构特征
        result = self._add_market_structure_features(result)
        
        # 4. 生成目标变量
        result = self._create_target(result, target_col, target_type)
        
        # 5. 清理无效数据
        result = result.dropna()
        
        self.feature_names = [col for col in result.columns if col not in 
                             ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'target']]
        
        logger.info(f"创建特征完成，共{len(self.feature_names)}个特征")
        return result
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加技术指标"""
        
        # ===== 趋势指标 =====
        # 移动平均线
        for period in [5, 10, 20, 50, 100, 200]:
            df[f'MA_{period}'] = df['close'].rolling(period).mean()
            df[f'MA_{period}_ratio'] = df['close'] / df[f'MA_{period}'] - 1
        
        # EMA
        for period in [12, 26, 50]:
            df[f'EMA_{period}'] = df['close'].ewm(span=period).mean()
        
        # MACD
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_hist'] = df['MACD'] - df['MACD_signal']
        
        # ADX
        high = df['high']
        low = df['low']
        close = df['close']
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(14).mean()
        
        plus_dm = high.diff()
        minus_dm = low.diff().abs()
        df['+DM'] = ((plus_dm > minus_dm) & (plus_dm > 0)) * plus_dm
        df['-DM'] = ((minus_dm > plus_dm) & (minus_dm > 0)) * minus_dm
        df['DI_plus'] = 100 * (df['+DM'].ewm(span=14).mean() / df['ATR'])
        df['DI_minus'] = 100 * (df['-DM'].ewm(span=14).mean() / df['ATR'])
        df['ADX'] = 100 * (abs(df['DI_plus'] - df['DI_minus']) / 
                          (df['DI_plus'] + df['DI_minus']) * df['ATR']).rolling(14).mean()
        
        # ===== 动量指标 =====
        # RSI
        df = self._add_rsi(df, periods=[6, 12, 24])
        
        # Stochastic
        low_14 = df['low'].rolling(14).min()
        high_14 = df['high'].rolling(14).max()
        df['Stoch_K'] = 100 * (df['close'] - low_14) / (high_14 - low_14)
        df['Stoch_D'] = df['Stoch_K'].rolling(3).mean()
        
        # CCI
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        ma_tp = typical_price.rolling(20).mean()
        mad = typical_price.rolling(20).apply(lambda x: np.abs(x - x.mean()).mean())
        df['CCI'] = (typical_price - ma_tp) / (0.015 * mad)
        
        # ===== 波动率指标 =====
        # Bollinger Bands
        bb_ma = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        df['BB_upper'] = bb_ma + 2 * bb_std
        df['BB_lower'] = bb_ma - 2 * bb_std
        df['BB_width'] = (df['BB_upper'] - df['BB_lower']) / bb_ma
        df['BB_position'] = (df['close'] - df['BB_lower']) / (df['BB_upper'] - df['BB_lower'])
        
        # Keltner Channels
        ema_21 = df['close'].ewm(span=21).mean()
        atr_14 = df['ATR'].rolling(14).mean()
        df['KC_upper'] = ema_21 + 2 * atr_14
        df['KC_lower'] = ema_21 - 2 * atr_14
        df['KC_width'] = (df['KC_upper'] - df['KC_lower']) / ema_21
        
        # ===== 成交量指标 =====
        # OBV
        obv = [0]
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.append(obv[-1] + df['volume'].iloc[i])
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.append(obv[-1] - df['volume'].iloc[i])
            else:
                obv.append(obv[-1])
        df['OBV'] = obv
        df['OBV_ma'] = df['OBV'].rolling(20).mean()
        
        # VWAP (日内)
        tp = (df['high'] + df['low'] + df['close']) / 3
        df['VWAP'] = (tp * df['volume']).cumsum() / df['volume'].cumsum()
        
        # MFI
        mf_rate = tp * df['volume']
        pos_mf = mf_rate.copy()
        neg_mf = mf_rate.copy()
        pos_mf[tp.diff() < 0] = 0
        neg_mf[tp.diff() >= 0] = 0
        df['MFI'] = 100 * (pos_mf.rolling(14).sum() / neg_mf.rolling(14).sum())
        
        # Volume Ratio
        df['Vol_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        
        # Volume Profile
        df['Vol_ma'] = df['volume'].rolling(20).mean()
        df['Vol_std'] = df['volume'].rolling(20).std()
        df['Vol_zscore'] = (df['volume'] - df['Vol_ma']) / (df['Vol_std'] + 1e-10)
        
        return df
    
    def _add_rsi(self, df: pd.DataFrame, periods: List[int] = [6, 12, 24]) -> pd.DataFrame:
        """添加RSI指标"""
        for period in periods:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
            rs = gain / (loss + 1e-10)
            df[f'RSI_{period}'] = 100 - (100 / (1 + rs))
        return df
    
    def _add_multi_timeframe_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加多时间窗口特征"""

        # 多时间窗口收益率
        for period in [1, 4, 12, 24, 48, 168]:  # 1h, 4h, 12h, 24h, 2d, 7d
            ret_col = f'Return_{period}h'
            df[ret_col] = df['close'].pct_change(period)

        # 多时间窗口波动率
        for period in [12, 24, 48]:
            ret_col = f'Return_{period}h'
            vol_col = f'Volatility_{period}h'
            df[vol_col] = df[ret_col].rolling(period).std()

        # 多时间窗口成交量变化
        for period in [12, 24]:
            vol_col = f'Vol_Change_{period}h'
            df[vol_col] = df['volume'].pct_change(period)

        return df
    
    def _add_market_structure_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加市场结构特征"""
        
        # 支撑阻力位
        df['Resistance_20'] = df['high'].rolling(20).max()
        df['Support_20'] = df['low'].rolling(20).min()
        df['Distance_to_Resistance'] = (df['Resistance_20'] - df['close']) / df['close']
        df['Distance_to_Support'] = (df['close'] - df['Support_20']) / df['close']
        
        # 价格位置
        df['Price_Position_20'] = (df['close'] - df['Support_20']) / (df['Resistance_20'] - df['Support_20'] + 1e-10)
        
        # 趋势强度
        df['Trend_Strength'] = abs(df['close'].diff(20)) / df['close'].shift(20)
        
        # 突破信号
        df['Breakout_20'] = (df['close'] > df['Resistance_20'].shift(1)).astype(int)
        df['Breakdown_20'] = (df['close'] < df['Support_20'].shift(1)).astype(int)
        
        return df
    
    def _create_target(self, df: pd.DataFrame, target_col: str, target_type: str) -> pd.DataFrame:
        """创建目标变量"""
        
        if target_type == 'direction':
            # 方向预测（上涨/下跌）
            df['target'] = (df[target_col].shift(-1) > df[target_col]).astype(int)
        elif target_type == 'magnitude':
            # 幅度预测
            df['target'] = df[target_col].pct_change(1).shift(-1)
        
        return df
    
    def get_feature_importance(self, model, feature_names: List[str]) -> pd.DataFrame:
        """获取特征重要性"""
        if hasattr(model, 'feature_importances_'):
            importance = pd.DataFrame({
                'feature': feature_names,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
            return importance
        return pd.DataFrame()


if __name__ == '__main__':
    # 测试示例
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 模拟数据
    np.random.seed(42)
    dates = pd.date_range(end=pd.Timestamp.now(), periods=500, freq='4h')
    prices = np.cumsum(np.random.randn(500) * 100) + 50000
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': prices + np.abs(np.random.randn(500) * 50),
        'low': prices - np.abs(np.random.randn(500) * 50),
        'close': prices,
        'volume': np.random.uniform(1000, 5000, 500)
    })
    
    engineer = CryptoFeatureEngineer()
    result = engineer.create_features(df)
    
    print(f"特征数: {len(engineer.feature_names)}")
    print(f"特征列表前20个: {engineer.feature_names[:20]}")
    print(f"\n数据形状: {result.shape}")
    print(f"\n目标变量分布:\n{result['target'].value_counts()}")
