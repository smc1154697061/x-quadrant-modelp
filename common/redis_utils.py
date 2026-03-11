"""
Redis工具类 - 处理Redis相关操作
"""
from common import log_

class RedisUtil:
    """Redis工具类，处理验证码存储"""
    
    @staticmethod
    def set_code(key, value, expire=300):
        """将验证码存入Redis，有效期为300秒（5分钟）"""
        try:
            from app import redis_client
            redis_key = f"email_code:{key}"
            redis_client.set(redis_key, value)
            redis_client.expire(redis_key, expire)
            return True
        except Exception as e:
            log_.error(f"Redis操作失败: {str(e)}")
            return False

    @staticmethod
    def get_code(key):
        """从Redis获取验证码"""
        try:
            from app import redis_client
            redis_key = f"email_code:{key}"
            code = redis_client.get(redis_key)
            return code.decode() if code else None
        except Exception as e:
            log_.error(f"Redis获取失败: {str(e)}")
            return None

    @staticmethod
    def delete_code(key):
        """删除Redis中的验证码"""
        try:
            from app import redis_client
            redis_key = f"email_code:{key}"
            redis_client.delete(redis_key)
            return True
        except Exception as e:
            log_.error(f"Redis删除失败: {str(e)}")
            return False 