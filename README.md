# x-quadrant-modelP

#### 项目简介
x-quadrant-modelP是一个结合大语言模型能力的智能文档处理系统，可以从各种文档中提取结构化信息、构建向量知识库并提供基于知识的问答服务。

#### 系统架构
- **前端**：Vue3 + Axios
- **后端**：Python Flask API
- **模型**：基于Ollama部署的本地大语言模型
- **存储**：MinIO对象存储 + 向量数据库

#### 主要功能
1. **文档管理**：上传、删除和查看文档
2. **信息提取**：从PDF、Word、图片等多种格式文档中自动提取结构化信息
3. **知识库构建**：将文档内容向量化并构建可检索的知识库
4. **智能问答**：基于知识库内容进行相关问题的回答

#### 安装使用

1. **环境要求**
   - Python 3.10
   - Node.js 16+
   - Ollama服务
   - MinIO服务（可选）

2. **后端安装**
   ```bash
   # 安装依赖
   pip install -r requirements.txt
   
   # 启动服务
   python app.py
   ```

3. **前端安装**
   ```bash
   cd vue3-ai
   npm install
   npm run dev
   ```

4. **配置说明**
   - 在`config/base.py`中配置模型、MinIO等相关参数

#### API接口
- `/llm/documents` - 获取文档列表
- `/llm/upload-document` - 上传文档
- `/api/v1/extract` - 提取文档信息
- `/llm/chat` - 知识库问答

#### 项目结构
- `app/` - 主应用代码
  - `controllers/` - 控制器层
  - `services/` - 服务层
  - `models/` - 模型层
- `apis/` - API接口定义
- `common/` - 公共工具类
- `config/` - 配置文件
- `vue3-ai/` - 前端代码

#### 开发团队
明日象限

#### 许可证
[添加您的许可证信息]
