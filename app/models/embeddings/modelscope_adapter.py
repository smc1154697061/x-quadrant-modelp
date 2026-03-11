"""
ModelScope嵌入模型适配器
"""
from typing import List, Any
from app.models.embeddings.base import BaseEmbeddingsModel

class ModelScopeAdapter(BaseEmbeddingsModel):
    """ModelScope嵌入模型适配器，适配我们的接口"""
    
    def __init__(self, modelscope_embeddings):
        """
        初始化适配器
        
        Args:
            modelscope_embeddings: ModelScopeEmbeddings实例
        """
        self.embeddings = modelscope_embeddings
        self.embedding_dim = 768  # 默认维度，实际上应该从模型中获取
    
    def embed_query(self, text: str) -> List[float]:
        """
        将单个查询文本转换为嵌入向量
        
        Args:
            text: 查询文本
            
        Returns:
            List[float]: 嵌入向量
        """
        try:
            # 处理文本 - 替换换行符和多余空格
            text = text.replace("\n", " ").strip()
            if not text:
                # 如果文本为空，返回全零向量
                return [0.0] * self.embedding_dim
            
            # 使用ModelScope获取嵌入
            embedding = self.embeddings.embed_query(text)
            
            # 确保是列表类型
            if hasattr(embedding, "tolist"):
                embedding = embedding.tolist()
            else:
                embedding = list(embedding)
                
            return embedding
        except Exception as e:
            from common import log_
            log_.error(f"获取查询嵌入失败: {str(e)}")
            # 失败时返回全零向量
            return [0.0] * self.embedding_dim
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        将多个文档文本转换为嵌入向量列表
        
        Args:
            texts: 文档文本列表
            
        Returns:
            List[List[float]]: 嵌入向量列表
        """
        try:
            # 处理空列表情况
            if not texts:
                return []
            
            # 处理文本 - 替换换行符和多余空格
            processed_texts = [text.replace("\n", " ").strip() for text in texts]
            
            # 过滤空文本
            valid_indices = [i for i, text in enumerate(processed_texts) if text]
            valid_texts = [processed_texts[i] for i in valid_indices]
            
            if not valid_texts:
                return [[0.0] * self.embedding_dim] * len(texts)
            
            # 调用ModelScope获取嵌入
            embeddings = self.embeddings.embed_documents(valid_texts)
            
            # 确保所有向量都是列表类型
            embeddings = [
                e.tolist() if hasattr(e, "tolist") else list(e)
                for e in embeddings
            ]
            
            # 重组结果，确保与原始texts顺序匹配
            result = []
            embedding_idx = 0
            
            for i in range(len(texts)):
                if i in valid_indices:
                    result.append(embeddings[embedding_idx])
                    embedding_idx += 1
                else:
                    # 对于空文本，返回全零向量
                    result.append([0.0] * self.embedding_dim)
            
            return result
        except Exception as e:
            from common import log_
            log_.error(f"获取文档嵌入失败: {str(e)}")
            # 失败时返回全零向量列表
            return [[0.0] * self.embedding_dim] * len(texts) 