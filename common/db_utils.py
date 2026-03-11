"""
数据库连接配置 - 使用 psycopg2 连接池（原生 SQL）
"""
from contextlib import contextmanager
from flask import g
import psycopg2
from psycopg2 import pool

from config.base import (
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME,
    DB_POOL_MIN_CONN, DB_POOL_MAX_CONN, DB_CONNECT_TIMEOUT,
    DB_KEEPALIVE_IDLE, DB_KEEPALIVE_INTERVAL, DB_KEEPALIVE_COUNT,
    DB_APPLICATION_NAME
)
from common import log_

# psycopg2 连接池（全局单例）
_db_pool = None

def get_db_pool():
    """获取或创建数据库连接池（单例模式）"""
    global _db_pool
    if _db_pool is None:
        try:
            _db_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=DB_POOL_MIN_CONN,
                maxconn=DB_POOL_MAX_CONN,
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                connect_timeout=DB_CONNECT_TIMEOUT,
                application_name=DB_APPLICATION_NAME,
                keepalives=1,
                keepalives_idle=DB_KEEPALIVE_IDLE,
                keepalives_interval=DB_KEEPALIVE_INTERVAL,
                keepalives_count=DB_KEEPALIVE_COUNT
            )
            log_.info(f"数据库连接池初始化成功 [minconn={DB_POOL_MIN_CONN}, maxconn={DB_POOL_MAX_CONN}]")
        except Exception as e:
            log_.error(f"数据库连接池初始化失败: {str(e)}")
            raise
    return _db_pool

@contextmanager
def get_db_connection():
    """从连接池获取连接的上下文管理器（推荐使用）
    
    使用示例:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM table")
                results = cursor.fetchall()
    """
    pool_obj = get_db_pool()
    conn = None
    try:
        conn = pool_obj.getconn()
        yield conn
        conn.commit()  # 自动提交
    except Exception as e:
        if conn:
            conn.rollback()  # 回滚
        log_.error(f"数据库操作失败: {str(e)}")
        raise
    finally:
        if conn:
            pool_obj.putconn(conn)  # 归还连接

def check_db_health():
    """检查数据库连接健康状态"""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
    except Exception as e:
        log_.error(f"数据库健康检查失败: {str(e)}")
        return False

def get_pool_status():
    """获取连接池状态（用于监控）
    
    返回:
        dict: 包含连接池状态信息
    """
    try:
        pool_obj = get_db_pool()
        # psycopg2 连接池没有直接的状态查询方法
        # 这里返回配置信息
        return {
            "minconn": DB_POOL_MIN_CONN,
            "maxconn": DB_POOL_MAX_CONN,
            "application_name": DB_APPLICATION_NAME,
            "status": "healthy" if check_db_health() else "unhealthy"
        }
    except Exception as e:
        log_.error(f"获取连接池状态失败: {str(e)}")
        return {"status": "error", "message": str(e)}