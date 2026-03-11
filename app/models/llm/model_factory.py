from config.base import LLM_PROVIDER
from common import log_

def get_llm_model():
    """
    根据配置返回对应的 LLM 实现。
    支持提供者：'ollama'（默认）、'openai_compatible'（DeepSeek/其他OpenAI兼容）。
    """
    provider = (LLM_PROVIDER or 'ollama').strip().lower()
    if provider == 'ollama':
        from app.models.llm.ollama_model import OllamaModel
        return OllamaModel()
    elif provider in ('openai', 'deepseek', 'openai_compatible'):
        from app.models.llm.openai_compatible_model import OpenAICompatibleModel
        return OpenAICompatibleModel()
    else:
        log_.warning(f"未知的LLM_PROVIDER: {provider}，回退到Ollama")
        from app.models.llm.ollama_model import OllamaModel
        return OllamaModel()

