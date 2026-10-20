# Baibai MCP Server - Vibe Coding Toolkit

I just open-sourced **Baibai**, a lightweight MCP (Model Context Protocol) toolkit for AI-powered development workflows.

## Why Baibai?

When using Claude Code or Cursor for financial analysis and content creation, I kept running into the same repetitive tasks:
- Formatting checks (Markdown, JSON, YAML)
- Data analysis scripts
- README generation
- Multi-platform sync

Instead of rewriting these every time, I built Baibai as a reusable MCP server.

## Features

- **12 standard tools**: format checker, data analyzer, README generator, md2html, TTS, speech-to-text, etc.
- **Zero dependencies** in core
- **MCP protocol support** - works with Claude Code, Cursor, Codex, and any MCP-compatible editor
- **ByOK (Bring Your Own Key)** - use your own API keys for TTS services
- **Three-platform sync** - GitHub, Gitee, GitCode

## Install

```bash
# From GitHub Releases
pip install https://github.com/Zeon7744/baibai/releases/download/v1.2.0/baibai-1.2.0-py3-none-any.whl

# Or from source
git clone https://github.com/Zeon7744/baibai.git
cd baibai
pip install -e .
```

## MCP Configuration

Add to your Claude Code / Cursor MCP settings:

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

## Repo

🔗 https://github.com/Zeon7744/baibai

Star if you find it useful! Questions and PRs welcome.

---

# Crypto MLP Analyzer - 92.94% CV Accuracy Prediction Engine

Just finished building a **multi-model ensemble prediction system** for cryptocurrency markets.

## The Problem

Single-model predictors are notoriously unstable. A model that works well in sideways markets might fail in trending ones. I wanted to see if an ensemble voting approach could improve robustness.

## The Solution

Five models vote on each prediction:
- **Random Forest** (weight: 0.30) - most stable, handles feature interactions well
- **Gradient Boosting** (weight: 0.25) - sequential optimization of weak learners
- **MLP Neural Net** (weight: 0.20) - strong non-linear fitting
- **Logistic Regression** (weight: 0.15) - interpretable baseline
- **SVM** (weight: 0.03) - high-dimensional classification

## Results

| Model | CV Accuracy | Test Accuracy |
|-------|-------------|---------------|
| Ensemble (voting) | **92.94%** | **86.70%** |
| RF (alone) | 92.94% | 86.70% |
| LR (alone) | 92.94% | 78.20% |
| GB (alone) | 90.22% | 82.10% |
| MLP (alone) | 84.34% | 75.80% |
| SVM (alone) | 50.59% | 51.30% |

The ensemble uses **adaptive weighting** based on recent performance, plus a **Kelly formula** for position sizing and a **three-level circuit breaker** for risk management.

## Interactive Demo

I built a live predictor simulator where you can adjust market conditions and see how each model votes:

🔗 https://zeon7744.github.io/crypto-mlp-high-confidence/

## Repo

🔗 https://github.com/Zeon7744/crypto-mlp-high-confidence

**Disclaimer**: For educational/research purposes only. Not investment advice.

Star if you find it interesting!

---

# Awesome AI Short Drama - Complete AI Content Creation Kit

Open-sourced my **AI short drama creation toolkit** — everything from script templates to production tools.

## What's Inside

- **9 complete scripts** (130 episodes) across romance, suspense, and workplace genres
- **5 short stories** (~59K words)
- **6 production tools**: format validator, script classifier, statistical analysis, etc.
- **Platform adaptation guide**: Douyin, Kuaishou, WeChat video
- **Monetization strategy** breakdown

## Tools Included

| Tool | Purpose |
|------|---------|
| format_validator.py | Enforce strict JSON/YAML screenplay format |
| script_classifier.py | Auto-classify by genre/subgenre |
| episode_analyzer.py | Episode structure and pacing stats |
| story_generator.py | Generate new story outlines |
| platform_adapter.py | Adapt scripts for different platforms |
| analytics_dashboard.py | Statistical analysis of your drama portfolio |

## Why I Open-Sourced This

The AI short drama space is growing fast, but most resources are scattered across private documents and paid courses. I believe open collaboration will push the whole field forward.

🔗 https://github.com/Zeon7744/awesome-ai-short-drama

Star and fork if useful!
