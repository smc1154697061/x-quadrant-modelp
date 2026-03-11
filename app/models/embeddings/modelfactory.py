from langchain_community.embeddings import ModelScopeEmbeddings
from config.base import EMBEDDINGS_MODEL_ID
import threading

class EmbeddingModelFactory:
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_embeddings(cls):
        """获取嵌入模型实例（单例模式）"""
        # 首先检查Flask g对象中是否已有模型实例
        try:
            from flask import g
            if hasattr(g, 'embedding_model') and g.embedding_model is not None:
                return g.embedding_model
        except:
            pass
            
        # 其次检查应用上下文中是否有模型实例
        try:
            from flask import current_app
            if hasattr(current_app, 'embedding_model') and current_app.embedding_model is not None:
                return current_app.embedding_model
        except:
            pass
        
        # 最后检查类级别的单例实例
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = ModelScopeEmbeddings(
                        model_id=EMBEDDINGS_MODEL_ID
                    )
        
        return cls._instance
