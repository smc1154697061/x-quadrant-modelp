"""
对话服务类 - 处理对话相关的业务逻辑（Java风格）
"""
from typing import List, Optional, Dict
from common import log_
from common.error_codes import APIException, ErrorCode, ResourceNotFound
from app.dao.conversation_dao import ConversationDAO
from app.entity.conversation import Conversation


class ConversationService:
    """对话服务类，处理对话相关的业务逻辑"""
    
    @classmethod
    def create_conversation(cls, user_id: int, bot_id: int) -> Dict:
        """创建对话
        
        参数:
            user_id: 用户ID
            bot_id: 机器人ID
        
        返回:
            对话信息字典
        """
        try:
            # 创建Conversation实体
            conversation = Conversation(
                user_id=user_id,
                bot_id=bot_id
            )
            
            # 调用DAO创建
            conversation_dict = ConversationDAO().create_conversation(conversation)
            
            return conversation_dict
        except Exception as e:
            log_.error(f"创建对话失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"创建对话失败: {str(e)}")
    
    @classmethod
    def get_conversation(cls, conversation_id: int, user_id: int = None) -> Dict:
        """获取对话详情
        
        参数:
            conversation_id: 对话ID
            user_id: 当前用户ID（用于权限检查）
        
        返回:
            对话信息字典
        """
        try:
            conversation = ConversationDAO().get_conversation(conversation_id)
            
            if not conversation:
                raise ResourceNotFound(msg="对话不存在")
            
            # 权限检查
            if user_id and conversation.get('user_id') != user_id:
                raise APIException(ErrorCode.PERMISSION_DENIED, msg="无权访问此对话")
            
            return conversation
        except (ResourceNotFound, APIException):
            raise
        except Exception as e:
            log_.error(f"获取对话失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"获取对话失败: {str(e)}")
    
    @classmethod
    def get_user_conversations(cls, user_id: int, bot_id: int = None) -> List[Dict]:
        """获取用户的对话列表
        
        参数:
            user_id: 用户ID
            bot_id: 可选的机器人ID过滤
        
        返回:
            对话列表
        """
        try:
            conversations = ConversationDAO().get_user_conversations(user_id, bot_id)
            return conversations
        except Exception as e:
            log_.error(f"获取对话列表失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"获取对话列表失败: {str(e)}")
    
    @classmethod
    def delete_conversation(cls, conversation_id: int, user_id: int) -> bool:
        """删除对话
        
        参数:
            conversation_id: 对话ID
            user_id: 当前用户ID（用于权限检查）
        
        返回:
            是否删除成功
        """
        try:
            # 验证对话存在和权限
            conversation = cls.get_conversation(conversation_id, user_id)
            
            # 调用DAO删除
            success = ConversationDAO().delete_conversation(conversation_id)
            
            return success
        except (ResourceNotFound, APIException):
            raise
        except Exception as e:
            log_.error(f"删除对话失败: {str(e)}")
            raise APIException(ErrorCode.SYSTEM_ERROR, msg=f"删除对话失败: {str(e)}")
