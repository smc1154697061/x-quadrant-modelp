"""
语义分块器
基于语义相似性进行文档分块
"""
from typing import List
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.utils.chunkers.base_chunker import BaseChunker
from common import log_


class SemanticChunker(BaseChunker):
    """
    语义分块器
    
    基于段落和语义边界进行分块，优先保持段落完整性，
    适合长文档和需要保持段落语义连贯性的场景
    """
    
    @property
    def strategy_name(self) -> str:
        return "semantic"
    
    def split(self, docs: List[Document]) -> List[Document]:
        """
        使用语义边界策略分割文档
        
        优先保持段落完整性，在段落内部再按句子边界分割
        
        Args:
            docs: 文档对象列表
            
        Returns:
            List[Document]: 分割后的文档块列表
        """
        # 优先使用段落分隔，保持语义完整性
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=[
                "\n\n",      # 段落（最高优先级）
                "\n",         # 换行
                "。 ",        # 中文句号+空格
                ". ",         # 英文句号+空格
                "；",         # 中文分号
                ";",          # 英文分号
                "，",         # 中文逗号
                ",",          # 英文逗号
                " ",          # 空格
                ""            # 字符
            ]
        )
        
        try:
            chunks = text_splitter.split_documents(docs)
            
            # 如果分块数量过多，进行合并优化
            chunks = self._optimize_chunks(chunks)
            
            return chunks
        except Exception as e:
            log_.error(f"语义分块失败: {str(e)}")
            # 降级为固定长度分块
            from app.utils.chunkers.fixed_chunker import FixedChunker
            fallback_chunker = FixedChunker(self.chunk_size, self.chunk_overlap)
            return fallback_chunker.split(docs)
    
    def _optimize_chunks(self, chunks: List[Document]) -> List[Document]:
        """
        优化分块结果，合并过小的块
        
        Args:
            chunks: 原始分块列表
            
        Returns:
            List[Document]: 优化后的分块列表
        """
        if not chunks:
            return chunks
        
        optimized = []
        current_chunk = None
        min_chunk_size = self.chunk_size // 4  # 最小块大小为1/4目标大小
        
        for chunk in chunks:
            if current_chunk is None:
                current_chunk = chunk
            elif len(current_chunk.page_content) < min_chunk_size:
                # 当前块太小，尝试合并
                combined_content = current_chunk.page_content + "\n\n" + chunk.page_content
                if len(combined_content) <= self.chunk_size:
                    # 合并块
                    current_chunk.page_content = combined_content
                    # 合并元数据
                    current_chunk.metadata.update(chunk.metadata)
                else:
                    # 无法合并，保存当前块
                    optimized.append(current_chunk)
                    current_chunk = chunk
            else:
                # 当前块大小合适，保存并继续
                optimized.append(current_chunk)
                current_chunk = chunk
        
        # 添加最后一个块
        if current_chunk is not None:
            optimized.append(current_chunk)
        
        return optimized
