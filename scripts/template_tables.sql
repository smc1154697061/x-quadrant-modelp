-- 文档模板表
CREATE TABLE IF NOT EXISTS dodo_document_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) DEFAULT '其他',
    minio_path VARCHAR(500),
    file_type VARCHAR(20),
    file_size BIGINT DEFAULT 0,
    created_by INTEGER NOT NULL,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 生成文档表
CREATE TABLE IF NOT EXISTS dodo_generated_documents (
    id SERIAL PRIMARY KEY,
    template_id INTEGER,
    template_name VARCHAR(255),
    user_input TEXT,
    generated_content TEXT,
    output_format VARCHAR(20) DEFAULT 'word',
    minio_path VARCHAR(500),
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 添加外键约束（如果模板表存在）
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'dodo_document_templates') THEN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints 
            WHERE constraint_name = 'fk_generated_doc_template' 
            AND table_name = 'dodo_generated_documents'
        ) THEN
            ALTER TABLE dodo_generated_documents 
            ADD CONSTRAINT fk_generated_doc_template 
            FOREIGN KEY (template_id) REFERENCES dodo_document_templates(id) ON DELETE SET NULL;
        END IF;
    END IF;
END $$;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_templates_created_by ON dodo_document_templates(created_by);
CREATE INDEX IF NOT EXISTS idx_templates_category ON dodo_document_templates(category);
CREATE INDEX IF NOT EXISTS idx_templates_is_public ON dodo_document_templates(is_public);
CREATE INDEX IF NOT EXISTS idx_generated_docs_created_by ON dodo_generated_documents(created_by);
CREATE INDEX IF NOT EXISTS idx_generated_docs_template_id ON dodo_generated_documents(template_id);

-- 添加注释
COMMENT ON TABLE dodo_document_templates IS '文档模板表';
COMMENT ON TABLE dodo_generated_documents IS '生成的文档记录表';
COMMENT ON COLUMN dodo_document_templates.name IS '模板名称';
COMMENT ON COLUMN dodo_document_templates.description IS '模板描述';
COMMENT ON COLUMN dodo_document_templates.category IS '模板分类：简历、论文、报告、合同、信函、其他';
COMMENT ON COLUMN dodo_document_templates.minio_path IS 'MinIO存储路径';
COMMENT ON COLUMN dodo_document_templates.file_type IS '文件类型：word、pdf、txt';
COMMENT ON COLUMN dodo_document_templates.is_public IS '是否公开';
COMMENT ON COLUMN dodo_generated_documents.template_name IS '模板名称（冗余存储）';
COMMENT ON COLUMN dodo_generated_documents.user_input IS '用户输入的信息';
COMMENT ON COLUMN dodo_generated_documents.generated_content IS 'AI生成的文档内容';
COMMENT ON COLUMN dodo_generated_documents.output_format IS '输出格式：word、pdf';
