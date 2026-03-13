# 调试脚本目录

此目录包含用于开发和调试的临时脚本，**不应用于生产环境**。

## 文件说明

### Coze 工作流测试
- `test_coze_workflow.py` - 测试 Coze API 工作流调用
- `test_coze_file_workflow.py` - 测试 Coze 文件处理工作流

### 文档处理测试
- `test_chunking_strategies.py` - 测试三种文档分块策略
- `test_document_processing.py` - 测试知识库文档向量化处理

## 注意事项

1. 这些脚本可能包含硬编码的 API Token 和测试配置
2. 运行前请检查并更新相关配置
3. 不要在生产环境中使用这些脚本
