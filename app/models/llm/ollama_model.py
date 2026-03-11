from langchain_ollama import OllamaLLM
from config.base import OLLAMA_MODEL, OLLAMA_BASE_URL, OLLAMA_TEMPERATURE
from common import log_
from common.error_codes import ModelCallError
import threading

class OllamaModel:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(OllamaModel, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        # 首先检查Flask g对象中是否已有模型实例
        try:
            from flask import g
            if hasattr(g, 'llm_model') and g.llm_model is not None:
                self.llm = g.llm_model.llm
                self._initialized = True
                return
        except:
            pass
            
        # 其次检查应用上下文中是否有模型实例
        try:
            from flask import current_app
            if hasattr(current_app, 'llm_model') and current_app.llm_model is not None:
                self.llm = current_app.llm_model.llm
                self._initialized = True
                return
        except:
            pass
        
        # 如果没有找到已有实例，则创建新的
        self.llm = OllamaLLM(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=OLLAMA_TEMPERATURE,
        )
        self._initialized = True

    def invoke(self, question: str) -> str:
        """非流式调用，返回完整响应"""
        try:
            response = self.llm.invoke(question)
            return response
        except Exception as e:
            log_.error(f"模型调用失败: {str(e)}")
            # 抛出ModelCallError异常而不是返回错误字符串
            raise ModelCallError(f"调用模型出错: {str(e)}")
    
    def stream(self, question: str):
        """流式调用，返回生成器，逐字输出响应
        
        Args:
            question: 用户问题/提示词
            
        Yields:
            str: 每个token的文本内容
        """
        try:
            # 使用langchain的stream方法
            for chunk in self.llm.stream(question):
                if chunk:
                    yield chunk
        except Exception as e:
            log_.error(f"模型流式调用失败: {str(e)}")
            raise ModelCallError(f"调用模型出错: {str(e)}")