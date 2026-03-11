import requests
from typing import List, Dict, Any
from config.base import OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT
from common import log_


class OpenAICompatibleModel:
    """
    兼容 OpenAI Chat Completions API 的模型封装。
    可用于 DeepSeek、Moonshot 等兼容实现（通过自定义 base_url 和 api_key）。
    """
    def __init__(self):
        self.base_url = OPENAI_BASE_URL.rstrip('/')
        self.api_key = OPENAI_API_KEY
        self.model = OPENAI_MODEL
        self.timeout = OPENAI_TIMEOUT or 30
        if not self.base_url or not self.api_key or not self.model:
            raise ValueError("OpenAI-Compatible 配置不完整，请在 config/base.py 设置 OPENAI_BASE_URL/OPENAI_API_KEY/OPENAI_MODEL")

    def _build_messages(self, prompt: str) -> List[Dict[str, Any]]:
        # 将长 prompt 作为 user 消息；若包含系统提示词可按约定自行拆分
        return [{"role": "user", "content": prompt}]

    def invoke(self, question: str) -> str:
        """
        简单的非流式调用，输入文本返回字符串回答。
        与 OllamaModel 接口保持一致。
        """
        try:
            url = f"{self.base_url}/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": self._build_messages(question),
                "temperature": 0.7
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            if resp.status_code != 200:
                log_.error(f"OpenAI-Compatible 调用失败: {resp.status_code} {resp.text[:200]}")
                return f"调用模型出错: HTTP {resp.status_code}"
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content or ""
        except Exception as e:
            log_.error(f"OpenAI-Compatible 调用异常: {str(e)}")
            return f"调用模型出错: {str(e)}"

