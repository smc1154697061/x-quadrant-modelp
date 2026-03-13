-- ====================================================================
-- 🦤 渡渡鸟项目完整数据库建表脚本
-- 使用方式：直接执行即可，会自动删除旧表并创建新表
-- ====================================================================

-- 启用pgvector扩展
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;

-- ====================================================================
-- 删除旧表（按依赖顺序）
-- ====================================================================
DROP TABLE IF EXISTS "public"."dodo_message_documents" CASCADE;
DROP TABLE IF EXISTS "public"."dodo_messages" CASCADE;
DROP TABLE IF EXISTS "public"."dodo_conversations" CASCADE;
DROP TABLE IF EXISTS "public"."dodo_document_chunks" CASCADE;
DROP TABLE IF EXISTS "public"."dodo_kb_documents" CASCADE;
DROP TABLE IF EXISTS "public"."dodo_documents" CASCADE;
DROP TABLE IF EXISTS "public"."dodo_bot_knowledge_bases" CASCADE;
DROP TABLE IF EXISTS "public"."dodo_bots" CASCADE;
DROP TABLE IF EXISTS "public"."dodo_knowledge_bases" CASCADE;
DROP TABLE IF EXISTS "public"."dodo_users" CASCADE;

-- 删除序列
DROP SEQUENCE IF EXISTS "public"."dodo_users_id_seq" CASCADE;
DROP SEQUENCE IF EXISTS "public"."dodo_bots_id_seq" CASCADE;
DROP SEQUENCE IF EXISTS "public"."dodo_knowledge_bases_id_seq" CASCADE;
DROP SEQUENCE IF EXISTS "public"."dodo_documents_id_seq" CASCADE;
DROP SEQUENCE IF EXISTS "public"."dodo_document_chunks_id_seq" CASCADE;
DROP SEQUENCE IF EXISTS "public"."dodo_conversations_id_seq" CASCADE;
DROP SEQUENCE IF EXISTS "public"."dodo_messages_id_seq" CASCADE;
DROP SEQUENCE IF EXISTS "public"."dodo_message_documents_id_seq" CASCADE;
DROP SEQUENCE IF EXISTS "public"."dodo_organizations_id_seq" CASCADE;
DROP SEQUENCE IF EXISTS "public"."dodo_organization_members_id_seq" CASCADE;

-- ====================================================================
-- 创建序列
-- ====================================================================
CREATE SEQUENCE "public"."dodo_users_id_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;
CREATE SEQUENCE "public"."dodo_bots_id_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;
CREATE SEQUENCE "public"."dodo_knowledge_bases_id_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;
CREATE SEQUENCE "public"."dodo_documents_id_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;
CREATE SEQUENCE "public"."dodo_document_chunks_id_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;
CREATE SEQUENCE "public"."dodo_conversations_id_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;
CREATE SEQUENCE "public"."dodo_messages_id_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;
CREATE SEQUENCE "public"."dodo_message_documents_id_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;
CREATE SEQUENCE "public"."dodo_organizations_id_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;
CREATE SEQUENCE "public"."dodo_organization_members_id_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;

-- ====================================================================
-- 创建表
-- ====================================================================

-- 用户表
CREATE TABLE "public"."dodo_users" (
    "id" int4 NOT NULL DEFAULT nextval('dodo_users_id_seq'::regclass),
    "email" varchar(200) NOT NULL,
    "name" varchar(100),
    "phone" varchar(20),
    "created_at" timestamptz(6) DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);
CREATE UNIQUE INDEX "idx_dodo_users_email" ON "public"."dodo_users" ("email");
CREATE UNIQUE INDEX "idx_dodo_users_phone" ON "public"."dodo_users" ("phone");
COMMENT ON COLUMN "public"."dodo_users"."email" IS '邮箱';

-- 机器人表
CREATE TABLE "public"."dodo_bots" (
    "id" int4 NOT NULL DEFAULT nextval('dodo_bots_id_seq'::regclass),
    "name" varchar(100) NOT NULL,
    "description" text,
    "system_prompt" text,
    "model_name" varchar(50),
    "created_by" int4,
    "is_public" bool DEFAULT false,
    "created_at" timestamptz(6) DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("created_by") REFERENCES "public"."dodo_users" ("id") ON DELETE NO ACTION
);
CREATE INDEX "idx_dodo_bots_created_by" ON "public"."dodo_bots" ("created_by");
CREATE INDEX "idx_dodo_bots_is_public" ON "public"."dodo_bots" ("is_public");

-- 知识库表
CREATE TABLE "public"."dodo_knowledge_bases" (
    "id" int4 NOT NULL DEFAULT nextval('dodo_knowledge_bases_id_seq'::regclass),
    "name" varchar(100) NOT NULL,
    "description" text,
    "created_by" int4 NOT NULL,
    "is_public" bool DEFAULT false,
    "chunking_strategy" varchar(20) DEFAULT 'fixed',
    "chunk_size" int4 DEFAULT 1000,
    "chunk_overlap" int4 DEFAULT 200,
    "created_at" timestamptz(6) DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("created_by") REFERENCES "public"."dodo_users" ("id") ON DELETE NO ACTION
);

-- 文档表（独立文档库，无kb_id）
CREATE TABLE "public"."dodo_documents" (
    "id" int4 NOT NULL DEFAULT nextval('dodo_documents_id_seq'::regclass),
    "name" varchar(255) NOT NULL,
    "minio_path" varchar(255) NOT NULL,
    "file_type" varchar(50),
    "file_size" int4,
    "status" varchar(20) DEFAULT 'pending',
    "created_at" timestamptz(6) DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);
CREATE INDEX "idx_dodo_documents_status" ON "public"."dodo_documents" ("status");

-- 文档分块表
CREATE TABLE "public"."dodo_document_chunks" (
    "id" int4 NOT NULL DEFAULT nextval('dodo_document_chunks_id_seq'::regclass),
    "document_id" int4,
    "content" text NOT NULL,
    "embedding" vector(768),
    "chunk_index" int4,
    "created_at" timestamptz(6) DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("document_id") REFERENCES "public"."dodo_documents" ("id") ON DELETE CASCADE
);
CREATE INDEX "idx_dodo_document_chunks_document_id" ON "public"."dodo_document_chunks" ("document_id");

-- 对话表
CREATE TABLE "public"."dodo_conversations" (
    "id" int4 NOT NULL DEFAULT nextval('dodo_conversations_id_seq'::regclass),
    "user_id" int4,
    "bot_id" int4,
    "created_at" timestamptz(6) DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("user_id") REFERENCES "public"."dodo_users" ("id") ON DELETE NO ACTION,
    FOREIGN KEY ("bot_id") REFERENCES "public"."dodo_bots" ("id") ON DELETE CASCADE
);
CREATE INDEX "idx_dodo_conversations_user_id" ON "public"."dodo_conversations" ("user_id");
CREATE INDEX "idx_dodo_conversations_bot_id" ON "public"."dodo_conversations" ("bot_id");

-- 消息表
CREATE TABLE "public"."dodo_messages" (
    "id" int4 NOT NULL DEFAULT nextval('dodo_messages_id_seq'::regclass),
    "conversation_id" int4,
    "role" varchar(20) NOT NULL,
    "content" text NOT NULL,
    "created_at" timestamptz(6) DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("conversation_id") REFERENCES "public"."dodo_conversations" ("id") ON DELETE CASCADE
);
CREATE INDEX "idx_dodo_messages_conversation_id" ON "public"."dodo_messages" ("conversation_id");

-- 消息-文档关联表（用于对话中上传的文件）
CREATE TABLE "public"."dodo_message_documents" (
    "id" int4 NOT NULL DEFAULT nextval('dodo_message_documents_id_seq'::regclass),
    "message_id" int4 NOT NULL,
    "document_id" int4 NOT NULL,
    "created_at" timestamptz(6) DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("message_id") REFERENCES "public"."dodo_messages" ("id") ON DELETE CASCADE,
    FOREIGN KEY ("document_id") REFERENCES "public"."dodo_documents" ("id") ON DELETE CASCADE
);
CREATE INDEX "idx_dodo_message_documents_message_id" ON "public"."dodo_message_documents" ("message_id");
CREATE INDEX "idx_dodo_message_documents_document_id" ON "public"."dodo_message_documents" ("document_id");

-- 机器人-知识库关联表
CREATE TABLE "public"."dodo_bot_knowledge_bases" (
    "bot_id" int4 NOT NULL,
    "kb_id" int4 NOT NULL,
    PRIMARY KEY ("bot_id", "kb_id"),
    FOREIGN KEY ("bot_id") REFERENCES "public"."dodo_bots" ("id") ON DELETE CASCADE,
    FOREIGN KEY ("kb_id") REFERENCES "public"."dodo_knowledge_bases" ("id") ON DELETE CASCADE
);

-- 知识库-文档关联表（新增）
CREATE TABLE "public"."dodo_kb_documents" (
    "kb_id" int4 NOT NULL,
    "document_id" int4 NOT NULL,
    "created_at" timestamptz(6) DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("kb_id", "document_id"),
    FOREIGN KEY ("kb_id") REFERENCES "public"."dodo_knowledge_bases" ("id") ON DELETE CASCADE,
    FOREIGN KEY ("document_id") REFERENCES "public"."dodo_documents" ("id") ON DELETE CASCADE
);
CREATE INDEX "idx_dodo_kb_documents_kb_id" ON "public"."dodo_kb_documents" ("kb_id");
CREATE INDEX "idx_dodo_kb_documents_document_id" ON "public"."dodo_kb_documents" ("document_id");

-- ====================================================================
-- 组织管理相关表
-- ====================================================================

-- 删除旧表（按依赖顺序）
DROP TABLE IF EXISTS "public"."dodo_organization_members" CASCADE;
DROP TABLE IF EXISTS "public"."dodo_organizations" CASCADE;

-- 组织表
CREATE TABLE "public"."dodo_organizations" (
    "id" int4 NOT NULL DEFAULT nextval('dodo_organizations_id_seq'::regclass),
    "name" varchar(100) NOT NULL,
    "description" text,
    "created_by" int4 NOT NULL,
    "created_at" timestamptz(6) DEFAULT CURRENT_TIMESTAMP,
    "updated_at" timestamptz(6) DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("created_by") REFERENCES "public"."dodo_users" ("id") ON DELETE NO ACTION
);
CREATE INDEX "idx_dodo_organizations_created_by" ON "public"."dodo_organizations" ("created_by");
CREATE INDEX "idx_dodo_organizations_name" ON "public"."dodo_organizations" ("name");
COMMENT ON TABLE "public"."dodo_organizations" IS '组织表';
COMMENT ON COLUMN "public"."dodo_organizations"."name" IS '组织名称';
COMMENT ON COLUMN "public"."dodo_organizations"."description" IS '组织描述';
COMMENT ON COLUMN "public"."dodo_organizations"."created_by" IS '创建者用户ID';

-- 组织成员表
CREATE TABLE "public"."dodo_organization_members" (
    "id" int4 NOT NULL DEFAULT nextval('dodo_organization_members_id_seq'::regclass),
    "organization_id" int4 NOT NULL,
    "user_id" int4 NOT NULL,
    "role" varchar(20) NOT NULL DEFAULT 'member',
    "created_at" timestamptz(6) DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("organization_id") REFERENCES "public"."dodo_organizations" ("id") ON DELETE CASCADE,
    FOREIGN KEY ("user_id") REFERENCES "public"."dodo_users" ("id") ON DELETE CASCADE,
    UNIQUE ("organization_id", "user_id")
);
CREATE INDEX "idx_dodo_org_members_org_id" ON "public"."dodo_organization_members" ("organization_id");
CREATE INDEX "idx_dodo_org_members_user_id" ON "public"."dodo_organization_members" ("user_id");
CREATE INDEX "idx_dodo_org_members_role" ON "public"."dodo_organization_members" ("role");
COMMENT ON TABLE "public"."dodo_organization_members" IS '组织成员表';
COMMENT ON COLUMN "public"."dodo_organization_members"."organization_id" IS '组织ID';
COMMENT ON COLUMN "public"."dodo_organization_members"."user_id" IS '用户ID';
COMMENT ON COLUMN "public"."dodo_organization_members"."role" IS '角色：owner(创建者)/admin(管理员)/member(成员)';

-- ====================================================================
-- 智能模板文档生成工具相关表
-- ====================================================================

-- 删除旧表（按依赖顺序）
DROP TABLE IF EXISTS "public"."dodo_template_generations" CASCADE;
DROP TABLE IF EXISTS "public"."dodo_document_templates" CASCADE;

-- 删除序列
DROP SEQUENCE IF EXISTS "public"."dodo_document_templates_id_seq" CASCADE;
DROP SEQUENCE IF EXISTS "public"."dodo_template_generations_id_seq" CASCADE;

-- 创建序列
CREATE SEQUENCE "public"."dodo_document_templates_id_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;
CREATE SEQUENCE "public"."dodo_template_generations_id_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;

-- 文档模板表
CREATE TABLE "public"."dodo_document_templates" (
    "id" int4 NOT NULL DEFAULT nextval('dodo_document_templates_id_seq'::regclass),
    "name" varchar(255) NOT NULL,
    "tags" varchar(255),
    "file_type" varchar(50) NOT NULL,
    "file_size" int4,
    "minio_path" varchar(500) NOT NULL,
    "created_by" int4 NOT NULL,
    "created_at" timestamptz(6) DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("created_by") REFERENCES "public"."dodo_users" ("id") ON DELETE NO ACTION
);
CREATE INDEX "idx_dodo_document_templates_created_by" ON "public"."dodo_document_templates" ("created_by");
CREATE INDEX "idx_dodo_document_templates_tags" ON "public"."dodo_document_templates" ("tags");
COMMENT ON TABLE "public"."dodo_document_templates" IS '文档模板表';
COMMENT ON COLUMN "public"."dodo_document_templates"."name" IS '模板名称';
COMMENT ON COLUMN "public"."dodo_document_templates"."tags" IS '模板标签，多个标签用逗号分隔';
COMMENT ON COLUMN "public"."dodo_document_templates"."file_type" IS '文件类型：word/pdf';
COMMENT ON COLUMN "public"."dodo_document_templates"."minio_path" IS 'MinIO存储路径';

-- 模板文档生成记录表
CREATE TABLE "public"."dodo_template_generations" (
    "id" int4 NOT NULL DEFAULT nextval('dodo_template_generations_id_seq'::regclass),
    "template_id" int4 NOT NULL,
    "user_id" int4 NOT NULL,
    "user_input" text NOT NULL,
    "generated_content" text,
    "output_file_path" varchar(500),
    "output_file_type" varchar(50),
    "status" varchar(20) DEFAULT 'pending',
    "created_at" timestamptz(6) DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("template_id") REFERENCES "public"."dodo_document_templates" ("id") ON DELETE CASCADE,
    FOREIGN KEY ("user_id") REFERENCES "public"."dodo_users" ("id") ON DELETE NO ACTION
);
CREATE INDEX "idx_dodo_template_generations_template_id" ON "public"."dodo_template_generations" ("template_id");
CREATE INDEX "idx_dodo_template_generations_user_id" ON "public"."dodo_template_generations" ("user_id");
CREATE INDEX "idx_dodo_template_generations_status" ON "public"."dodo_template_generations" ("status");
COMMENT ON TABLE "public"."dodo_template_generations" IS '模板文档生成记录表';
COMMENT ON COLUMN "public"."dodo_template_generations"."user_input" IS '用户输入的个人信息';
COMMENT ON COLUMN "public"."dodo_template_generations"."generated_content" IS 'AI生成的文档内容';
COMMENT ON COLUMN "public"."dodo_template_generations"."output_file_path" IS '生成的文档文件路径';
COMMENT ON COLUMN "public"."dodo_template_generations"."status" IS '状态：pending/generating/completed/failed';

-- ====================================================================
-- 完成！
-- ====================================================================
