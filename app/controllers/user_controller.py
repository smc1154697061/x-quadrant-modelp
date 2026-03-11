"""
用户控制器 - 处理用户相关的请求
"""
from flask import request, g
from .base import BaseResource
from app.core.decorators import api_exception_handler, login_required
from common import log_
from common.error_codes import APIException, ErrorCode, ParameterError, ResourceNotFound
from app.services.user_service import UserService
from app.entity.dto.user_dto import UserUpdateDTO

class UserResource(BaseResource):
    """用户资源控制器"""
    
    @api_exception_handler
    @login_required
    def get(self, user_id=None):
        """获取用户信息
        
        如果提供了user_id，则获取特定用户的信息
        否则获取当前用户的信息（从会话中）
        """
        try:
            if not user_id:
                # 这里应该从会话中获取当前用户ID
                # 在实际项目中，应该实现认证中间件来处理用户认证
                raise ParameterError(msg="缺少用户ID")
            
            # 通过ID获取用户
            user = UserService.get_user_by_id(user_id)
            if not user:
                raise ResourceNotFound(msg="用户不存在")
            
            # 返回用户信息，移除敏感字段
            response = {
                "code": ErrorCode.SUCCESS.code,
                "message": "获取用户信息成功",
                "data": {
                    "id": user["id"],
                    "email": user["email"],
                    "name": user["name"],
                    "phone": user.get("phone"),
                    "created_at": user.get("created_at")
                }
            }
            return response
        
        except APIException as e:
            return e.to_dict()
        
        except Exception as e:
            log_.exception(f"获取用户信息异常: {str(e)}")
            error = APIException(ErrorCode.SYSTEM_ERROR, msg="系统错误")
            return error.to_dict()
    
    @api_exception_handler
    @login_required
    def put(self, user_id=None):
        """更新用户信息（Java风格）"""
        # 1. 接收请求转为DTO
        data = self.get_params()
        dto = UserUpdateDTO.from_request(data)
        
        # 2. DTO校验
        dto.validate()
        
        # 3. 使用当前用户ID或指定的user_id
        target_user_id = user_id or g.user_id
        
        # 4. 调用Service
        updated_user = UserService.update_user_by_dto(target_user_id, dto)
        
        # 5. 返回VO（Service已返回VO格式）
        return {
            "code": ErrorCode.SUCCESS.code,
            "message": "更新用户信息成功",
            "data": updated_user
        }
    
    def delete(self, user_id=None):
        """删除用户"""
        try:
            if not user_id:
                raise ParameterError(msg="缺少用户ID")
            
            # 删除用户 - 使用UserService
            try:
                deleted = UserService.delete_user(user_id)
                
                return {
                    "code": ErrorCode.SUCCESS.code,
                    "message": "删除用户成功"
                }
            except ResourceNotFound as e:
                raise e
            except APIException as e:
                raise e
        
        except APIException as e:
            return e.to_dict()
        
        except Exception as e:
            log_.exception(f"删除用户异常: {str(e)}")
            error = APIException(ErrorCode.SYSTEM_ERROR, msg="系统错误")
            return error.to_dict()
    
    def post(self):
        """获取用户列表（分页）"""
        try:
            # 获取分页参数
            params = self.get_params()
            page = int(params.get('page', 1))
            page_size = int(params.get('page_size', 10))
            
            # 验证参数
            if page < 1:
                page = 1
                
            if page_size < 1 or page_size > 100:
                page_size = 10
                
            # 获取用户列表
            result = UserService.list_users(page, page_size)
            
            return {
                "code": ErrorCode.SUCCESS.code,
                "message": "获取用户列表成功",
                "data": result
            }
        
        except APIException as e:
            return e.to_dict()
        
        except Exception as e:
            log_.exception(f"获取用户列表异常: {str(e)}")
            error = APIException(ErrorCode.SYSTEM_ERROR, msg="系统错误")
            return error.to_dict() 