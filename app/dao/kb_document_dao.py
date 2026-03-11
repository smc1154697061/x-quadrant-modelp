"""
知识库-文档关联表DAO - 管理知识库和文档的多对多关系
"""
from typing import List
from common.db_utils import get_db_connection
from common import log_


class KBDocumentDAO:
    """知识库-文档关联表DAO"""
    
    def add_document_to_kb(self, kb_id: int, document_id: int):
        """将文档添加到知识库
        
        Args:
            kb_id: 知识库ID
            document_id: 文档ID
        
        Returns:
            bool: 是否成功
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO dodo_kb_documents (kb_id, document_id) VALUES (%s, %s)",
                        (kb_id, document_id)
                    )
            return True
        except Exception as e:
            log_.error(f"添加文档到知识库失败: {str(e)}")
            return False
    
    def remove_document_from_kb(self, kb_id: int, document_id: int):
        """从知识库移除文档
        
        Args:
            kb_id: 知识库ID
            document_id: 文档ID
        
        Returns:
            bool: 是否成功
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM dodo_kb_documents WHERE kb_id = %s AND document_id = %s",
                        (kb_id, document_id)
                    )
            return True
        except Exception as e:
            log_.error(f"从知识库移除文档失败: {str(e)}")
            return False
    
    def get_kb_documents(self, kb_id: int) -> List[int]:
        """获取知识库的所有文档ID
        
        Args:
            kb_id: 知识库ID
        
        Returns:
            List[int]: 文档ID列表
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT document_id FROM dodo_kb_documents WHERE kb_id = %s",
                        (kb_id,)
                    )
                    return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            log_.error(f"获取知识库文档失败: {str(e)}")
            return []
    
    def get_document_kbs(self, document_id: int) -> List[int]:
        """获取文档所属的所有知识库ID
        
        Args:
            document_id: 文档ID
        
        Returns:
            List[int]: 知识库ID列表
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT kb_id FROM dodo_kb_documents WHERE document_id = %s",
                        (document_id,)
                    )
                    return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            log_.error(f"获取文档所属知识库失败: {str(e)}")
            return []
    
    def is_document_in_kb(self, kb_id: int, document_id: int) -> bool:
        """检查文档是否在知识库中
        
        Args:
            kb_id: 知识库ID
            document_id: 文档ID
        
        Returns:
            bool: 是否存在关联
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT COUNT(*) FROM dodo_kb_documents WHERE kb_id = %s AND document_id = %s",
                        (kb_id, document_id)
                    )
                    count = cursor.fetchone()[0]
                    return count > 0
        except Exception as e:
            log_.error(f"检查文档知识库关联失败: {str(e)}")
            return False
    
    def batch_add_documents_to_kb(self, kb_id: int, document_ids: List[int]):
        """批量将文档添加到知识库
        
        Args:
            kb_id: 知识库ID
            document_ids: 文档ID列表
        
        Returns:
            int: 成功添加的数量
        """
        if not document_ids:
            return 0
        
        success_count = 0
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    for document_id in document_ids:
                        try:
                            cursor.execute(
                                "INSERT INTO dodo_kb_documents (kb_id, document_id) VALUES (%s, %s)",
                                (kb_id, document_id)
                            )
                            success_count += 1
                        except Exception as e:
                            log_.warning(f"添加文档{document_id}到知识库{kb_id}失败: {str(e)}")
                            continue
            return success_count
        except Exception as e:
            log_.error(f"批量添加文档到知识库失败: {str(e)}")
            return success_count
    
    def remove_all_documents_from_kb(self, kb_id: int):
        """删除知识库的所有文档关联（不删除文档本身）
        
        Args:
            kb_id: 知识库ID
        
        Returns:
            int: 删除的关联数量
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM dodo_kb_documents WHERE kb_id = %s",
                        (kb_id,)
                    )
                    return cursor.rowcount
        except Exception as e:
            log_.error(f"删除知识库所有文档关联失败: {str(e)}")
            return 0
