"""
用户服务类 - 处理用户相关的业务逻辑
"""
from common import log_
from common.error_codes import APIException, ErrorCode, ParameterError, ResourceNotFound
from app.dao.user_dao import UserDAO
from app.entity.bo.user_bo import UserBO
from app.entity.dto.user_dto import UserUpdateDTO
import jwt
from datetime import datetime
from config.base import SECRET_KEY

class UserService:
    """用户服务类，处理用户相关的业务逻辑"""
    
    @classmethod
    def validate_token(cls, token):
        """验证JWT token并返回用户ID
        
        参数:
            token (str): JWT token
            
        返回:
            int: 用户ID，验证失败时返回None
        """
        try:
            # 解析JWT token，使用SECRET_KEY
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

            # 验证token是否过期
            exp = payload.get('exp')
            if exp and datetime.utcnow().timestamp() > exp:
                log_.warning(f"Token已过期: {token[:10]}...")
                return None
                
            # 获取用户ID
            user_id = payload.get('user_id')
            if not user_id:
                log_.warning(f"Token中缺少user_id: {payload}")
                return None
                
            # 验证用户是否存在
            user = cls.get_user_by_id(user_id)
            if not user:
                log_.warning(f"Token中的用户不存在: {user_id}")
                return None
                
            return user_id
        except jwt.DecodeError as e:
            log_.warning(f"Token解析失败: {token[:20]}..., 错误: {str(e)}")
            return None
        except Exception as e:
            log_.error(f"验证Token时发生错误: {str(e)}")
            return None
    
    @classmethod
    def get_user_by_email(cls, email):
        """通过邮箱获取用户信息"""
        user_dict = UserDAO().find_by_email(email)
        if not user_dict:
            return None
        
        # 转换为BO处理业务逻辑
        user_bo = UserBO.from_dict(user_dict)
        
        # 返回BO的dict
        return user_bo.to_dict()
    
    @classmethod
    def get_user_by_id(cls, user_id):
        """通过ID获取用户信息"""
        user_dict = UserDAO().find_by_id(user_id)
        if not user_dict:
            return None
        
        # 转换为BO处理业务逻辑
        user_bo = UserBO.from_dict(user_dict)
        
        # 返回BO的dict
        return user_bo.to_dict()
    
    @classmethod
    def create_user(cls, email, phone=None):
        """创建新用户，返回BO"""
        # 验证邮箱格式
        if not cls._validate_email(email):
            raise ParameterError(msg="邮箱格式不正确")
            
        # 验证手机号格式
        if phone and not cls._validate_phone(phone):
            raise ParameterError(msg="手机号格式不正确")
            
        # 检查邮箱是否已存在
        existing_user = UserDAO().find_by_email(email)
        if existing_user:
            raise APIException(ErrorCode.VALIDATION_ERROR, msg="邮箱已被注册")
            
        # 检查手机号是否已存在
        if phone:
            existing_phone = UserDAO().find_by_phone(phone)
            if existing_phone:
                raise APIException(ErrorCode.VALIDATION_ERROR, msg="手机号已被注册")
        
        # 创建用户实体对象
        from app.entity.user import User
        user = User(email=email, phone=phone)
        user_dict = UserDAO().create(user)
        
        # 转换为BO进行业务处理
        user_bo = UserBO.from_dict(user_dict)
        
        # 返回BO的dict
        return user_bo.to_dict()
    
    @classmethod
    def update_user(cls, user_id, data):
        """更新用户信息"""
        # 验证用户是否存在
        existing_user = UserDAO().find_by_id(user_id)

        if not existing_user:
            raise ResourceNotFound(msg="用户不存在")
            
        # 验证邮箱格式
        if 'email' in data and not cls._validate_email(data['email']):
            raise ParameterError(msg="邮箱格式不正确")
            
        # 验证手机号格式
        if 'phone' in data and not cls._validate_phone(data['phone']):
            raise ParameterError(msg="手机号格式不正确")
        
        # 构建用户实体对象进行更新
        from app.entity.user import User
        user = User(id=user_id)
        if 'email' in data:
            user.email = data['email']
        if 'phone' in data:
            user.phone = data['phone']
        
        # 更新用户信息
        updated = UserDAO().update(user)
        if not updated:
            raise APIException(ErrorCode.DATABASE_ERROR, msg="更新用户信息失败")
        
        # 获取并返回更新后的用户信息
        return cls.get_user_by_id(user_id)
    
    @classmethod
    def update_user_by_dto(cls, user_id: int, dto: UserUpdateDTO):
        """通过DTO更新用户信息（Java风格）
        
        参数:
            user_id: 用户ID
            dto: UserUpdateDTO对象
        
        返回:
            用户详情（dict）
        """
        # 1. 验证用户是否存在
        existing_user = UserDAO().find_by_id(user_id)
        if not existing_user:
            raise ResourceNotFound(msg="用户不存在")
        
        # 2. 构建User实体对象
        from app.entity.user import User
        user = User(id=user_id)
        if dto.email:
            user.email = dto.email
        if dto.phone:
            user.phone = dto.phone
        
        # 3. 调用DAO更新
        updated = UserDAO().update(user)
        if not updated:
            raise APIException(ErrorCode.DATABASE_ERROR, msg="更新用户信息失败")
        
        # 4. 返回更新后的VO
        return cls.get_user_by_id(user_id)
    
    @classmethod
    def delete_user(cls, user_id):
        """删除用户"""
        # 验证用户是否存在
        existing_user = UserDAO().find_by_id(user_id)
        if not existing_user:
            raise ResourceNotFound(msg="用户不存在")
            
        # 删除用户
        deleted = UserDAO().delete(user_id)
        if not deleted:
            raise APIException(ErrorCode.DATABASE_ERROR, msg="删除用户失败")
            
        return True
    
    @classmethod
    def list_users(cls, page=1, page_size=10):
        """获取用户列表（分页），返回ListVO"""
        offset = (page - 1) * page_size
        users = UserDAO().find_all(page_size, offset)
        
        # 转换为BO列表
        user_bos = []
        for user in users:
            user_dict = user.to_dict() if hasattr(user, 'to_dict') else user
            user_bo = UserBO.from_dict(user_dict)
            user_bos.append(user_bo.to_dict())
        
        # 获取总数
        total = UserDAO().count()
        
        # 直接返回分页数据
        return {
            'users': user_bos,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
    
    @staticmethod
    def _validate_email(email):
        """验证邮箱格式"""
        if not email:
            return False
            
        # 简单的邮箱格式验证
        return '@' in email and '.' in email.split('@')[-1]
    
    @staticmethod
    def _validate_phone(phone):
        """验证手机号格式"""
        if not phone:
            return False
            
        # 简单的手机号格式验证（这里假设手机号为纯数字且长度在5-20之间）
        return phone.isdigit() and 5 <= len(phone) <= 20 