"""
向量存储基础模块
"""
from typing import Dict, List, Any, Optional

class BaseVectorStore:
    """向量存储基础接口"""
    
    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """
        向向量存储添加文本
        
        Args:
            texts: 文本列表
            metadatas: 元数据列表
            
        Returns:
            List[str]: 文档ID列表
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def search(self, query: str, k: int = 4) -> List[Dict[str, Any]]:
        """
        搜索与查询最相似的文档
        
        Args:
            query: 查询字符串
            k: 返回结果数量
            
        Returns:
            List[Dict[str, Any]]: 搜索结果列表
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def delete(self, ids: List[str]) -> None:
        """
        删除文档
        
        Args:
            ids: 文档ID列表
        """
        raise NotImplementedError("子类必须实现此方法")

def get_vector_store() -> BaseVectorStore:
    """
    获取向量存储实例
    
    Returns:
        BaseVectorStore: 向量存储实例
    """
    from app.models.vector_store.pg_vector_store import PGVectorStore
    return PGVectorStore() 