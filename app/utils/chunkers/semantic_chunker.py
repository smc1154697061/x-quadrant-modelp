"""
语义分块策略
"""
from typing import List
from langchain.schema import Document

from app.utils.chunkers.base_chunker import BaseChunker
from common import log_


class SemanticChunker(BaseChunker):
    """语义分块策略 - 基于语义相似度分割"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, embeddings_model=None):
        super().__init__(chunk_size, chunk_overlap)
        self.embeddings_model = embeddings_model
    
    @property
    def strategy_name(self) -> str:
        return "semantic"
    
    def split(self, documents: List[Document]) -> List[Document]:
        """
        使用语义相似度分割文档
        
        Args:
            documents: 文档对象列表
            
        Returns:
            List[Document]: 分割后的文档块列表
        """
        try:
            if self.embeddings_model is None:
                from app.models.embeddings.base import get_embeddings_model
                self.embeddings_model = get_embeddings_model()
            
            from langchain_experimental.text_splitter import SemanticChunker as LangChainSemanticChunker
            
            semantic_splitter = LangChainSemanticChunker(
                embeddings=self.embeddings_model,
                breakpoint_threshold_type="percentile",
                breakpoint_threshold_amount=95
            )
            
            all_chunks = []
            for doc in documents:
                chunks = semantic_splitter.split_documents([doc])
                all_chunks.extend(chunks)
            
            return all_chunks
        except Exception as e:
            log_.warning(f"语义分块失败，回退到固定分块: {str(e)}")
            from app.utils.chunkers.fixed_chunker import FixedChunker
            fallback_chunker = FixedChunker(self.chunk_size, self.chunk_overlap)
            return fallback_chunker.split(documents)
