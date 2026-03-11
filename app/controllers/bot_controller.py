"""
机器人控制器 - 处理机器人相关的HTTP请求（Java风格）
"""
from flask import request, g
from app.controllers.base import BaseResource
from app.core.decorators import api_exception_handler, login_required
from app.services.bot_service import BotService
from app.entity.dto.bot_dto import BotCreateDTO, BotUpdateDTO
from common import log_
from common.error_codes import APIException, ErrorCode


class BotController(BaseResource):
    """机器人控制器 - 符合Java面向对象思想"""
    
    @api_exception_handler
    @login_required
    def post(self):
        """创建机器人（POST /api/bots）
        
        请求体:
        {
            "name": "机器人名称",
            "description": "描述",
            "system_prompt": "系统提示词",
            "model_name": "qwen2:7b",
            "is_public": false,
            "kb_ids": [1, 2, 3]
        }
        
        返回:
        {
            "code": "SUCCESS",
            "message": "机器人创建成功",
            "data": { ... BotDetailVO ... }
        }
        """
        # 1. 接收请求，转为DTO（面向对象）
        data = self.get_params()
        dto = BotCreateDTO.from_request(data)
        
        # 2. DTO自己校验（不在Controller里校验！）
        dto.validate()
        
        # 3. 获取当前用户ID
        user_id = g.user_id
        
        # 4. 调用Service（不是直接调DAO！）
        bot_vo = BotService.create_bot(dto, user_id=user_id)
        
        # 5. 返回VO
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "机器人创建成功",
            "data": bot_vo
        }
    
    @api_exception_handler
    @login_required
    def get(self, bot_id=None):
        """获取机器人信息
        
        GET /api/bots/:bot_id - 获取单个机器人
        GET /api/bots - 获取机器人列表
        """
        if bot_id:
            # 获取单个机器人
            user_id = getattr(g, 'user_id', None)
            bot_vo = BotService.get_bot(bot_id, user_id=user_id)
            
            return {
                "code": ErrorCode.SUCCESS.code,
                "message": "获取机器人成功",
                "data": bot_vo
            }
        else:
            # 获取机器人列表
            user_id = g.user_id
            params = request.args
            list_type = params.get('type', 'user')  # user, public
            
            if list_type == 'public':
                # 获取公开机器人列表
                bots = BotService.list_public_bots()
            else:
                # 获取用户的机器人列表
                include_public = params.get('include_public', 'true').lower() == 'true'
                bots = BotService.list_user_bots(user_id, include_public=include_public)
            
            # 简单返回，前端取data.bots
            return {
                "code": ErrorCode.SUCCESS.code,
                "message": "获取机器人列表成功",
                "data": {
                    "bots": bots  # 前端期待这个结构
                }
            }
    
    @api_exception_handler
    @login_required
    def put(self, bot_id):
        """更新机器人信息（PUT /api/bots/:bot_id）
        
        请求体:
        {
            "name": "新名称",
            "description": "新描述",
            ...
        }
        """
        # 1. 接收请求，转为DTO
        data = self.get_params()
        dto = BotUpdateDTO.from_request(data)
        
        # 2. DTO自己校验
        dto.validate()
        
        # 3. 获取当前用户ID
        user_id = g.user_id
        
        # 4. 调用Service更新
        bot_vo = BotService.update_bot(bot_id, dto, user_id=user_id)
        
        # 5. 返回VO
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "更新机器人成功",
            "data": bot_vo
        }
    
    @api_exception_handler
    @login_required
    def delete(self, bot_id):
        """删除机器人（DELETE /api/bots/:bot_id）"""
        # 1. 获取当前用户ID
        user_id = g.user_id
        
        # 2. 调用Service删除
        BotService.delete_bot(bot_id, user_id=user_id)
        
        # 3. 返回成功
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "删除机器人成功"
        }