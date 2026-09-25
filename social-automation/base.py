"""
社交自动化工具集 - 公共基础模块
"""
import logging
import time
import json
import os
from datetime import datetime
from pathlib import Path
from functools import wraps

import requests

# ── 日志 ─────────────────────────────────────────────
def setup_logger(name, level="INFO"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter(
            "[%(asctime)s] %(name)s %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(h)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


# ── 重试装饰器 ────────────────────────────────────────
def retry(max_retries=3, delay=2.0, backoff=1.5, exceptions=(requests.RequestException,)):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    wait = delay * (backoff ** attempt)
                    logging.warning(f"Retry {attempt+1}/{max_retries} after {wait:.1f}s: {e}")
                    time.sleep(wait)
            raise last_exc
        return wrapper
    return decorator


# ── 限流器 ───────────────────────────────────────────
class RateLimiter:
    """简单令牌桶限流"""
    def __init__(self, calls_per_minute=10):
        self.interval = 60.0 / calls_per_minute
        self.last_call = 0.0

    def wait(self):
        now = time.time()
        diff = self.interval - (now - self.last_call)
        if diff > 0:
            time.sleep(diff)
        self.last_call = time.time()


# ── 数据持久化 ────────────────────────────────────────
DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)


def save_json(filename, data):
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    return path


def load_json(filename, default=None):
    path = DATA_DIR / filename
    if not path.exists():
        return default if default is not None else {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── HTTP 客户端基类 ──────────────────────────────────
class BaseAPIClient:
    """平台 API 客户端基类"""

    def __init__(self, platform_name, config):
        self.platform = platform_name
        self.config = config
        self.api_base = config.get("api_base", "")
        self.rate_limiter = RateLimiter(config.get("rate_limit", 10))
        self.timeout = config.get("timeout", 30)
        self.session = requests.Session()
        self.logger = setup_logger(f"social.{platform_name}")

    def _headers(self):
        return {"Content-Type": "application/json", "User-Agent": "SocialAutomation/1.0"}

    def _request(self, method, url, **kwargs):
        self.rate_limiter.wait()
        kwargs.setdefault("timeout", self.timeout)
        kwargs.setdefault("headers", {}).update(self._headers())
        resp = self.session.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def get(self, url, **kwargs):
        return self._request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self._request("POST", url, **kwargs)

    def put(self, url, **kwargs):
        return self._request("PUT", url, **kwargs)

    def delete(self, url, **kwargs):
        return self._request("DELETE", url, **kwargs)
