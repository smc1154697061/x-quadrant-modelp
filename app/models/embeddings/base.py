"""
嵌入模型基础模块
"""
from typing import List, Dict, Any, Optional

class BaseEmbeddingsModel:
    """嵌入模型基础接口"""
    
    def embed_query(self, text: str) -> List[float]:
        """
        将单个查询文本转换为嵌入向量
        
        Args:
            text: 查询文本
            
        Returns:
            List[float]: 嵌入向量
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        将多个文档文本转换为嵌入向量列表
        
        Args:
            texts: 文档文本列表
            
        Returns:
            List[List[float]]: 嵌入向量列表
        """
        raise NotImplementedError("子类必须实现此方法")

def get_embeddings_model() -> BaseEmbeddingsModel:
    """
    获取嵌入模型实例
    
    Returns:
        BaseEmbeddingsModel: 嵌入模型实例
    """
    from app.models.embeddings.modelscope_adapter import ModelScopeAdapter
    from app.models.embeddings.modelfactory import EmbeddingModelFactory
    
    # 使用已有的ModelScope嵌入模型
    embeddings = EmbeddingModelFactory.get_embeddings()
    return ModelScopeAdapter(embeddings) 