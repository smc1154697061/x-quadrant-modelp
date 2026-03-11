"""
机器人Mapper - MyBatis Plus风格
"""
from typing import Optional, List
from app.dao.mapper import BaseMapper, select
from app.entity.bot import Bot
from common import log_
from common.db_utils import get_db_connection

class BotDAO(BaseMapper):
    """机器人Mapper，继承BaseMapper获得通用CRUD"""
    
    entity_class = Bot
    table_name = 'dodo_bots'
    primary_key = 'id'

    def create_bot(self, bot: Bot, kb_ids=None):
        """创建新的机器人（面向对象风格）
        
        参数:
            bot: Bot实体对象
            kb_ids: 关联的知识库ID列表（可选）
        
        返回:
            创建后的Bot字典（包含id和kb_ids）
        """
        # 插入Bot实体
        bot_id = self.insert(bot)
        bot.id = bot_id
        
        # 关联知识库
        if kb_ids:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    for kb_id in kb_ids:
                        cursor.execute(
                            "INSERT INTO dodo_bot_knowledge_bases (bot_id, kb_id) VALUES (%s, %s)",
                            (bot_id, kb_id)
                        )
        
        bot_dict = bot.to_dict()
        bot_dict['kb_ids'] = kb_ids if kb_ids else []
        return bot_dict
    
    def get_bot(self, bot_id):
        """获取机器人信息"""
        bot = self.select_by_id(bot_id)
        if not bot:
            return None
        
        bot_dict = bot.to_dict()
        
        # 查询关联的知识库
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT kb_id FROM dodo_bot_knowledge_bases WHERE bot_id = %s",
                    (bot_id,)
                )
                kb_ids = [row[0] for row in cursor.fetchall()]
                bot_dict['kb_ids'] = kb_ids
                
                # 查询知识库名称
                if kb_ids:
                    placeholders = ','.join(['%s'] * len(kb_ids))
                    cursor.execute(
                        f"SELECT name FROM dodo_knowledge_bases WHERE id IN ({placeholders})",
                        kb_ids
                    )
                    kb_names = [row[0] for row in cursor.fetchall()]
                    bot_dict['kb_names'] = kb_names
                else:
                    bot_dict['kb_names'] = []
        
        return bot_dict
    
    def update_bot(self, bot: Bot, kb_ids=None):
        """更新机器人信息（面向对象风格）
        
        参数:
            bot: Bot实体对象（必须包含id）
            kb_ids: 新的知识库ID列表（可选，None表示不更新关联）
        
        返回:
            更新后的Bot字典
        """
        if not bot.id:
            raise ValueError("Bot实体必须包含id字段")
        
        # 将Bot对象转为字典进行更新
        update_data = bot.to_dict()
        # 移除id字段（不更新主键）
        update_data.pop('id', None)
        # 移除created_at字段（不更新创建时间）
        update_data.pop('created_at', None)
        # 移除created_by字段（不更新创建者）
        update_data.pop('created_by', None)
        
        # 过滤掉值为 None 的字段，避免把数据库字段更新为 NULL
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        if update_data:
            self.update(update_data, {'id': bot.id})
        
        # 更新知识库关联
        if kb_ids is not None:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # 删除旧关联
                    cursor.execute("DELETE FROM dodo_bot_knowledge_bases WHERE bot_id = %s", (bot.id,))
                    # 添加新关联
                    for kb_id in kb_ids:
                        cursor.execute(
                            "INSERT INTO dodo_bot_knowledge_bases (bot_id, kb_id) VALUES (%s, %s)",
                            (bot.id, kb_id)
                        )
        
        return self.get_bot(bot.id)
    
    def delete_bot(self, bot_id):
        """删除机器人"""
        return self.delete_by_id(bot_id) > 0
    
    @select("""
        SELECT * FROM dodo_bots 
        WHERE (created_by = %s OR is_public = %s)
        ORDER BY created_at DESC
    """, Bot)
    def _get_user_bots_with_public(self, user_id: int, is_public: bool) -> List[Bot]:
        pass
    
    @select("""
        SELECT * FROM dodo_bots 
        WHERE created_by = %s
        ORDER BY created_at DESC
    """, Bot)
    def _get_user_bots_only(self, user_id: int) -> List[Bot]:
        pass
    
    def get_user_bots(self, user_id, include_public=True):
        """获取用户的机器人列表"""
        if include_public:
            bots = self._get_user_bots_with_public(user_id, True)
        else:
            bots = self._get_user_bots_only(user_id)
        
        # bots已经是dict列表（来自decorator返回）
        result = []
        for bot in bots:
            bot['kb_ids'] = []
            bot['kb_names'] = []
            result.append(bot)
        
        return result
    
    @select("SELECT * FROM dodo_bots WHERE is_public = true ORDER BY created_at DESC", Bot)
    def _get_public_bots_query(self) -> List[Bot]:
        pass
    
    def get_public_bots(self):
        """获取公开机器人列表"""
        bots = self._get_public_bots_query()
        # bots已经是dict列表（来自decorator返回）
        result = []
        for bot in bots:
            bot['kb_ids'] = []
            bot['kb_names'] = []
            result.append(bot)
        return result
    
    def get_bot_knowledge_bases(self, bot_id):
        """获取机器人关联的知识库ID列表"""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT kb_id FROM dodo_bot_knowledge_bases WHERE bot_id = %s", (bot_id,))
                return [row[0] for row in cursor.fetchall()]
    
    def get_available_bots(self, user_id):
        """获取用户可用的机器人列表（用户创建的和公开的）"""
        return self.get_user_bots(user_id, include_public=True)