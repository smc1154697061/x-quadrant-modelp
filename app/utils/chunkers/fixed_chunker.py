"""
固定长度分块策略
"""
from typing import List
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.utils.chunkers.base_chunker import BaseChunker


class FixedChunker(BaseChunker):
    """固定长度分块策略 - 使用递归字符分割器"""
    
    @property
    def strategy_name(self) -> str:
        return "fixed"
    
    def split(self, documents: List[Document]) -> List[Document]:
        """
        使用固定长度分割文档
        
        Args:
            documents: 文档对象列表
            
        Returns:
            List[Document]: 分割后的文档块列表
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", ".", "!", "?", ";", " ", ""]
        )
        
        chunks = text_splitter.split_documents(documents)
        return chunks
