"""
基础数据访问对象 (BaseDAO) - 提供数据库连接和基本操作方法
"""
import psycopg2
import psycopg2.extras
from flask import g, current_app
from common import log_
from common.error_codes import APIException, ErrorCode
from common.db_utils import get_db_connection

class BaseDAO:
    """数据访问对象基类"""
    
    def __init__(self):
        """初始化，不再直接创建连接"""
        pass
    
    def cursor_to_dict(self, cursor):
        """将游标结果转换为字典"""
        try:
            columns = [col[0] for col in cursor.description]
            result = cursor.fetchone()
            if not result:
                return None
            return dict(zip(columns, result))
        except Exception as e:
            log_.error(f"转换游标结果为字典失败: {str(e)}")
            return None
    
    def cursor_to_dict_list(self, cursor):
        """将游标结果转换为字典列表"""
        try:
            columns = [col[0] for col in cursor.description]
            results = cursor.fetchall()
            return [dict(zip(columns, row)) for row in results]
        except Exception as e:
            log_.error(f"转换游标结果为字典列表失败: {str(e)}")
            return []
    
    def execute_query(self, sql, params=None):
        """执行查询语句并返回结果集"""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                    
                return self.cursor_to_dict_list(cursor)
    
    def execute_query_one(self, sql, params=None):
        """执行查询语句并返回单条结果"""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                    
                return self.cursor_to_dict(cursor)
    
    @classmethod
    def execute_update(cls, sql, params=None):
        """执行更新语句（INSERT, UPDATE, DELETE）"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    if params:
                        cursor.execute(sql, params)
                    else:
                        cursor.execute(sql)
                    
                    affected_rows = cursor.rowcount
                    return affected_rows
        except psycopg2.errors.UniqueViolation as e:
            # 唯一约束冲突
            log_.error(f"唯一约束冲突: {str(e)}")
            raise APIException(ErrorCode.VALIDATION_ERROR, msg="数据已存在，违反唯一约束")
        except Exception as e:
            log_.error(f"执行更新失败: {str(e)}")
            raise APIException(ErrorCode.DATABASE_ERROR, msg="数据库更新失败")
    
    @classmethod
    def execute_insert_returning(cls, sql, params=None):
        """执行INSERT语句并返回新插入行的ID"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    if params:
                        cursor.execute(sql, params)
                    else:
                        cursor.execute(sql)
                    
                    result = cursor.fetchone()
                    return result[0] if result else None
        except psycopg2.errors.UniqueViolation as e:
            # 唯一约束冲突
            log_.error(f"唯一约束冲突: {str(e)}")
            raise APIException(ErrorCode.VALIDATION_ERROR, msg="数据已存在，违反唯一约束")
        except Exception as e:
            log_.error(f"执行插入失败: {str(e)}")
            raise APIException(ErrorCode.DATABASE_ERROR, msg="数据库插入失败") 