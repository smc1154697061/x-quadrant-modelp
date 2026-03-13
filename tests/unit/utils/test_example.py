# -*- coding: utf-8 -*-
"""
工具类单元测试示例
"""
import pytest
from tests.base import BaseTestCase


class TestExample(BaseTestCase):
    """测试示例"""
    
    def test_example_pass(self):
        """测试示例 - 通过"""
        assert True
    
    def test_example_math(self):
        """测试数学运算"""
        assert 1 + 1 == 2
        assert 2 * 3 == 6


class TestWithPytest:
    """使用 pytest 风格的测试"""
    
    def test_string_operations(self):
        """测试字符串操作"""
        text = "Hello, World!"
        assert text.startswith("Hello")
        assert "World" in text
        assert len(text) == 13
    
    def test_list_operations(self):
        """测试列表操作"""
        items = [1, 2, 3]
        assert len(items) == 3
        assert 2 in items
        items.append(4)
        assert len(items) == 4
