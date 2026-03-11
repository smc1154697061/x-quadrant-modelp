"""消息Mapper - MyBatis Plus风格"""
from typing import List, Optional
from app.dao.mapper import BaseMapper, select, select_one
from app.entity.message import Message

class MessageDAO(BaseMapper):
    """消息Mapper，继承BaseMapper获得通用CRUD"""
    
    entity_class = Message
    table_name = 'dodo_messages'
    primary_key = 'id'
    
    def create_message(self, message: Message):
        """创建新的消息（面向对象风格）
        
        参数:
            message: Message实体对象
        
        返回:
            创建后的Message字典（包含id）
        """
        msg_id = self.insert(message)
        message.id = msg_id
        return message.to_dict()
    
    def get_message(self, message_id):
        """获取消息信息"""
        message = self.select_by_id(message_id)
        return message.to_dict() if message else None
    
    @select("SELECT * FROM dodo_messages WHERE conversation_id = %s ORDER BY created_at ASC LIMIT %s", Message)
    def _get_messages_query(self, conversation_id: int, limit: int) -> List[Message]:
        pass
    
    def get_messages(self, conversation_id, limit=100):
        """获取对话的消息列表"""
        messages = self._get_messages_query(conversation_id, limit)
        # @select装饰器已返回dict列表，无需再调用to_dict()
        return messages
    
    @select_one("SELECT * FROM dodo_messages WHERE conversation_id = %s ORDER BY created_at DESC LIMIT 1", Message)
    def _get_latest_message_query(self, conversation_id: int) -> Optional[Message]:
        pass
    
    def get_latest_message(self, conversation_id):
        """获取对话的最新消息"""
        message = self._get_latest_message_query(conversation_id)
        return message.to_dict() if message else None
    
    def delete_message(self, message_id):
        """删除消息"""
        return self.delete_by_id(message_id) > 0
    
    def delete_conversation_messages(self, conversation_id):
        """删除对话的所有消息"""
        return self.delete({'conversation_id': conversation_id}) > 0
    
    def count_messages(self, conversation_id):
        """统计对话的消息数量"""
        return self.count({'conversation_id': conversation_id})
    
    def save_message(self, message: Message):
        """保存消息到数据库（面向对象风格）
        
        参数:
            message: Message实体对象
        
        返回:
            创建后的Message字典（包含id）
        """
        return self.create_message(message)
    
    @select("SELECT * FROM dodo_messages WHERE conversation_id = %s ORDER BY created_at DESC LIMIT %s", Message)
    def _get_recent_messages_query(self, conversation_id: int, limit: int) -> List[Message]:
        pass
    
    def get_recent_messages(self, conversation_id, limit=10):
        """获取对话的最近消息"""
        messages = self._get_recent_messages_query(conversation_id, limit)
        # @select装饰器已返回dict列表，无需再调用to_dict()
        messages.reverse()
        return messages