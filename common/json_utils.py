"""
JSON工具模块，提供JSON解析和修复功能。
支持处理格式不规范的JSON字符串，如：
1. 尾随逗号
2. 缺少引号的键
3. 单引号替代双引号
4. 其他常见JSON错误
"""
import json
import re
import logging

# 尝试导入json5库（需要先安装：pip install json5）
try:
    import json5
    HAS_JSON5 = True
except ImportError:
    HAS_JSON5 = False

# 尝试导入hjson库（需要先安装：pip install hjson）
try:
    import hjson
    HAS_HJSON = True
except ImportError:
    HAS_HJSON = False

# 从日志模块导入
from common import log_

def fix_and_parse_json(json_str):
    """
    修复并解析JSON字符串，返回解析后的Python对象
    
    Args:
        json_str: 要解析的JSON字符串
        
    Returns:
        dict/list: 解析后的Python对象
        
    Raises:
        ValueError: 如果所有解析方法都失败，抛出此异常
    """
    # 1. 先尝试标准json解析
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        log_.warning(f"标准JSON解析失败: {str(e)}")
    
    # 2. 尝试使用json5库（如果可用）
    if HAS_JSON5:
        try:
            return json5.loads(json_str)
        except Exception as e:
            log_.warning(f"JSON5解析失败: {str(e)}")
    
    # 3. 尝试使用hjson库（如果可用）
    if HAS_HJSON:
        try:
            return hjson.loads(json_str)
        except Exception as e:
            log_.warning(f"Hjson解析失败: {str(e)}")
    
    # 4. 使用正则表达式修复常见问题
    try:
        # 修复尾随逗号
        fixed_json = re.sub(r',\s*}', '}', json_str)
        fixed_json = re.sub(r',\s*]', ']', fixed_json)
        
        # 修复没有引号的键
        fixed_json = re.sub(r'(\s*?{\s*?|\s*?,\s*?)([a-zA-Z0-9_]+)(\s*?):', r'\1"\2"\3:', fixed_json)
        
        # 修复单引号
        fixed_json = re.sub(r"'([^']*)'", r'"\1"', fixed_json)
        
        return json.loads(fixed_json)
    except Exception as e:
        log_.error(f"正则表达式修复失败: {str(e)}")
    
    # 5. 所有方法都失败，抛出异常
    raise ValueError(f"无法解析JSON字符串: {json_str[:100]}...")

def dump_json(obj, ensure_ascii=False, indent=None):
    """
    将Python对象转换为JSON字符串
    
    Args:
        obj: 要转换的Python对象
        ensure_ascii: 是否确保ASCII编码（默认False，保留中文）
        indent: 缩进空格数（默认None，不格式化）
        
    Returns:
        str: JSON字符串
    """
    return json.dumps(obj, ensure_ascii=ensure_ascii, indent=indent)
