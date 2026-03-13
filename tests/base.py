# -*- coding: utf-8 -*-
"""
测试基类
"""
import os
import sys
import unittest
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class BaseTestCase(unittest.TestCase):
    """测试基类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        super().setUpClass()
        cls.project_root = PROJECT_ROOT
        cls.fixtures_dir = PROJECT_ROOT / 'tests' / 'fixtures'
    
    def setUp(self):
        """每个测试方法前执行"""
        super().setUp()
    
    def tearDown(self):
        """每个测试方法后执行"""
        super().tearDown()
    
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        super().tearDownClass()
    
    def get_fixture_path(self, filename):
        """获取测试数据文件路径"""
        return self.fixtures_dir / filename
    
    def load_fixture(self, filename, mode='r', encoding='utf-8'):
        """加载测试数据文件"""
        file_path = self.get_fixture_path(filename)
        with open(file_path, mode, encoding=encoding) as f:
            return f.read()


class BaseServiceTestCase(BaseTestCase):
    """服务层测试基类"""
    
    def setUp(self):
        super().setUp()
        # 可以在这里初始化服务相关的 mock


class BaseDAOTestCase(BaseTestCase):
    """DAO层测试基类"""
    
    def setUp(self):
        super().setUp()
        # 可以在这里初始化数据库连接


class BaseAPITestCase(BaseTestCase):
    """API测试基类"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # 创建 Flask 测试应用
        from app import create_app
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
    
    def setUp(self):
        super().setUp()
        # 设置请求上下文
        self.ctx = self.app.app_context()
        self.ctx.push()
    
    def tearDown(self):
        # 清理请求上下文
        self.ctx.pop()
        super().tearDown()
