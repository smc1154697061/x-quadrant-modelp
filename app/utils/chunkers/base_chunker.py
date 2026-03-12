"""
分块策略抽象基类
"""
from abc import ABC, abstractmethod
from typing import List
from langchain.schema import Document


class BaseChunker(ABC):
    """文档分块抽象基类"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    @abstractmethod
    def split(self, documents: List[Document]) -> List[Document]:
        """
        分割文档为小块
        
        Args:
            documents: 文档对象列表
            
        Returns:
            List[Document]: 分割后的文档块列表
        """
        pass
    
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """返回策略名称"""
        pass
