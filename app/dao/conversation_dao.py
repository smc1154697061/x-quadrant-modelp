"""对话Mapper - MyBatis Plus风格"""
from typing import List, Optional
from app.dao.mapper import BaseMapper, select
from app.entity.conversation import Conversation

class ConversationDAO(BaseMapper):
    """对话Mapper，继承BaseMapper获得通用CRUD"""
    
    entity_class = Conversation
    table_name = 'dodo_conversations'
    primary_key = 'id'
    
    def create_conversation(self, conversation: Conversation):
        """创建新的对话（面向对象风格）
        
        参数:
            conversation: Conversation实体对象
        
        返回:
            创建后的Conversation字典（包含id）
        """
        conv_id = self.insert(conversation)
        conversation.id = conv_id
        return conversation.to_dict()
    
    def get_conversation(self, conversation_id):
        """获取对话信息"""
        conversation = self.select_by_id(conversation_id)
        return conversation.to_dict() if conversation else None
    
    @select("SELECT * FROM dodo_conversations WHERE user_id = %s AND bot_id = %s ORDER BY created_at DESC LIMIT 1", Conversation)
    def _find_recent_conversation(self, user_id: int, bot_id: int) -> Optional[Conversation]:
        pass
    
    def get_or_create_conversation(self, user_id, bot_id):
        """获取或创建用户与机器人的对话"""
        conversation = self._find_recent_conversation(user_id, bot_id)
        if conversation:
            return conversation.to_dict()
        return self.create_conversation(user_id, bot_id)
    
    @select("SELECT * FROM dodo_conversations WHERE user_id = %s ORDER BY created_at DESC", Conversation)
    def _get_user_all_conversations(self, user_id: int) -> List[Conversation]:
        pass
    
    @select("SELECT * FROM dodo_conversations WHERE user_id = %s AND bot_id = %s ORDER BY created_at DESC", Conversation)
    def _get_user_bot_conversations(self, user_id: int, bot_id: int) -> List[Conversation]:
        pass
    
    def get_user_conversations(self, user_id, bot_id=None):
        """获取用户的对话列表，可选按机器人ID过滤"""
        if bot_id:
            conversations = self._get_user_bot_conversations(user_id, bot_id)
        else:
            conversations = self._get_user_all_conversations(user_id)
        # @select装饰器已返回dict列表，无需再调用to_dict()
        return conversations
    
    def delete_conversation(self, conversation_id):
        """删除对话"""
        return self.delete_by_id(conversation_id) > 0