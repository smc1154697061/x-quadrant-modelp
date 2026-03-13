# -*- coding: utf-8 -*-
"""
Pytest 配置文件
"""
import os
import sys
import pytest

# 添加项目根目录到 Python 路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture(scope="session")
def app():
    """创建 Flask 应用实例"""
    from app import create_app
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app


@pytest.fixture(scope="function")
def client(app):
    """创建测试客户端"""
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture(scope="function")
def db(app):
    """创建数据库会话"""
    from app import db
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()


@pytest.fixture(scope="function")
def mock_logger():
    """Mock 日志记录器"""
    class MockLogger:
        def debug(self, msg, *args, **kwargs):
            pass
        
        def info(self, msg, *args, **kwargs):
            pass
        
        def warning(self, msg, *args, **kwargs):
            pass
        
        def error(self, msg, *args, **kwargs):
            pass
        
        def exception(self, msg, *args, **kwargs):
            pass
    
    return MockLogger()
