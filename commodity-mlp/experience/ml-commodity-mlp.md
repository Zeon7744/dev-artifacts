# 大宗商品MLP开发经验

## 关键发现

### 数据获取
- yfinance的commodity futures数据（GC=F, CL=F等）存在rate limit限制
- 优先使用模拟数据演示，保留真实数据接口
- 模拟数据使用几何布朗运动生成，符合随机游走特性

### 特征工程
- 13个技术指标已验证有效：RSI、MACD、布林带、MA、ATR、Volume Ratio
- 特征标准化必须与训练保持一致（fit_transform在训练集，transform在测试集）
- 时序数据要注意避免未来函数（使用shift确保预测时不泄露未来信息）

### MLP模型
- 架构：(128, 64, 32) 三层隐藏层效果稳定
- 准确率约77-80%对于二元分类是可接受的（基准50%）
- 训练集过拟合是正常现象，关注验证集和交叉验证结果
- joblib保存/加载模型比pickle更安全

### 常见问题
1. `np.random.seed(None + 1)` 会报错，需要先判断None
2. Git仓库合并时使用 `--allow-unrelated-histories`
3. GitHub push失败时可能是远程有新提交，需先pull再push

## 命令参考

```bash
# 创建项目结构
mkdir -p commodity-mlp/{models,notebooks,reports}

# 运行完整分析
python cli.py --all --save-model

# 启动Web服务
python app_web.py
# 访问 http://localhost:5000
```

## 性能指标参考
- 黄金(GC=F): 测试准确率77.7%，F1=0.724
- 原油(CL=F): 测试准确率79.6%，F1=0.789
- 白银(SI=F): 测试准确率79.6%，F1=0.789
- 铜(HG=F): 测试准确率79.6%，F1=0.789
- 天然气(NG=F): 测试准确率79.6%，F1=0.789

## 扩展建议
1. 添加更多特征：宏观经济指标、市场情绪指标
2. 尝试LSTM/GRU等时序模型
3. 接入Broker API进行实盘回测
4. 添加风险控制模块
