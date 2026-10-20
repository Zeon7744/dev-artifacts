# 一个独立开发者的 GitHub 项目矩阵：从 MCP 工具库到量化预测引擎

> 作者：Zeon7744 · [GitHub 主页](https://github.com/Zeon7744)

---

大家好，我最近做了一组开源项目，主要围绕 **AI 内容创作** 和 **量化投资** 两个方向。今天来分享一下这个"项目矩阵"的构成和背后的思考。

---

## 项目总览

| 项目 | 类型 | 状态 | Stars |
|------|------|------|-------|
| [baibai](https://github.com/Zeon7744/baibai) | MCP 工具库 | ✅ v1.2.0 | 1 |
| [crypto-mlp-high-confidence](https://github.com/Zeon7744/crypto-mlp-high-confidence) | 加密货币预测引擎 | ✅ v1.0.0 | 0 |
| [global-investment-mlp](https://github.com/Zeon7744/global-investment-mlp) | 量化投资框架 | ✅ v0.1.0 | 0 |
| [awesome-ai-short-drama](https://github.com/Zeon7744/awesome-ai-short-drama) | AI 短剧资源库 | ✅ v1.0.0 | 1 |
| [dev-artifacts](https://github.com/Zeon7744/dev-artifacts) | 开发工具箱 | ✅ v0.1.0 | 0 |

---

## 1. baibai — MCP 工具库（我的主力项目）

这是我投入最多的项目。核心思路是：**让 AI 编程助手通过 MCP 协议调用标准化工具，而不是每次写脚本。**

**特点：**
- 12 个标准工具（check_format / analyze / gen_readme / md2html / classify / tts / speech 等）
- 核心零依赖，pip install 即可用
- 支持 Claude Code、Cursor、Codex 等主流 AI 编辑器
- 三平台同步（GitHub / Gitee / GitCode）

**安装：**
```bash
pip install git+https://github.com/Zeon7744/baibai.git
```

**MCP 配置：**
```json
{
  "mcpServers": {
    "baibai": {
      "command": "python",
      "args": ["-m", "tools.cli", "mcp", "serve"]
    }
  }
}
```

---

## 2. crypto-mlp-high-confidence — 五模型投票预测引擎

这个是我最有技术成就感的项目。用随机森林、梯度提升、神经网络、逻辑回归、SVM 五个模型投票，CV 准确率做到 92.94%。

**亮点：**
- 五模型自适应加权投票
- 64+ 特征工程维度
- Kelly 公式仓位管理
- 三级熔断风控机制
- **交互式预测模拟器**（可拖动滑块模拟不同市场条件）

👉 [在线体验预测模拟器](https://zeon7744.github.io/crypto-mlp-high-confidence/)

**快速开始：**
```bash
git clone https://github.com/Zeon7744/crypto-mlp-high-confidence.git
pip install -r requirements.txt
python advanced_analyzer.py
```

> ⚠️ 仅供学术研究和算法验证，不构成投资建议。

---

## 3. global-investment-mlp — 四因子量化投资框架

面向更广泛市场的量化投资工具，支持 A 股、美股、加密货币。

**核心能力：**
- 四因子选股模型（动量、价值、质量、低波动）
- VaR / CVaR 风险分析
- HTML 报告自动生成
- 多市场行情数据接入

---

## 4. awesome-ai-short-drama — AI 短剧创作库

这个比较有趣。我把 AI 生成短剧剧本的完整流程开源了：

- 9 部完整剧本（130 集，涵盖言情、悬疑、职场三类）
- 5 篇短篇故事（约 5.9 万字）
- 6 个生产工具（格式校验、分类器、统计分析等）
- 平台适配方法论

适合对 AI 内容创作感兴趣的同学参考。

---

## 5. dev-artifacts — 统一开发工具箱

这是我个人的开发基础设施项目，整合了：
- API 网关（异步 HTTP + WebSocket）
- 多 Agent 协作系统（analyst / orchestrator / reporter / watcher）
- Docker 部署模板
- 金融新闻 MCP、短剧 MCP 等服务

---

## 三平台同步方案

所有项目都配置了 GitHub Actions 自动同步到 Gitee 和 GitCode：

```yaml
name: sync-gitee-gitcode
on:
  push:
    branches: [main]
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: wearerequired/git-mirror-action@master
        env:
          SSH_PRIVATE_KEY: ${{ secrets.GITEE_SSH_KEY }}
        with:
          source-repo: git@github.com:Zeon7744/<repo>.git
          destination-repo: git@gitee.com:Zeon7744/<repo>.git
```

---

## 开发心得

1. **MCP 是未来** — 工具标准化让 AI 助手能力边界大幅扩展
2. **集成 > 单点** — 多个小工具组合比一个大数据模型更实用
3. **三平台同步很必要** — 国内开发者访问 Gitee/GitCode 更快
4. **文档即产品** — README、CHANGELOG、Pages 站都是项目的重要组成部分

---

如果觉得有帮助，欢迎 Star 支持！有任何问题也可以提 Issue 讨论。

*发布于 2026-09 · Vibe Coding · 三平台同步*
