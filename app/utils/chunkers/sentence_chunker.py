"""
句子分块器
基于句子边界进行文档分块
"""
import re
from typing import List
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.utils.chunkers.base_chunker import BaseChunker


class SentenceChunker(BaseChunker):
    """
    句子分块器
    
    优先按句子边界分割文档，保持句子完整性，
    适合需要保持语义完整性的场景
    """
    
    @property
    def strategy_name(self) -> str:
        return "sentence"
    
    def split(self, docs: List[Document]) -> List[Document]:
        """
        使用句子边界策略分割文档
        
        Args:
            docs: 文档对象列表
            
        Returns:
            List[Document]: 分割后的文档块列表
        """
        # 使用句子分隔符作为优先分隔符
        # 支持中英文句子结束符
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=[
                "\n\n",  # 段落
                "\n",     # 换行
                "。",     # 中文句号
                "？",     # 中文问号
                "！",     # 中文感叹号
                ".",      # 英文句号
                "?",      # 英文问号
                "!",      # 英文感叹号
                "；",     # 中文分号
                ";",      # 英文分号
                " ",      # 空格
                ""        # 字符
            ]
        )
        
        chunks = text_splitter.split_documents(docs)
        return chunks
