"""
固定长度分块器
基于固定字符长度进行文档分块
"""
from typing import List
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.utils.chunkers.base_chunker import BaseChunker


class FixedChunker(BaseChunker):
    """
    固定长度分块器
    
    使用递归字符文本分割器，按固定长度分割文档，
    支持多种分隔符优先级：段落 -> 换行 -> 空格 -> 字符
    """
    
    @property
    def strategy_name(self) -> str:
        return "fixed"
    
    def split(self, docs: List[Document]) -> List[Document]:
        """
        使用固定长度策略分割文档
        
        Args:
            docs: 文档对象列表
            
        Returns:
            List[Document]: 分割后的文档块列表
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.split_documents(docs)
        return chunks
