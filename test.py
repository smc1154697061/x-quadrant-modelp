import requests
import json
import os


class CozeFileWorkflow:
    def __init__(self, token):
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def run_file_workflow(self, workflow_id, file_url, question):
        """运行文件处理工作流（直接使用文件URL）"""
        url = 'https://api.coze.cn/v1/workflow/run'

        payload = {
            "workflow_id": workflow_id,
            "parameters": {
                "question": question,
                "image": json.dumps({"url": file_url})  # 直接使用文件URL
            }
        }

        response = requests.post(
            url,
            headers=self.headers,
            data=json.dumps(payload)
        )
        if response.status_code != 200:
            raise Exception(f"工作流调用失败: {response.text}")

        return response.json()


# ==================== 使用示例 ====================

# 1. 配置信息
API_TOKEN = "pat_6L4gDFLdRgAkUj4DvtOgc0EnHOxZLIZKaUeG6wA7uRlL8jB3DShUFzHjh4gQWUNF"
WORKFLOW_ID = "7529481489819090971"
FILE_URL = "http://115.190.130.68:9090/api/v1/download-shared-object/aHR0cDovLzEyNy4wLjAuMTo5MDAwL2RvY3VtZW50cy8lRTclQUUlODAlRTUlOEUlODYlRTQlQkYlQTElRTYlODElQUYudHh0P1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9M0xZUjBKRlBGQkpJTDRSQ0FPS0olMkYyMDI1MDgwMSUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNTA4MDFUMDg0MjU1WiZYLUFtei1FeHBpcmVzPTQzMjAwJlgtQW16LVNlY3VyaXR5LVRva2VuPWV5SmhiR2NpT2lKSVV6VXhNaUlzSW5SNWNDSTZJa3BYVkNKOS5leUpoWTJObGMzTkxaWGtpT2lJelRGbFNNRXBHVUVaQ1NrbE1ORkpEUVU5TFNpSXNJbVY0Y0NJNk1UYzFOREE0TURrek1pd2ljR0Z5Wlc1MElqb2liV2x1YVc5aFpHMXBiaUo5LkdsOGdGMHB6eU5PNFBrb3VmRUE2UTNBSjRRd3BmOHFYYWs0U0JLaDdBTUdrODhMWTFMNUFIUkpldG0wMnBiVUIyei1PV3JCa19yUnB1TlRwWDh0QXFnJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCZ2ZXJzaW9uSWQ9bnVsbCZYLUFtei1TaWduYXR1cmU9OTM3YmVlOTdiMzNjZmI0MmVlNTJhNGUzODNjOGQ2NTEzZDBkZDNlNTkyZjQ5OGI2ZjJlNzc3MTAzYjc5MjNlNg"
QUESTION = "请描述图中的内容"

# 初始化API客户端
coze_workflow = CozeFileWorkflow(API_TOKEN)

try:
    # 直接运行工作流（使用文件URL）
    print("🚀 运行工作流中...")
    result = coze_workflow.run_file_workflow(WORKFLOW_ID, FILE_URL, QUESTION)

    # 处理结果
    if result.get('status') == 'success':
        print("🎉 工作流执行成功!")
        print("📝 工作流输出:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("⚠️ 工作流执行异常:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

except Exception as e:
    print(f"❌ 处理失败: {str(e)}")