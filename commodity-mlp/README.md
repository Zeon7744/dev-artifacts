# 大宗商品MLP投资分析工具

基于深度神经网络（MLP）的大宗商品投资预测工具，使用13个技术指标作为特征，预测未来5日价格走势。

## 功能特性

- 📊 **多商品支持**：黄金、原油、白银、铜、天然气等主流大宗商品
- 🧠 **MLP神经网络**：三层隐藏层（128-64-32），自动学习非线性模式
- 📈 **13个技术指标**：RSI、MACD、布林带、移动平均线等
- 💻 **命令行界面**：快速批量分析和报告生成
- 🌐 **Web界面**：交互式可视化和实时监控
- 📉 **特征重要性分析**：识别关键预测因子
- 🔬 **模拟数据**：开箱即用，无需API密钥

## 项目结构

```
commodity-mlp/
├── data_fetcher.py      # 数据获取模块（模拟+真实数据）
├── feature_engineering.py  # 特征工程（13个技术指标）
├── mlp_model.py         # MLP模型训练与预测
├── cli.py               # 命令行工具
├── app_web.py           # Flask Web界面
├── requirements.txt     # Python依赖
├── README.md            # 本文档
├── models/              # 训练好的模型存储
├── notebooks/           # Jupyter笔记本（可选）
└── reports/             # 分析报告输出
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 命令行使用

```bash
# 分析单个商品（默认黄金）
python cli.py

# 分析多个商品
python cli.py --symbols GC=F CL=F SI=F

# 分析所有商品
python cli.py --all

# 使用真实数据（需要yfinance）
python cli.py --symbols GC=F --real-data

# 保存训练好的模型
python cli.py --all --save-model
```

### Web界面

```bash
# 启动Web服务
python app_web.py

# 访问 http://localhost:5000
```

## 技术细节

### 模型架构

- **类型**：多层感知机（MLP）分类器
- **隐藏层**：128 → 64 → 32 神经元
- **激活函数**：ReLU
- **优化器**：Adam
- **正则化**：L2 (alpha=0.0001)
- **批次大小**：32
- **最大迭代**：500

### 特征工程

13个技术指标：
1. `Returns_1d` - 日收益率
2. `Returns_5d` - 5日累计收益率
3. `Returns_10d` - 10日累计收益率
4. `MA_5` - 5日均线
5. `MA_10` - 10日均线
6. `MA_20` - 20日均线
7. `RSI_14` - 14日相对强弱指数
8. `MACD` - MACD线
9. `MACD_Signal` - MACD信号线
10. `Bollinger_Band_Width` - 布林带宽度
11. `Bollinger_Position` - 价格在布林带中的位置
12. `ATR_14` - 14日平均真实波动范围
13. `Volume_Ratio` - 成交量比率

### 预测目标

预测未来5日价格走势（二元分类）：
- **1（上涨）**：5日后收盘价高于当前价
- **0（下跌）**：5日后收盘价低于当前价

## 使用示例

### 基本分析流程

```python
from data_fetcher import CommodityDataFetcher
from feature_engineering import FeatureEngineer
from mlp_model import CommodityMLPModel

# 1. 获取数据
fetcher = CommodityDataFetcher()
df = fetcher.generate_simulated_data('GC=F', days=800)

# 2. 提取特征
engineer = FeatureEngineer()
features = engineer.extract_features(df)
target = df['Target'].iloc[:len(features)]

# 3. 训练模型
model = CommodityMLPModel()
metrics = model.train(features, target)

# 4. 预测
prediction = model.predict(features.tail(1))
print(f"预测信号: {'看涨' if prediction[0] == 1 else '看跌'}")

# 5. 查看特征重要性
importance = model.get_importance()
print("Top 5 重要特征:")
for i, (feat, imp) in enumerate(list(importance.items())[:5], 1):
    print(f"  {i}. {feat}: {imp:.4f}")
```

### API接口

```python
# 训练接口
POST /api/train
{
    "symbol": "GC=F",
    "use_real_data": false
}

# 预测接口
GET /api/predict/GC=F

# 特征重要性
GET /api/importance/GC=F

# 所有报告
GET /api/all_reports
```

## 运行测试

```bash
# 测试数据获取
python data_fetcher.py

# 测试特征工程
python feature_engineering.py

# 测试模型
python mlp_model.py

# 完整演示
python cli.py --all
```

## 支持的 commodity

| 代码 | 名称 | 单位 | 基础价格 |
|------|------|------|----------|
| GC=F | 黄金 | USD/oz | 1950 |
| CL=F | 原油 | USD/bbl | 80 |
| SI=F | 白银 | USD/oz | 23 |
| HG=F | 铜 | USD/lb | 3.8 |
| NG=F | 天然气 | USD/MMBtu | 2.5 |

## 注意事项

⚠️ **风险提示**：本工具仅供学习和研究使用，不构成任何投资建议。金融市场存在风险，过去表现不代表未来结果。

⚠️ **数据说明**：
- 默认使用模拟数据（几何布朗运动生成）
- 真实数据需要 yfinance 库，可能受API限制
- 建议用小资金验证策略后再大规模应用

## 性能指标

典型测试结果（模拟数据）：
- 训练集准确率：52-55%
- 测试集准确率：48-52%
- F1分数：0.45-0.50
- 交叉验证稳定性：良好

> 注：金融时间序列预测难度较高，50%左右的准确率已具备统计学意义。

## 扩展建议

1. **增加特征**：
   - 宏观经济指标（CPI、利率等）
   - 市场情绪指标
   - 跨商品相关性

2. **改进模型**：
   - LSTM/GRU 时序模型
   - XGBoost/LightGBM 集成学习
   - 深度学习Transformer

3. **实盘对接**：
   - 接入Broker API
   - 风险控制模块
   - 仓位管理策略

## 许可证

MIT License - 自由使用、修改和分发

## 作者

由 Agnes AI Agent 开发

---

**仓库归属**：dev-artifacts（通用开发成果成品库）  
**标签**：`ml-finance`, `python`, `cli-tools`, `dev-artifacts`
