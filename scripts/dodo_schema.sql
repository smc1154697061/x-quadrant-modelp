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
COMMENT ON COLUMN "public"."dodo_knowledge_bases"."chunking_strategy" IS '分块策略: fixed-固定长度, semantic-语义分块, sentence-句子分块';
COMMENT ON COLUMN "public"."dodo_knowledge_bases"."chunk_size" IS '分块大小(字符数)';
COMMENT ON COLUMN "public"."dodo_knowledge_bases"."chunk_overlap" IS '分块重叠大小(字符数)';

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
-- 完成！
-- ====================================================================
