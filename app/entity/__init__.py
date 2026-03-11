"""
实体层 - 包含所有数据库实体（PO）

注意：为避免循环导入，不在此处自动导入所有实体
请在需要时直接导入：
    from app.entity.user import User
    from app.entity.bot import Bot
    等等
"""

__all__ = [
    'User',
    'Bot',
    'Conversation',
    'Message',
    'KnowledgeBase',
    'Document',
    'DocumentChunk',
    'bot_knowledge_bases',
    'MessageRole'
]