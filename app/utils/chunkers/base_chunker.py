"""
分块器抽象基类
定义文档分块的标准接口
"""
from abc import ABC, abstractmethod
from typing import List
from langchain.schema import Document


class BaseChunker(ABC):
    """文档分块器抽象基类"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        初始化分块器
        
        Args:
            chunk_size: 分块大小（字符数）
            chunk_overlap: 分块重叠大小（字符数）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    @abstractmethod
    def split(self, docs: List[Document]) -> List[Document]:
        """
        分割文档为小块
        
        Args:
            docs: 文档对象列表
            
        Returns:
            List[Document]: 分割后的文档块列表
        """
        pass
    
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """
        返回分块策略名称
        
        Returns:
            str: 策略名称
        """
        pass
