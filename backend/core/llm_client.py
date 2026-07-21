"""
LLM 统一客户端 — 优先走 LiteLLM 代理，fallback 直连 DeepSeek
"""
import logging
from config import settings

logger = logging.getLogger("mitouai.llm")


class LLMClient:
    """统一的 LLM 调用客户端"""

    def __init__(self, model: str = None):
        self.model = model or settings.DEFAULT_MODEL
        self._client = None

    @property
    def client(self):
        """懒加载 OpenAI 兼容客户端"""
        if self._client is None:
            try:
                from openai import OpenAI
                # 优先用 LiteLLM 代理
                if settings.LITELLM_API_BASE and settings.LITELLM_MASTER_KEY:
                    self._client = OpenAI(
                        base_url=f"{settings.LITELLM_API_BASE}/v1",
                        api_key=settings.LITELLM_MASTER_KEY,
                    )
                    logger.info(f"LLM 客户端: LiteLLM ({settings.LITELLM_API_BASE})")
                # Fallback 直连 DeepSeek
                elif settings.DEEPSEEK_API_KEY:
                    self._client = OpenAI(
                        base_url=settings.DEEPSEEK_BASE_URL,
                        api_key=settings.DEEPSEEK_API_KEY,
                    )
                    logger.info("LLM 客户端: DeepSeek 直连")
                    self.model = "deepseek-chat"
                else:
                    raise RuntimeError("未配置任何 LLM API Key")
            except ImportError:
                raise RuntimeError("请安装 openai 包: pip install openai")
        return self._client

    def chat(self, messages: list[dict], **kwargs) -> str:
        """同步调用"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 4096),
        )
        return response.choices[0].message.content

    async def achat(self, messages: list[dict], **kwargs) -> str:
        """异步调用"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.chat, messages, kwargs)


# 全局单例
llm = LLMClient()
