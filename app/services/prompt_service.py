"""
提示词服务 - 统一管理所有提示词模板和拼接逻辑
"""
from common import log_


class PromptService:
    """提示词服务，负责构建和管理所有提示词"""
    
    # 角色模板定义
    ROLE_TEMPLATES = {
        "default": "你是一个专业的智能助手。",
        "writer": "你是一位经验丰富的作家，擅长创作各类文学作品，包括小说、散文、诗歌等。你的文笔优美，善于运用修辞手法，能够根据用户需求创作出高质量的文字内容。",
        "english_expert": "你是一位英语专业人员，精通英语语法、词汇和表达方式。你可以帮助用户进行英语翻译、写作指导、语法纠错等工作。你的回答准确、专业，能够提供详细的解释和例句。",
        "programmer": "你是一位资深程序员，精通多种编程语言和开发框架。你可以帮助用户解决编程问题、代码审查、架构设计等。你的回答清晰、准确，注重代码质量和最佳实践。",
        "teacher": "你是一位耐心的教师，擅长用通俗易懂的方式解释复杂的概念。你会根据学生的理解程度调整讲解方式，善于举例说明，帮助学生真正理解知识点。",
        "consultant": "你是一位专业的咨询顾问，擅长分析问题、提供解决方案。你会从多个角度思考问题，给出全面、可行的建议。",
        "translator": "你是一位专业的翻译人员，精通多国语言。你能够准确理解原文含义，并用地道的目标语言进行翻译，保持原文的风格和语气。"
    }
    
    @staticmethod
    def get_role_prompt(role_key=None, custom_prompt=None):
        """
        获取角色提示词
        
        Args:
            role_key: 角色标识（writer, english_expert等）
            custom_prompt: 自定义提示词（优先级最高）
            
        Returns:
            str: 角色提示词
        """
        if custom_prompt:
            return custom_prompt
        
        if role_key and role_key in PromptService.ROLE_TEMPLATES:
            return PromptService.ROLE_TEMPLATES[role_key]
        
        return PromptService.ROLE_TEMPLATES["default"]
    
    @staticmethod
    def build_history_context(history_messages, max_pairs=5):
        """
        构建历史对话上下文
        
        Args:
            history_messages: 历史消息列表
            max_pairs: 最多保留几轮对话
            
        Returns:
            str: 格式化的历史对话文本
        """
        if not history_messages:
            return ""
        
        history_pairs = []
        for i in range(0, len(history_messages) - 1, 2):
            if i + 1 < len(history_messages):
                user_msg = history_messages[i]['content']
                bot_msg = history_messages[i + 1]['content']
                history_pairs.append(f"用户: {user_msg}\n助手: {bot_msg}")
        
        # 只保留最近的几轮对话
        history_pairs = history_pairs[-max_pairs:]
        
        if history_pairs:
            return "对话历史:\n" + "\n\n".join(history_pairs) + "\n\n"
        
        return ""
    
    @staticmethod
    def build_knowledge_context(knowledge_results):
        """
        构建知识库上下文
        
        Args:
            knowledge_results: 知识库检索结果列表
            
        Returns:
            str: 格式化的知识库上下文
        """
        if not knowledge_results:
            return ""
        
        context_texts = [result["text"] for result in knowledge_results]
        context = "\n\n".join(context_texts)
        
        return f"参考信息:\n{context}\n\n"
    
    @staticmethod
    def build_file_context(file_contents):
        """
        构建文件附件上下文
        
        Args:
            file_contents: 文件内容列表 [{'filename': xx, 'content': xx}, ...]
            
        Returns:
            str: 格式化的文件内容
        """
        if not file_contents:
            return ""
        
        file_texts = []
        for file_info in file_contents:
            filename = file_info.get('filename', '未知文件')
            content = file_info.get('content', '')
            
            if content and content != "[图片文件]":
                file_texts.append(f"【文件：{filename}】\n{content}")
        
        if file_texts:
            return "附件内容:\n" + "\n\n".join(file_texts) + "\n\n"
        
        return ""
    
    @staticmethod
    def build_rag_prompt(
        role_prompt,
        history_context="",
        knowledge_context="",
        file_context="",
        question=""
    ):
        """
        构建RAG（检索增强生成）模式的完整提示词
        
        Args:
            role_prompt: 角色提示词
            history_context: 历史对话上下文
            knowledge_context: 知识库上下文
            file_context: 文件附件上下文
            question: 用户问题
            
        Returns:
            str: 完整的提示词
        """
        prompt = f"""{role_prompt}

{history_context}{knowledge_context}{file_context}用户问题: {question}

回答要求:
1. 如果参考信息中包含与问题相关的内容，请基于这些信息回答
2. 如果参考信息不足以回答问题，可以使用你自己的知识，但请明确指出
3. 如果问题完全超出了参考信息的范围，请礼貌告知无法基于现有知识回答
4. 回答应简洁明了，直接针对问题给出有用的信息

请基于以上要求回答:"""
        
        return prompt
    
    @staticmethod
    def build_direct_prompt(
        role_prompt,
        history_context="",
        file_context="",
        question=""
    ):
        """
        构建直接回答模式的提示词（无知识库）
        
        Args:
            role_prompt: 角色提示词
            history_context: 历史对话上下文
            file_context: 文件附件上下文
            question: 用户问题
            
        Returns:
            str: 完整的提示词
        """
        prompt = f"""{role_prompt}

{history_context}{file_context}用户问题: {question}

请回答:"""
        
        return prompt
    
    @staticmethod
    def add_custom_role(role_key, role_description):
        """
        添加自定义角色模板
        
        Args:
            role_key: 角色标识
            role_description: 角色描述
        """
        PromptService.ROLE_TEMPLATES[role_key] = role_description
        log_.info(f"添加自定义角色模板: {role_key}")
    
    @staticmethod
    def get_all_roles():
        """
        获取所有可用的角色列表
        
        Returns:
            dict: 角色字典
        """
        return PromptService.ROLE_TEMPLATES.copy()
