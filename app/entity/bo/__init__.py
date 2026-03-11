"""
Business Object - 业务对象，用于Service层业务逻辑处理
"""
from .user_bo import UserBO
from .bot_bo import BotBO
from .conversation_bo import ConversationBO
from .message_bo import MessageBO

__all__ = ['UserBO', 'BotBO', 'ConversationBO', 'MessageBO']
