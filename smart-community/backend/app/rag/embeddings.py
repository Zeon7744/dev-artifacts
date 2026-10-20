"""
文本向量化（Embedding）

策略：
1. 优先调用本地 Ollama 的嵌入接口（nomic-embed-text），超时 3 秒；
2. 任何失败 / 超时 / 服务未启动，自动降级为纯 Python 确定性哈希向量
   （md5 分词哈希 -> 256 维 float 向量 -> L2 归一化），保证离线可运行。

注意：同一进程内嵌入方式应保持一致（要么全走 Ollama，要么全走哈希），
否则向量维度不同无法比较。降级在「单次 embed 调用」粒度上整体生效。
"""
import hashlib
import logging
import math
import re
from typing import List, Sequence

import httpx

from ..core.config import settings

logger = logging.getLogger(__name__)

# 降级哈希向量维度
FALLBACK_DIM: int = 256
# Ollama 嵌入请求超时（秒）
OLLAMA_TIMEOUT: float = 3.0
# 嵌入模型（可通过配置覆盖，默认 nomic-embed-text）
DEFAULT_EMBED_MODEL: str = "nomic-embed-text"

# 分词：中英文按字符 n-gram + 英文单词
_TOKEN_RE = re.compile(r"[a-zA-Z0-9]+|[一-鿿]")


def _tokenize(text: str) -> List[str]:
    """简单分词：英文/数字按词，中文按单字。

    Args:
        text: 待分词文本

    Returns:
        分词结果列表（中文会额外生成相邻二元组以捕捉词组语义）
    """
    tokens: List[str] = _TOKEN_RE.findall(text.lower())
    # 中文单字相邻二元组（bigram），提升短文本匹配效果
    cjk = [t for t in tokens if re.match(r"[一-鿿]", t)]
    tokens.extend(cjk[i] + cjk[i + 1] for i in range(len(cjk) - 1))
    return tokens


def _l2_normalize(vec: List[float]) -> List[float]:
    """L2 归一化向量。

    Args:
        vec: 原始向量

    Returns:
        归一化后的向量；零向量原样返回
    """
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return vec
    return [x / norm for x in vec]


class Embedder:
    """文本向量化器（Ollama 优先，纯 Python 哈希兜底）。"""

    def __init__(self, model: str = DEFAULT_EMBED_MODEL, dim: int = FALLBACK_DIM) -> None:
        """初始化向量化器。

        Args:
            model: Ollama 嵌入模型名
            dim: 降级哈希向量维度
        """
        self.model = model
        self.dim = dim

    async def embed(self, texts: Sequence[str]) -> List[List[float]]:
        """批量文本向量化。

        Args:
            texts: 待向量化的文本列表

        Returns:
            与输入等长的向量列表，每个向量为 L2 归一化后的 float 列表。
            Ollama 不可用时整体降级为哈希向量（维度 256）。
        """
        if not texts:
            return []

        # 优先尝试 Ollama；失败则整体降级，保证同一批向量维度一致
        try:
            vectors = await self._embed_ollama(list(texts))
            if vectors and len(vectors) == len(texts):
                return vectors
            logger.warning("Ollama 返回向量数量不符，降级为哈希向量")
        except Exception as exc:  # noqa: BLE001 - 降级路径需捕获所有异常
            logger.warning("Ollama 嵌入不可用，降级为纯 Python 哈希向量: %s", exc)

        return [self._hash_embed(text) for text in texts]

    async def _embed_ollama(self, texts: List[str]) -> List[List[float]]:
        """调用 Ollama /api/embeddings 批量生成向量。

        Args:
            texts: 文本列表

        Returns:
            向量列表

        Raises:
            httpx.HTTPError / 任意网络异常：交由上层降级
        """
        base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        url = f"{base_url}/api/embeddings"
        vectors: List[List[float]] = []
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
            for text in texts:
                resp = await client.post(
                    url,
                    json={"model": self.model, "prompt": text},
                )
                resp.raise_for_status()
                data = resp.json()
                embedding = data.get("embedding")
                if not embedding:
                    raise ValueError("Ollama 响应缺少 embedding 字段")
                vectors.append([float(x) for x in embedding])
        return vectors

    def _hash_embed(self, text: str) -> List[float]:
        """纯 Python 确定性哈希向量（离线降级方案）。

        对每个 token 计算 md5，映射到向量维度并累加，最后 L2 归一化。
        相同文本恒定得到相同向量。

        Args:
            text: 待向量化文本

        Returns:
            256 维 L2 归一化 float 向量
        """
        vec = [0.0] * self.dim
        for token in _tokenize(text):
            digest = hashlib.md5(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "little") % self.dim
            # 用第二个 4 字节决定符号与权重，避免所有维度同向
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            weight = 1.0 + (digest[5] / 255.0)
            vec[idx] += sign * weight
        return _l2_normalize(vec)

    @staticmethod
    def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
        """计算两个向量的余弦相似度。

        Args:
            a: 向量 A
            b: 向量 B

        Returns:
            余弦相似度，范围 [-1, 1]；零向量返回 0.0
        """
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
