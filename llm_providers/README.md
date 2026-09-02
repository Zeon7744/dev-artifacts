"""
LLM Providers - 本地LLM集成模块

功能：
- Ollama本地模型支持（DeepSeek/Qwen/Llama）
- OpenAI API备用
- 动态切换与故障转移
- 嵌入向量生成（RAG支持）
- 熔断器机制

配置示例：
```python
from llm_providers import ProviderFactory, ProviderConfig, ProviderType

# 自动模式（优先Ollama，失败则OpenAI）
config = ProviderConfig(type=ProviderType.AUTO)
factory = ProviderFactory(config)

# 手动指定Ollama
config = ProviderConfig(
    type=ProviderType.OLLAMA,
    ollama_model="deepseek-r1:7b",
    ollama_base_url="http://localhost:11434"
)
factory = ProviderFactory(config)
```

使用示例：
```python
from llm_providers import Message

# 对话
messages = [
    Message(role="system", content="你是一个金融分析师"),
    Message(role="user", content="分析黄金价格走势")
]
response = factory.chat(messages)
print(response.content)

# 嵌入
embeddings = factory.embed(["黄金价格上涨"])
```
"""

from .base_provider import BaseProvider, Message, LLMResponse
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider, AuthenticationError, RateLimitError
from .provider_factory import ProviderFactory, ProviderConfig, ProviderType

__all__ = [
    'BaseProvider',
    'Message',
    'LLMResponse',
    'OllamaProvider',
    'OpenAIProvider',
    'AuthenticationError',
    'RateLimitError',
    'ProviderFactory',
    'ProviderConfig',
    'ProviderType',
]
