"""
测试 Coze 工作流调用流程
使用直接API调用方式，避免第三方库兼容性问题
"""

import os
import json
import requests
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Coze 配置
COZE_API_TOKEN = "pat_lDRZGkLAJPZhFzykojNac6KHSGR943diur5jzdnHspdexz2nFQDMhWGvGxkWyTEo"
WORKFLOW_ID = "7529481489819090971"


def upload_file_to_coze(file_path):
    """上传文件到 Coze 并获取 file_id"""
    try:
        url = "https://api.coze.cn/v1/files/upload"
        headers = {
            'Authorization': f'Bearer {COZE_API_TOKEN}'
        }

        # 读取文件
        with open(file_path, 'rb') as f:
            files = {"file": (os.path.basename(file_path), f)}
            response = requests.post(url, headers=headers, files=files)

        if response.status_code != 200:
            print(f"上传文件失败: {response.status_code}, {response.text}")
            return None

        result = response.json()
        if result.get('code') != 0:
            print(f"上传文件失败: {result}")
            return None

        file_id = result['data']['id']
        print(f"✅ 文件上传成功，file_id: {file_id}")
        return file_id

    except Exception as e:
        print(f"❌ 上传文件异常: {str(e)}")
        return None


def execute_workflow(file_path, schema):
    """执行工作流 - 使用直接API调用"""
    try:
        # 1. 上传文件
        file_id = upload_file_to_coze(file_path)
        if not file_id:
            return None

        # 2. 构建工作流请求
        url = "https://api.coze.cn/v1/workflow/run"
        headers = {
            'Authorization': f'Bearer {COZE_API_TOKEN}',
            'Content-Type': 'application/json'
        }

        # 正确的参数格式 - 三个参数
        payload = {
            "workflow_id": WORKFLOW_ID,
            "parameters": {
                "uploadFile": {"file_id": file_id},  # 文件ID参数
                "type": schema,  # 文件类型（doc、pdf、txt等）
                "schema": '{"name": "", "age": 0, "email": "", "phone": ""}'  # 要提取的JSON字段结构
            }
        }

        print("🔄 调用工作流中...")
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()

        print(f"📊 API响应状态码: {response.status_code}")

        if result.get('code') == 0:
            print("✅ 工作流调用成功！")

            # 解析返回的data字段（它本身是一个JSON字符串）
            if 'data' in result and result['data']:
                try:
                    # data字段是字符串，需要再次解析为JSON
                    data_obj = json.loads(result['data'])
                    output = data_obj.get('output', '')

                    print(f"📄 输出内容: '{output}'")
                    print(f"📏 输出长度: {len(output)}")

                    # 返回完整结果和调试链接
                    return {
                        'success': True,
                        'output': output,
                        'debug_url': result.get('debug_url', ''),
                        'full_response': result
                    }
                except json.JSONDecodeError:
                    print("❌ 解析工作流返回数据失败")
                    return {
                        'success': False,
                        'error': '数据解析失败',
                        'debug_url': result.get('debug_url', ''),
                        'raw_data': result['data']
                    }
            else:
                print("⚠️ 工作流返回数据为空")
                return {
                    'success': True,  # API调用成功，但内容为空
                    'output': '',
                    'debug_url': result.get('debug_url', ''),
                    'full_response': result
                }
        else:
            error_msg = result.get('msg', '未知错误')
            print(f"❌ 工作流调用失败: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'debug_url': result.get('debug_url', ''),
                'full_response': result
            }

    except Exception as e:
        print(f"❌ 工作流调用异常: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


def main():
    """主函数"""
    # 测试文件路径
    test_file = "C:\\Users\\Administrator\\Desktop\\test\\个人信息.docx"
    file_type = "docx"

    print("🚀 开始测试 Coze 工作流调用...")
    print(f"📁 测试文件: {test_file}")
    print(f"📝 文件类型: {file_type}")
    print("-" * 50)

    # 执行工作流
    result = execute_workflow(test_file, file_type)

    print("\n" + "=" * 50)
    if result['success']:
        print("✅ 工作流调用成功！")

        # 显示调试链接（非常重要）
        if result.get('debug_url'):
            print(f"🔗 调试链接: {result['debug_url']}")
            print("💡 请访问此链接查看工作流详细执行情况")

        # 检查输出内容
        output = result.get('output', '')
        if output and output.strip():
            print(f"📋 提取到的内容: {output}")
        else:
            print("⚠️ 工作流返回空内容")
            print("可能原因:")
            print("1. 工作流内部处理逻辑问题")
            print("2. 文件内容为空或格式不支持")
            print("3. 工作流输出节点配置问题")
            print("💡 请访问上面的调试链接排查具体原因")
    else:
        print("❌ 工作流调用失败！")
        if 'error' in result:
            print(f"错误信息: {result['error']}")
        print("请检查以下方面:")
        print("1. API Token 权限和有效期")
        print("2. 工作流是否已发布")
        print("3. 网络连接是否正常")


if __name__ == "__main__":
    main()