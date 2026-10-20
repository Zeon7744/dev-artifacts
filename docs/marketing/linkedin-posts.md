# LinkedIn: Building a Multi-Model Crypto Prediction System with 92.94% Accuracy

I recently built and open-sourced a cryptocurrency prediction system that improved from ~49% to 92.94% CV accuracy using an ensemble voting approach. Here's the technical deep-dive.

## The Problem with Single Models

In quantitative trading, single-model predictors are notoriously unstable. A Random Forest might dominate in sideways markets but fail during trending periods. The variance in predictions leads to inconsistent signals.

## The Ensemble Solution

I implemented a five-model ensemble with adaptive weighting:

| Model | Weight | CV Accuracy | Role |
|-------|--------|-------------|------|
| Random Forest | 30% | 92.94% | Primary predictor, handles feature interactions |
| Gradient Boosting | 25% | 90.22% | Sequential optimization of weak learners |
| MLP Neural Network | 20% | 84.34% | Non-linear pattern capture |
| Logistic Regression | 15% | 92.94% | Interpretable baseline |
| SVM | 3% | 50.59% | High-dimensional boundary detection |

The key insight: **different models fail in different ways**. By voting, we average out individual biases.

## Feature Engineering (64+ Dimensions)

The real magic is in the features, not the models:

**Technical Indicators:** RSI, MACD histogram, Bollinger Band width, ATR, KDJ, OBV, MFI

**Volume-Price Relationships:** Volume change ratio, price deviation from MA20, fund flow imbalance

**Time-Series Features:** Lag features (t-1, t-5, t-20), rolling statistics (20-day mean/std), volatility clustering detection

**Target Variable:** Binary classification (next candle up/down) with confidence calibration

## Risk Management

Prediction is only half the battle. I added:

1. **Kelly Formula position sizing** — dynamically adjusts based on rolling win rate and average win/loss ratio
2. **Three-level circuit breaker** — 5%/10%/consecutive-stop-loss triggers different protection levels
3. **Confidence threshold filtering** — only act when ensemble confidence > 80%

## Interactive Demo

I built a live predictor simulator at: https://zeon7744.github.io/crypto-mlp-high-confidence/

You can adjust market parameters (volatility, volume change, RSI, etc.) and see how each model votes in real-time.

## Open Source

The complete codebase is on GitHub: https://github.com/Zeon7744/crypto-mlp-high-confidence

It includes:
- Full training pipeline with Optuna hyperparameter search
- Advanced analyzer with multi-model voting
- Interactive visualization dashboard
- Comprehensive documentation and CHANGELOG

## Disclaimer

This is for educational and research purposes only. Cryptocurrency markets are extremely volatile. Past performance does not guarantee future results. Not investment advice.

## What I Learned

1. **Ensemble methods are underrated** — the improvement from 49% to 93% wasn't from a single breakthrough, but from averaging multiple imperfect signals
2. **Feature engineering beats model complexity** — 64+ well-crafted features outperformed deeper neural networks
3. **Risk management is non-negotiable** — a 90% accurate model without position sizing can still blow up your account

Would love to hear your thoughts on ensemble methods in quantitative finance. Have you tried similar approaches?

#MachineLearning #QuantitativeTrading #Cryptocurrency #Python #OpenSource #DataScience

---

# LinkedIn: Baibai MCP Toolkit for AI-Assisted Development

I just open-sourced **Baibai**, an MCP (Model Context Protocol) toolkit designed for AI-powered development workflows.

## Why MCP?

When using Claude Code, Cursor, or other AI coding assistants, you quickly realize that many tasks repeat across projects:
- Format validation (Markdown, JSON, YAML)
- Statistical analysis of CSV/JSON data
- README generation
- Markdown-to-HTML conversion
- Text-to-speech for reports

Instead of rewriting these every time, MCP lets you package them as reusable tools that any AI assistant can call.

## What's in Baibai

**12 standard tools** covering:
- `check_format` — Code and documentation format validation
- `analyze` — Statistical analysis of CSV/JSON data
- `gen_readme` — Automated README generation
- `md2html` — Markdown to HTML conversion
- `classify` — Content auto-classification
- `get_time` — Timestamp utilities
- `read_file` / `write_file` — File operations
- `search` — Global project search
- `tts` — Text-to-speech synthesis
- `speech` — Speech-to-text transcription
- `http_get` — HTTP request wrapper

**Zero dependencies** in the core. BYOK (Bring Your Own Key) for TTS services.

## Why This Matters

MCP is becoming the standard protocol for AI tool integration. By building on it, Baibai works with:
- Claude Code
- Cursor
- VS Code with MCP extensions
- Any MCP-compatible agent framework

## Quick Start

```bash
# Install from GitHub Releases
pip install https://github.com/Zeon7744/baibai/releases/download/v1.2.0/baibai-1.2.0-py3-none-any.whl

# Configure MCP
echo '{"mcpServers":{"baibai":{"command":"python","args":["-m","tools.cli","mcp","serve"]}}}' > ~/.claude/settings.json
```

## Three-Platform Strategy

All my projects support three platforms for maximum accessibility:
- **GitHub** (primary) — https://github.com/Zeon7744/baibai
- **Gitee** (China) — mirrors via GitHub Actions
- **GitCode** (Huawei Cloud) — mirrors via GitHub Actions

## Full Project Ecosystem

Baibai is part of a larger toolkit I've been building:

| Project | Description |
|---------|-------------|
| [baibai](https://github.com/Zeon7744/baibai) | MCP toolkit for Vibe Coding |
| [crypto-mlp-high-confidence](https://github.com/Zeon7744/crypto-mlp-high-confidence) | 5-model crypto prediction engine |
| [global-investment-mlp](https://github.com/Zeon7744/global-investment-mlp) | Multi-factor investment framework |
| [awesome-ai-short-drama](https://github.com/Zeon7744/awesome-ai-short-drama) | AI short drama creation kit |
| [dev-artifacts](https://github.com/Zeon7744/dev-artifacts) | Developer artifact repository |

Interested in AI-assisted development workflows? Check out the repo and let me know what tools you'd like to see!

#MCP #ClaudeCode #Cursor #OpenSource #Python #AIAssistant #DevTools

---

# LinkedIn: Building an AI Short Drama Content Factory

I've been exploring the intersection of AI and content creation, and just open-sourced a comprehensive toolkit for AI-generated short drama production.

## The Opportunity

AI-generated short dramas (微短剧) are one of the fastest-growing content formats in China, with the market expected to exceed $10B by 2025. But the production pipeline is fragmented — prompts, scripts, tools, and monetization strategies are scattered across private channels.

## What I Built

**awesome-ai-short-drama** — a complete resource library:

- **9 full scripts** (130 episodes) across romance, suspense, and workplace genres
- **5 short stories** (~59K words)
- **6 production tools**: format validator, script classifier, episode analyzer, story generator, platform adapter, analytics dashboard
- **Platform adaptation guide** for Douyin, Kuaishou, WeChat Video
- **Monetization strategy breakdown**

## The Tools

Each tool is designed to be used standalone or in pipeline:

| Tool | Purpose |
|------|---------|
| format_validator.py | Enforce strict JSON/YAML screenplay format |
| script_classifier.py | Auto-classify by genre/subgenre |
| episode_analyzer.py | Episode structure and pacing stats |
| story_generator.py | Generate new story outlines from prompts |
| platform_adapter.py | Adapt scripts for different platforms |
| analytics_dashboard.py | Statistical analysis of your drama portfolio |

## Why Open Source?

Most AI short drama resources are locked in private documents or paid courses. I believe open collaboration will accelerate the entire field. By sharing my scripts, tools, and learnings, others can build on a solid foundation rather than starting from scratch.

## The Future

I'm planning to add:
- More genre templates (currently romance/suspense/workplace)
- Character development tools
- Hook/retention optimization suggestions
- Platform-specific format converters

Check it out: https://github.com/Zeon7744/awesome-ai-short-drama

Has anyone else been working on AI content generation tools? Would love to connect and share ideas.

#AI #ShortDrama #ContentCreation #OpenSource #Python #AICoding #DigitalContent
