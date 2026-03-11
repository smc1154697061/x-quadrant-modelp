import functools
from typing import Type, Optional
from common import log_
from common.db_utils import get_db_connection


def _execute_query(sql: str, params=None, fetch_one=False, entity_class=None):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                # 始终传递params，即使是空tuple
                cursor.execute(sql, params if params else ())
                
                if fetch_one:
                    columns = [col[0] for col in cursor.description]
                    result = cursor.fetchone()
                    if not result:
                        return None
                    data = dict(zip(columns, result))
                    if entity_class:
                        # 返回实体对象转换为dict，而不是返回实体对象本身
                        entity = entity_class.from_dict(data)
                        return entity.to_dict()
                    return data
                else:
                    columns = [col[0] for col in cursor.description]
                    results = cursor.fetchall()
                    data_list = [dict(zip(columns, row)) for row in results]
                    if entity_class:
                        # 返回dict列表，而不是实体对象列表
                        entities = entity_class.from_dict_list(data_list)
                        return [entity.to_dict() for entity in entities]
                    return data_list
            except Exception as e:
                log_.error(f"执行查询SQL失败: {sql}, 参数: {params}, 错误: {str(e)}")
                raise


def _execute_update(sql: str, params=None, returning=False):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            try:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                if returning:
                    result = cursor.fetchone()
                    return result[0] if result else None
                else:
                    return cursor.rowcount
            except Exception as e:
                log_.error(f"执行更新SQL失败: {sql}, 参数: {params}, 错误: {str(e)}")
                raise


def select(sql: str, entity_class: Optional[Type] = None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # 将参数转为tuple
            params = args if args else ()
            return _execute_query(sql, params, fetch_one=False, entity_class=entity_class)
        return wrapper
    return decorator


def select_one(sql: str, entity_class: Optional[Type] = None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # 将参数转为tuple，即使只有一个参数也要保持tuple格式
            params = args if args else ()
            return _execute_query(sql, params, fetch_one=True, entity_class=entity_class)
        return wrapper
    return decorator


def insert(sql: str, returning_id=True):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            params = args if args else None
            return _execute_update(sql, params, returning=returning_id)
        return wrapper
    return decorator


def update(sql: str):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            params = args if args else None
            return _execute_update(sql, params, returning=False)
        return wrapper
    return decorator


def delete(sql: str):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            params = args if args else None
            return _execute_update(sql, params, returning=False)
        return wrapper
    return decorator
