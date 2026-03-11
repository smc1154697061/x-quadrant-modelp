"""
机器人服务类 - 处理机器人相关的业务逻辑
"""
from typing import List, Optional
from common import log_
from common.error_codes import APIException, ErrorCode, ParameterError, ResourceNotFound
from app.dao.bot_dao import BotDAO
from app.entity.bot import Bot
from app.entity.bo.bot_bo import BotBO
from app.entity.dto.bot_dto import BotCreateDTO, BotUpdateDTO


class BotService:
    """机器人服务类，处理机器人相关的业务逻辑"""
    
    @classmethod
    def create_bot(cls, dto: BotCreateDTO, user_id: int):
        """创建机器人（面向对象风格）
        
        参数:
            dto: BotCreateDTO请求对象
            user_id: 当前用户ID
        
        返回:
            机器人详情（dict）
        """
        # 1. 校验DTO（DTO自己校验）
        dto.validate()
        
        # 2. DTO转换为Bot实体
        bot = Bot(
            name=dto.name,
            description=dto.description,
            system_prompt=dto.system_prompt,
            model_name=dto.model_name or 'qwen2:7b',
            created_by=user_id,
            is_public=dto.is_public
        )
        
        # 3. 调用DAO创建
        bot_dict = BotDAO().create_bot(bot, kb_ids=dto.kb_ids)
        
        # 4. 转为BO处理业务逻辑
        bot_bo = BotBO.from_dict(bot_dict)
        
        # 5. 返回BO的dict
        return bot_bo.to_dict()
    
    @classmethod
    def get_bot(cls, bot_id: int, user_id: Optional[int] = None):
        """获取机器人详情
        
        参数:
            bot_id: 机器人ID
            user_id: 当前用户ID（用于权限检查）
        
        返回:
            机器人详情（dict）
        """
        bot_dict = BotDAO().get_bot(bot_id)
        if not bot_dict:
            raise ResourceNotFound(msg="机器人不存在")
        
        # 转为BO处理业务逻辑
        bot_bo = BotBO.from_dict(bot_dict)
        
        # 检查访问权限
        if user_id and not bot_bo.can_access_by_user(user_id):
            raise APIException(ErrorCode.PERMISSION_DENIED, msg="无权访问此机器人")
        
        # 返回BO的dict
        return bot_bo.to_dict()
    
    @classmethod
    def update_bot(cls, bot_id: int, dto: BotUpdateDTO, user_id: int):
        """更新机器人信息
        
        参数:
            bot_id: 机器人ID
            dto: BotUpdateDTO请求对象
            user_id: 当前用户ID
        
        返回:
            机器人详情（dict）
        """
        # 1. 校验DTO
        dto.validate()
        
        # 2. 验证机器人是否存在
        existing_bot = BotDAO().get_bot(bot_id)
        if not existing_bot:
            raise ResourceNotFound(msg="机器人不存在")
        
        # 3. 检查权限（只有创建者可以修改）
        if existing_bot['created_by'] != user_id:
            raise APIException(ErrorCode.PERMISSION_DENIED, msg="无权修改此机器人")
        
        # 4. 构建更新的Bot实体
        bot = Bot(id=bot_id)
        if dto.name:
            bot.name = dto.name
        if dto.description is not None:
            bot.description = dto.description
        if dto.system_prompt is not None:
            bot.system_prompt = dto.system_prompt
        if dto.model_name:
            bot.model_name = dto.model_name
        if dto.is_public is not None:
            bot.is_public = dto.is_public
        
        # 5. 调用DAO更新
        bot_dict = BotDAO().update_bot(bot, kb_ids=dto.kb_ids)
        
        # 6. 转为BO
        bot_bo = BotBO.from_dict(bot_dict)
        
        # 7. 返回BO的dict
        return bot_bo.to_dict()
    
    @classmethod
    def delete_bot(cls, bot_id: int, user_id: int):
        """删除机器人
        
        参数:
            bot_id: 机器人ID
            user_id: 当前用户ID
        
        返回:
            是否删除成功
        """
        # 1. 验证机器人是否存在
        existing_bot = BotDAO().get_bot(bot_id)
        if not existing_bot:
            raise ResourceNotFound(msg="机器人不存在")
        
        # 2. 检查权限（只有创建者可以删除）
        if existing_bot['created_by'] != user_id:
            raise APIException(ErrorCode.PERMISSION_DENIED, msg="无权删除此机器人")
        
        # 3. 删除机器人
        deleted = BotDAO().delete_bot(bot_id)
        if not deleted:
            raise APIException(ErrorCode.DATABASE_ERROR, msg="删除机器人失败")
        
        return True
    
    @classmethod
    def list_user_bots(cls, user_id: int, include_public: bool = True):
        """获取用户的机器人列表
        
        参数:
            user_id: 用户ID
            include_public: 是否包含公开机器人
        
        返回:
            机器人列表（简单dict数组）
        """
        bots_dict = BotDAO().get_user_bots(user_id, include_public=include_public)
        
        # 简单返回，不用复杂的VO封装
        return bots_dict
    
    @classmethod
    def list_public_bots(cls):
        """获取公开机器人列表
        
        返回:
            机器人列表（简单dict数组）
        """
        bots_dict = BotDAO().get_public_bots()
        
        # 简单返回，不用复杂的VO封装
        return bots_dict
