"""
模板文档API测试脚本
"""
import requests
import json
import os

BASE_URL = "http://localhost:5000/api"

def test_template_apis():
    """测试模板相关API"""
    
    print("=" * 50)
    print("模板文档API测试")
    print("=" * 50)
    
    # 测试1: 获取模板列表（需要登录）
    print("\n1. 测试获取模板列表...")
    try:
        response = requests.get(f"{BASE_URL}/llm/templates")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text[:200]}...")
    except Exception as e:
        print(f"   错误: {str(e)}")
    
    # 测试2: 获取模板分类
    print("\n2. 测试获取模板分类...")
    try:
        response = requests.get(f"{BASE_URL}/llm/templates/categories")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text}")
    except Exception as e:
        print(f"   错误: {str(e)}")
    
    # 测试3: 获取生成历史
    print("\n3. 测试获取生成历史...")
    try:
        response = requests.get(f"{BASE_URL}/llm/documents/generated")
        print(f"   状态码: {response.status_code}")
        print(f"   响应: {response.text[:200]}...")
    except Exception as e:
        print(f"   错误: {str(e)}")
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)


def test_database_connection():
    """测试数据库连接"""
    print("\n" + "=" * 50)
    print("数据库连接测试")
    print("=" * 50)
    
    try:
        from common.db_utils import get_db_connection
        
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 检查表是否存在
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_name IN ('dodo_document_templates', 'dodo_generated_documents')
                """)
                tables = cursor.fetchall()
                print(f"\n存在的表: {[t[0] for t in tables]}")
                
                if len(tables) < 2:
                    print("\n⚠️ 数据库表不存在，请先执行SQL脚本:")
                    print("   psql -U your_user -d your_database -f scripts/template_tables.sql")
                else:
                    print("\n✅ 数据库表已创建")
                    
    except Exception as e:
        print(f"\n❌ 数据库连接失败: {str(e)}")


def test_minio_connection():
    """测试MinIO连接"""
    print("\n" + "=" * 50)
    print("MinIO连接测试")
    print("=" * 50)
    
    try:
        from common.minio_client import MinioClient
        
        client = MinioClient.get_instance()
        if client and client.client:
            print("\n✅ MinIO客户端初始化成功")
            
            # 尝试列出对象
            try:
                objects = client.list_objects()
                print(f"   存储桶中的对象数量: {len(objects)}")
            except Exception as e:
                print(f"   列出对象失败: {str(e)}")
        else:
            print("\n⚠️ MinIO客户端未初始化")
            
    except Exception as e:
        print(f"\n❌ MinIO连接失败: {str(e)}")


def test_ollama_connection():
    """测试Ollama连接"""
    print("\n" + "=" * 50)
    print("Ollama连接测试")
    print("=" * 50)
    
    try:
        from app.models.llm.ollama_model import OllamaModel
        
        model = OllamaModel()
        print("\n✅ Ollama模型初始化成功")
        
        # 尝试简单调用
        try:
            response = model.invoke("你好")
            print(f"   模型响应: {response[:50]}...")
        except Exception as e:
            print(f"   模型调用失败: {str(e)}")
            
    except Exception as e:
        print(f"\n❌ Ollama连接失败: {str(e)}")


if __name__ == "__main__":
    # 测试数据库连接
    test_database_connection()
    
    # 测试MinIO连接
    test_minio_connection()
    
    # 测试Ollama连接
    test_ollama_connection()
    
    # 测试API
    test_template_apis()
