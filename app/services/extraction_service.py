from app.models.llm.ollama_model import OllamaModel
from common import log_
from common.document_extractor import extract_content  # 导入文档提取工具
from common.error_codes import FileError, OCRError, ErrorCode, APIException, ModelCallError  # 添加ModelCallError
from common.json_utils import fix_and_parse_json, dump_json
from config.base import EXTRACTION_MODE, COZE_API_TOKEN, COZE_WORKFLOW_ID, COZE_BOT_ID
import json
import re
import os
import requests
from cozepy import COZE_CN_BASE_URL, Coze, TokenAuth, Stream, WorkflowEventType

class ExtractionService:
    def __init__(self):
        self.ollama_model = OllamaModel()
        # 从配置文件读取提取模式
        self.extraction_mode = EXTRACTION_MODE
        
        # Coze 配置（从配置文件读取）
        self.coze_api_token = COZE_API_TOKEN
        self.workflow_id = COZE_WORKFLOW_ID
        self.bot_id = COZE_BOT_ID
        
        # 初始化Coze客户端（仅在需要时）
        if self.extraction_mode == 1:
            coze_api_base = COZE_CN_BASE_URL
            self.coze = Coze(auth=TokenAuth(token=self.coze_api_token), base_url=coze_api_base)
        else:
            self.coze = None

    def process_file(self, file_object, schema, file_type=None):
        """
        处理文件并提取结构化信息
        
        Args:
            file_object: 文件对象
            schema: JSON结构模板
            file_type: 文件类型(可选)
            
        Returns:
            dict: 提取的结构化信息
        """
        try:
            # 根据配置选择处理方式
            if self.extraction_mode == 1:
                # Coze模式：上传文件到Coze并调用工作流
                return self._process_with_coze(file_object, schema, file_type)
            else:
                # 本地Ollama模式：提取文件内容后调用本地模型
                return self._process_with_ollama(file_object, schema, file_type)
                
        except FileError as e:
            log_.error(f"文件处理失败: {str(e)}")
            raise ValueError(f"文件处理失败: {str(e)}")  # 提供更具体的错误信息
    
    def _process_with_ollama(self, file_object, schema, file_type=None):
        """使用本地Ollama模型处理文件"""
        try:
            # 确保文件对象有name属性，以便document_extractor能正确识别类型
            if hasattr(file_object, 'name') == False and file_type:
                # 如果文件对象没有name属性，但传入了file_type，则添加一个name属性
                file_path = getattr(file_object, 'name', None)
                if not file_path:
                    # 创建带有合适扩展名的临时文件名
                    extension = self._get_extension_for_type(file_type)
                    temp_name = f"temp_file{extension}"
                    # 给文件对象添加name属性
                    file_object.name = temp_name
            
            # 1. 从文件中提取文本内容，传入文件类型
            file_content = self.extract_file_content(file_object, file_type)
            
            # 2. 从文本内容中提取结构化信息
            result = self.extract_from_file(file_content, schema)
            
            # 检查结果是否包含错误信息
            if isinstance(result, str) and ('调用模型出错' in result or '<!DOCTYPE html>' in result):
                log_.error(f"模型调用失败: {result[:200]}...")
                raise APIException(ErrorCode.EXTRACT_ERROR, msg=f"模型调用失败: {result[:100]}...")
            
            # 3. 确保返回JSON对象
            try:
                result_json = json.loads(result) if isinstance(result, str) else result
                return result_json, 200
            except json.JSONDecodeError as e:
                log_.error(f"JSON解析失败: {str(e)}, 原始数据: {result[:200]}...")
                # 如果出现解析错误，返回空的schema结构
                empty_schema = json.loads(schema)
                for key in empty_schema:
                    if isinstance(empty_schema[key], str):
                        empty_schema[key] = ""
                    elif isinstance(empty_schema[key], (int, float)):
                        empty_schema[key] = 0
                    elif isinstance(empty_schema[key], list):
                        empty_schema[key] = []
                return empty_schema, 200
                
        except Exception as e:
            log_.error(f"本地Ollama处理失败: {str(e)}")
            raise APIException(ErrorCode.EXTRACT_ERROR, msg=f"本地Ollama处理失败: {str(e)}")
    
    def _process_with_coze(self, file_object, schema, file_type=None):
        """使用Coze工作流处理文件"""
        try:
            # 1. 上传文件到Coze
            file_id = self.upload_file_to_coze(file_object)
            
            # 2. 确定文件类型
            if not file_type:
                # 从文件名推断文件类型
                filename = getattr(file_object, 'name', 'unknown')
                if filename.endswith('.docx') or filename.endswith('.doc'):
                    file_type = 'doc'
                elif filename.endswith('.pdf'):
                    file_type = 'pdf'
                elif filename.endswith('.txt'):
                    file_type = 'txt'
                else:
                    file_type = 'txt'  # 默认类型
            
            # 3. 调用Coze工作流
            result = self.extract_with_coze(file_id, file_type, schema)
            
            # 3. 解析结果
            try:
                result_json = json.loads(result) if isinstance(result, str) else result
                return result_json, 200
            except json.JSONDecodeError as e:
                log_.error(f"Coze结果解析失败: {str(e)}, 原始数据: {result[:200]}...")
                # 如果出现解析错误，返回空的schema结构
                empty_schema = json.loads(schema)
                for key in empty_schema:
                    if isinstance(empty_schema[key], str):
                        empty_schema[key] = ""
                    elif isinstance(empty_schema[key], (int, float)):
                        empty_schema[key] = 0
                    elif isinstance(empty_schema[key], list):
                        empty_schema[key] = []
                return empty_schema, 200
                
        except Exception as e:
            log_.error(f"Coze处理失败: {str(e)}")
            raise APIException(ErrorCode.EXTRACT_ERROR, msg=f"Coze处理失败: {str(e)}")
    
    def extract_file_content(self, file_object, file_type=None):
        """
        从文件对象中提取文本内容，支持多种文件格式
        使用common.document_extractor工具类
        
        Args:
            file_object: 文件对象
            file_type: 文件类型，如果提供则强制使用此类型
            
        Returns:
            str: 提取的文本内容
        """
        try:
            # 使用document_extractor提取文本内容，传入文件类型
            content = extract_content(file_object, file_type)
            return content
        except (FileError, OCRError) as e:
            # 专门处理FileError和OCRError
            log_.error(f"文件内容提取失败: {str(e)}")
            raise ValueError(f"文件处理失败({e.__class__.__name__}): {str(e)}")
        except Exception as e:
            log_.error(f"文件内容提取失败: {str(e)}")
            raise ValueError(f"无法从文件中提取内容: {str(e)}")
            
    def upload_file_to_coze(self, file_object):
        """
        直接上传文件对象到Coze服务器并获取file_id
        """
        try:
            url = "https://api.coze.cn/v1/files/upload"
            headers = {
                'Authorization': f'Bearer {self.coze_api_token}'
            }
            
            # 确保文件指针在开头
            file_object.seek(0)
            
            # 获取文件名，如果存在的话
            filename = getattr(file_object, 'name', 'file.txt')
            if hasattr(file_object, 'filename'):
                filename = file_object.filename
                
            # 直接上传文件对象
            files = {"file": (os.path.basename(filename), file_object)}
            response = requests.post(url, headers=headers, files=files)
                
            if response.status_code != 200:
                log_.error(f"上传文件到Coze失败: {response.status_code}, {response.text}")
                raise APIException(ErrorCode.EXTRACT_ERROR, msg=f"上传文件到Coze失败: {response.status_code}")
                
            result = response.json()
            if 'data' not in result or 'id' not in result['data']:
                log_.error(f"Coze上传响应格式错误: {result}")
                raise APIException(ErrorCode.EXTRACT_ERROR, msg="Coze上传响应格式错误")
                
            file_id = result['data']['id']
            return file_id
        except Exception as e:
            log_.error(f"上传文件到Coze失败: {str(e)}")
            raise APIException(ErrorCode.EXTRACT_ERROR, msg=f"上传文件到Coze失败: {str(e)}")

    def extract_with_bot(self, file_id, schema):
        """
        调用豆包Coze智能体，传入file_id和schema，返回 JSON 字符串
        """
        try:
            # 构建消息内容
            message_content = f"""
请根据以下schema从上传的文件中提取信息：

Schema: {schema}

请严格按照JSON格式返回提取结果，确保字段名称与schema完全一致。
对于找不到的信息，字符串类型用空字符串""，数字类型用0，数组类型用[]。
"""
            
            # 构建请求参数
            data = {
                "bot_id": self.bot_id,
                "messages": [
                    {
                        "role": "user",
                        "content": message_content,
                        "attachments": [
                            {
                                "type": "file",
                                "file_id": file_id
                            }
                        ]
                    }
                ],
                "stream": False
            }
            
            # 调用豆包智能体API
            response = self.coze.bots.chat.create(**data)
            # 获取响应内容
            if hasattr(response, 'choices') and response.choices:
                message = response.choices[0].message
                if hasattr(message, 'content') and message.content:
                    result = message.content
                    return result
            
            log_.error("豆包智能体未返回有效结果")
            raise APIException(ErrorCode.EXTRACT_ERROR, msg="豆包智能体未返回有效结果")
                
        except Exception as e:
            log_.error(f"调用豆包智能体异常: {str(e)}")
            raise APIException(ErrorCode.EXTRACT_ERROR, msg=f"调用豆包智能体失败: {str(e)}")

    def extract_with_coze(self, file_id, file_type, schema):
        """
        调用 Coze 工作流，传入file_id、文件类型和schema，返回 JSON 字符串
        """
        try:
            # 构建参数 - 三个参数：file_id、type、schema
            parameters = {
                'uploadFile': f'{{\"file_id\": \"{file_id}\"}}',  # 文件ID参数
                'type': file_type,  # 文件类型（doc、pdf、txt等）
                'schema': schema   # 要提取的JSON字段结构
            }
            
            # 记录调用参数
            # 使用非流式API调用
            response = self.coze.workflows.runs.create(
                workflow_id=self.workflow_id,
                parameters=parameters
            )
            
            # 检查响应中是否包含data字段
            if hasattr(response, 'data') and response.data:
                return response.data
            else:
                # 尝试获取原始响应内容
                response_dict = response.__dict__
                log_.debug(f"响应完整内容: {response_dict}")
                
                # 尝试从可能的位置获取数据
                if 'data' in response_dict:
                    return response_dict['data']
                elif '_json_data' in response_dict and 'data' in response_dict['_json_data']:
                    return response_dict['_json_data']['data']
                
                log_.error("Coze智能体响应中未找到data字段")
                raise APIException(ErrorCode.EXTRACT_ERROR, msg="Coze智能体响应中未找到data字段")
                
        except Exception as e:
            log_.error(f"调用Coze工作流异常: {str(e)}")
            raise APIException(ErrorCode.EXTRACT_ERROR, msg=f"调用Coze工作流失败: {str(e)}")

    def extract_from_file(self, file_content, schema):
        """从文件内容中提取结构化信息，仅使用传入的文件内容"""
        try:
            # 构建提示词，添加具体示例
            prompt = f"""你是一个专业的信息提取AI助手。请严格按照以下要求提取信息：

1. 你的任务是从提供的文本中提取信息，并填充到指定的JSON模板中
2. 你必须严格按照JSON格式返回结果
3. 不要返回任何其他格式或额外的解释文本
4. 不要使用markdown格式或```符号
5. 对于找不到的信息：
   - 字符串类型用空字符串 ""
   - 数字类型用 0
   - 数组类型用 []

=== 示例 ===
示例文本内容：
张三是一名32岁的软件工程师，他的联系方式是：
电话：13812345678
邮箱：zhangsan@example.com
目前在阿里巴巴担任高级开发工程师，工作经验8年。

示例JSON模板：
{{
    "name": "",
    "age": 0,
    "email": "",
    "phone": "",
    "company": "",
    "experience": 0
}}

正确的返回格式：
{{
    "name": "张三",
    "age": 32,
    "email": "zhangsan@example.com",
    "phone": "13812345678",
    "company": "阿里巴巴",
    "experience": 8
}}

=== 现在请处理以下内容 ===
JSON模板:
{schema}

文本内容:
{file_content}

请直接返回填充后的JSON数据，确保：
1. 保持原始字段名称不变
2. 不添加任何注释或额外字段
3. 返回内容必须是合法的JSON格式
"""
            # 记录提示词（修改为DEBUG级别，减少INFO日志数量）
            log_.debug(f"======= 提取提示词 =======\n{prompt}")
            
            # 调用模型获取响应
            response = self.ollama_model.invoke(prompt)
            
            # 记录原始响应（修改为DEBUG级别）
            log_.debug(f"======= 模型原始响应 =======\n{response}")
            
            # 清理响应内容，确保是有效的JSON
            cleaned_response = re.sub(r'```json\s*|\s*```', '', response.strip())
            
            # 记录清理后的响应（修改为DEBUG级别）
            log_.debug(f"======= 清理后的响应 =======\n{cleaned_response}")
            
            try:
                # 尝试使用共通的JSON修复和解析方法
                result_json = fix_and_parse_json(cleaned_response)
                # 详细数据移至DEBUG级别
                log_.debug(f"解析JSON结果:\n{dump_json(result_json, ensure_ascii=False, indent=2)}")
                return dump_json(result_json)
            except ValueError as e:
                log_.error(f"JSON解析失败: {str(e)}")
                empty_schema = json.loads(schema)
                for key in empty_schema:
                    if isinstance(empty_schema[key], str):
                        empty_schema[key] = ""
                    elif isinstance(empty_schema[key], (int, float)):
                        empty_schema[key] = 0
                    elif isinstance(empty_schema[key], list):
                        empty_schema[key] = []
                return json.dumps(empty_schema)
            
        except ModelCallError as e:
            # 直接重新抛出模型调用错误，让上层处理
            log_.error(f"模型调用错误: {str(e)}")
            raise
        except Exception as e:
            log_.error(f"内容提取失败: {str(e)}")
            empty_schema = json.loads(schema)
            for key in empty_schema:
                if isinstance(empty_schema[key], str):
                    empty_schema[key] = ""
                elif isinstance(empty_schema[key], (int, float)):
                    empty_schema[key] = 0
                elif isinstance(empty_schema[key], list):
                    empty_schema[key] = []
            return json.dumps(empty_schema)
    
    def extract_from_text(self, text, schema):
        """从纯文本中提取结构化信息（对外API使用）"""
        return self.extract_from_file(text, schema)
    
    def _get_extension_for_type(self, file_type):
        """根据文件类型获取对应的扩展名"""
        type_to_extension = {
            'text': '.txt',
            'word': '.docx',
            'markdown': '.md',
            'pdf': '.pdf',
            'image': '.jpg'
        }
        return type_to_extension.get(file_type, '.unknown')