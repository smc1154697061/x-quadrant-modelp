"""
句子分块策略
"""
import re
from typing import List
from langchain.schema import Document

from app.utils.chunkers.base_chunker import BaseChunker


class SentenceChunker(BaseChunker):
    """句子分块策略 - 按句子边界分割"""
    
    @property
    def strategy_name(self) -> str:
        return "sentence"
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        将文本分割成句子
        
        Args:
            text: 输入文本
            
        Returns:
            List[str]: 句子列表
        """
        sentence_endings = r'(?<=[。！？.!?])\s*'
        sentences = re.split(sentence_endings, text)
        return [s.strip() for s in sentences if s.strip()]
    
    def split(self, documents: List[Document]) -> List[Document]:
        """
        按句子分割文档
        
        Args:
            documents: 文档对象列表
            
        Returns:
            List[Document]: 分割后的文档块列表
        """
        all_chunks = []
        
        for doc in documents:
            text = doc.page_content
            metadata = doc.metadata.copy()
            
            sentences = self._split_into_sentences(text)
            
            current_chunk = []
            current_length = 0
            
            for sentence in sentences:
                sentence_length = len(sentence)
                
                if current_length + sentence_length > self.chunk_size and current_chunk:
                    chunk_text = ''.join(current_chunk)
                    all_chunks.append(Document(
                        page_content=chunk_text,
                        metadata=metadata.copy()
                    ))
                    
                    if self.chunk_overlap > 0:
                        overlap_text = chunk_text[-self.chunk_overlap:] if len(chunk_text) > self.chunk_overlap else chunk_text
                        current_chunk = [overlap_text]
                        current_length = len(overlap_text)
                    else:
                        current_chunk = []
                        current_length = 0
                
                current_chunk.append(sentence)
                current_length += sentence_length
            
            if current_chunk:
                all_chunks.append(Document(
                    page_content=''.join(current_chunk),
                    metadata=metadata.copy()
                ))
        
        return all_chunks
