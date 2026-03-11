"""
聊天数据传输对象 - 接收前端请求参数
"""
from typing import Optional, List
from common.error_codes import ParameterError


class ChatMessageDTO:
    """聊天消息请求参数"""
    
    def __init__(self, bot_id: int, message: str, conversation_id: Optional[int] = None):
        self.bot_id = bot_id
        self.message = message
        self.conversation_id = conversation_id
    
    def validate(self):
        """参数校验"""
        if not self.bot_id:
            raise ParameterError(msg="机器人ID不能为空")
        if not self.message:
            raise ParameterError(msg="消息内容不能为空")
        if len(self.message) > 10000:
            raise ParameterError(msg="消息内容不能超过10000个字符")
        return True
    
    @classmethod
    def from_request(cls, data: dict):
        """从请求数据创建"""
        return cls(
            bot_id=data.get('bot_id'),
            message=data.get('message'),
            conversation_id=data.get('conversation_id')
        )


class GetMessagesDTO:
    """获取消息列表请求参数"""
    
    def __init__(self, conversation_id: int, limit: int = 100):
        self.conversation_id = conversation_id
        self.limit = limit
    
    def validate(self):
        """参数校验"""
        if not self.conversation_id:
            raise ParameterError(msg="对话ID不能为空")
        if self.limit < 1 or self.limit > 1000:
            raise ParameterError(msg="限制数量必须在1-1000之间")
        return True
    
    @classmethod
    def from_request(cls, data: dict):
        """从请求数据创建"""
        return cls(
            conversation_id=data.get('conversation_id'),
            limit=data.get('limit', 100)
        )
