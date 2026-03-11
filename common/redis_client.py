import redis
from flask import current_app
from config.base import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD
from config.base import REDIS_KEY_PREFIX_VERIFICATION_CODE, REDIS_KEY_PREFIX_RATE_LIMIT

class RedisClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True
            )
        return cls._instance
    
    @property
    def redis(self):
        return self.client
    
    def get_verification_code_key(self, email):
        """获取验证码的Redis键"""
        return f"{REDIS_KEY_PREFIX_VERIFICATION_CODE}{email}"
    
    def get_rate_limit_key(self, email):
        """获取频率限制的Redis键"""
        return f"{REDIS_KEY_PREFIX_RATE_LIMIT}{email}"
    
    def set_verification_code(self, email, code):
        """设置验证码，5分钟过期"""
        key = self.get_verification_code_key(email)
        self.redis.setex(key, 300, code)
    
    def get_verification_code(self, email):
        """获取验证码"""
        key = self.get_verification_code_key(email)
        return self.redis.get(key)
    
    def delete_verification_code(self, email):
        """删除验证码"""
        key = self.get_verification_code_key(email)
        self.redis.delete(key)
    
    def set_rate_limit(self, email):
        """设置频率限制，1分钟"""
        key = self.get_rate_limit_key(email)
        self.redis.setex(key, 60, '1')
    
    def check_rate_limit(self, email):
        """检查频率限制"""
        key = self.get_rate_limit_key(email)
        return self.redis.exists(key)
