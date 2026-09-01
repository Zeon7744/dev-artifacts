# 大宗商品MLP投资分析工具

基于深度神经网络（MLP + LSTM）的大宗商品投资预测工具，集成13个技术指标特征工程、超参数自动搜索、风险管理回测引擎和 REST API 服务。

## 功能特性

### 核心能力
- 📊 **多商品支持**：黄金(GC=F)、原油(CL=F)、白银(SI=F)、铜(HG=F)、天然气(NG=F)
- 🧠 **双模型架构**：MLP集成学习 + LSTM时序模型，可按需选择
- 📈 **13个技术指标**：RSI、MACD、布林带、ATR、移动平均线等
- 🔍 **超参数自动搜索**：基于Optuna的贝叶斯优化，自动搜索最优网络结构
- 🛡️ **风险管理回测**：止损/止盈、每日亏损限制、连续亏损熔断、动态仓位管理
- 🌐 **REST API服务**：完整的RESTful接口，支持数据查询、训练、预测、回测
- 💻 **命令行界面**：快速批量分析和报告生成
- 🖥️ **Web界面**：交互式可视化和实时监控
- 🔬 **模拟数据**：开箱即用，无需API密钥（也支持yfinance真实数据）

### 迭代版本
| 版本 | 文件 | 说明 |
|------|------|------|
| 原版 | `data_fetcher.py`, `mlp_model.py` | 基础MLP模型 |
| 高级版 | `mlp_model_advanced.py` | 集成学习 + 时序交叉验证 + 特征选择 |
| v2 | `data_fetcher_v2.py` | 增强数据获取（多数据源） |
| v3 | `lstm_model.py` | LSTM时序模型 |
| v3 | `hyperparameter_optimizer.py` | Optuna超参数搜索 |
| v3 | `risk_backtest.py` | 风险管理回测引擎 |
| v3 | `api_server.py` | REST API服务 |

## 项目结构

```
commodity-mlp/
├── data_fetcher.py              # 数据获取（原版）
├── data_fetcher_v2.py           # 数据获取 v2（增强版，多数据源）
├── data_fetcher_v3.py           # 数据获取 v3（yfinance/新浪/Tushare）
├── feature_engineering.py       # 特征工程（13个技术指标）
├── mlp_model.py                 # MLP模型（原版）
├── mlp_model_advanced.py        # MLP高级版（集成学习+时序CV）
├── lstm_model.py                # LSTM时序模型
├── hyperparameter_optimizer.py  # 超参数自动搜索（Optuna）
├── risk_manager.py              # 风险管理器
├── risk_backtest.py             # 风险管理回测引擎
├── api_server.py                # REST API服务（Flask）
├── cli.py                       # 命令行工具（原版）
├── cli_advanced.py              # 命令行工具（高级版）
├── app_web.py                   # Flask Web界面
├── test_api.py                  # API端点测试
├── test_comprehensive_v2.py     # 综合测试套件
├── test_realistic_data.py       # 真实数据模拟测试
├── requirements.txt             # Python依赖
├── models/                      # 训练好的模型存储
└── reports/                     # 分析报告输出
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

# 高级版CLI（集成学习+时序CV）
python cli_advanced.py --all
```

### REST API 服务

```bash
# 启动API服务
python api_server.py

# 或指定端口
python api_server.py --port 8080
```

#### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/symbols` | 获取可用商品列表 |
| GET | `/api/data/<symbol>` | 获取商品数据 |
| POST | `/api/train/<symbol>` | 训练模型 |
| POST | `/api/predict/<symbol>` | 实时预测 |
| POST | `/api/backtest/<symbol>` | 运行回测 |
| GET | `/api/analysis/<symbol>` | 综合分析（训练+回测+预测） |
| GET | `/api/docs` | API文档 |

#### API 使用示例

```bash
# 获取黄金数据
curl http://localhost:5000/api/data/GC=F?days=500

# 训练LSTM模型
curl -X POST http://localhost:5000/api/train/GC=F \
  -H "Content-Type: application/json" \
  -d '{"model_type": "lstm"}'

# 获取预测信号
curl -X POST http://localhost:5000/api/predict/GC=F \
  -H "Content-Type: application/json" \
  -d '{"model_type": "mlp"}'

# 运行风险管理回测
curl -X POST http://localhost:5000/api/backtest/GC=F \
  -H "Content-Type: application/json" \
  -d '{"initial_capital": 100000}'

# 一键综合分析
curl http://localhost:5000/api/analysis/GC=F
```

### Web界面

```bash
python app_web.py
# 访问 http://localhost:5000
```

## 模型详解

### MLP集成学习模型

- **集成策略**：3个MLP分类器投票/概率平均
- **隐藏层**：128 → 64 → 32 神经元
- **时序交叉验证**：5折TimeSeriesSplit，避免未来信息泄露
- **特征选择**：基于随机森林的递归特征消除

### LSTM时序模型

- **架构**：双层LSTM + Dropout + 全连接层
- **序列长度**：可配置（默认20步）
- **适用场景**：捕捉价格序列的时序依赖关系

### 超参数自动搜索

使用Optuna进行贝叶斯优化，搜索空间：
- 隐藏层结构（1-3层，32-256神经元）
- 学习率（1e-4 ~ 1e-2）
- Dropout比例（0.1 ~ 0.5）
- 激活函数（relu/tanh/logistic）
- 正则化强度（1e-5 ~ 1e-2）

## 风险管理回测引擎

- **止损**：可配置百分比止损
- **止盈**：可配置百分比止盈
- **每日亏损限制**：超过阈值暂停交易
- **连续亏损熔断**：连续N次亏损后暂停
- **动态仓位**：根据波动率调整仓位大小
- **滑点和手续费**：真实交易成本模拟

## 性能指标

典型测试结果（模拟数据）：

| 模型 | 商品 | 测试准确率 | 备注 |
|------|------|-----------|------|
| MLP集成 | GC=F | ~71% | 时序CV: 76% |
| LSTM | GC=F | ~79% | 时序建模更强 |
| MLP+超参搜索 | GC=F | ~82% | 自动优化结构 |
| MLP集成 | CL=F | ~73% | 原油波动更大 |

> ⚠️ 金融时间序列预测难度较高，准确率受市场环境、数据质量等多种因素影响。

## 运行测试

```bash
# API端点测试
python test_api.py

# 综合测试（MLP + LSTM + 超参优化）
python test_comprehensive_v2.py

# 真实数据对比测试
python test_realistic_data.py
```

## 支持的商品

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
- 真实数据需要 yfinance 库，可能受API速率限制
- 建议用小资金验证策略后再大规模应用

## 许可证

MIT License - 自由使用、修改和分发

---

**仓库归属**：dev-artifacts（通用开发成果成品库）  
**标签**：`ml-finance`, `python`, `cli-tools`, `rest-api`, `lstm`, `dev-artifacts`
