"""
文档分块策略模块
"""
from app.utils.chunkers.base_chunker import BaseChunker
from app.utils.chunkers.fixed_chunker import FixedChunker
from app.utils.chunkers.semantic_chunker import SemanticChunker
from app.utils.chunkers.sentence_chunker import SentenceChunker

__all__ = ['BaseChunker', 'FixedChunker', 'SemanticChunker', 'SentenceChunker', 'get_chunker']

def get_chunker(strategy: str, chunk_size: int = 1000, chunk_overlap: int = 200):
    """
    根据策略获取对应的分块器
    
    Args:
        strategy: 分块策略
        chunk_size: 分块大小
        chunk_overlap: 分块重叠大小
        
    Returns:
        BaseChunker: 分块器实例
    """
    chunkers = {
        'fixed': FixedChunker,
        'semantic': SemanticChunker,
        'sentence': SentenceChunker
    }
    
    chunker_cls = chunkers.get(strategy, FixedChunker)
    return chunker_cls(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
