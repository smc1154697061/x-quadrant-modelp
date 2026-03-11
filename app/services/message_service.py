"""
消息服务类 - 处理消息相关的业务逻辑（Java风格）
"""
from typing import List, Dict
from common import log_
from common.error_codes import APIException, ErrorCode
from app.dao.message_dao import MessageDAO
from app.dao.message_document_dao import MessageDocumentDAO
from app.entity.message import Message


class MessageService:
    """消息服务类，处理消息相关的业务逻辑"""
    
    @classmethod
    def save_message(cls, conversation_id: int, role: str, content: str) -> Dict:
        """保存消息
        
        参数:
            conversation_id: 对话ID
            role: 角色（user/assistant）
            content: 消息内容
        
        返回:
            消息信息字典
        """
        try:
            # 创建Message实体
            message = Message(
                conversation_id=conversation_id,
                role=role,
                content=content
            )
            
            # 调用DAO保存
            message_dict = MessageDAO().save_message(message)
            return message_dict
        except Exception as e:
            log_.error(f"保存消息失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"保存消息失败: {str(e)}")
    
    @classmethod
    def get_messages(cls, conversation_id: int) -> List[Dict]:
        """获取对话的所有消息（包含附件）
        
        参数:
            conversation_id: 对话ID
        
        返回:
            消息列表（每条消息包含 attachments 字段）
        """
        try:
            messages = MessageDAO().get_messages(conversation_id)
            message_document_dao = MessageDocumentDAO()

            # 延迟导入，避免循环依赖
            from common.minio_client import MinioClient
            from config.base import MINIO_DEFAULT_BUCKET

            minio_client = MinioClient.get_instance()

            # 为每条消息添加附件信息
            for message in messages:
                message_id = message.get('id')
                if message_id:
                    attachments = message_document_dao.get_message_documents(message_id)

                    # 为每个附件增加预览URL和预览能力标记（目前仅支持txt）
                    enhanced_attachments = []
                    for att in attachments:
                        minio_path = att.get('minio_path')
                        file_type = (att.get('file_type') or '').lower()
                        preview_url = None

                        if minio_path and minio_client:
                            try:
                                preview_url = minio_client.get_presigned_url(
                                    object_name=minio_path,
                                    bucket_name=MINIO_DEFAULT_BUCKET
                                )
                            except Exception as e:
                                log_.error(f"生成附件预览URL失败: {str(e)}")
                                preview_url = None

                        att['preview_url'] = preview_url
                        # 目前只支持txt文件在线预览
                        att['previewable'] = (file_type == 'txt')
                        enhanced_attachments.append(att)

                    message['attachments'] = enhanced_attachments
                else:
                    message['attachments'] = []

            return messages
        except Exception as e:
            log_.error(f"获取消息列表失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"获取消息列表失败: {str(e)}")
    
    @classmethod
    def delete_conversation_messages(cls, conversation_id: int) -> bool:
        """删除对话的所有消息
        
        参数:
            conversation_id: 对话ID
        
        返回:
            是否删除成功
        """
        try:
            success = MessageDAO().delete_conversation_messages(conversation_id)
            
            return success
        except Exception as e:
            log_.error(f"删除对话消息失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"删除对话消息失败: {str(e)}")
