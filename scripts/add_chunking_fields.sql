-- 为 dodo_knowledge_bases 表添加分块配置字段
-- 执行此脚本前请先备份数据

-- 添加分块策略字段（默认为 fixed）
ALTER TABLE "public"."dodo_knowledge_bases" 
ADD COLUMN IF NOT EXISTS "chunking_strategy" varchar(20) DEFAULT 'fixed';

-- 添加分块大小字段（默认 1000）
ALTER TABLE "public"."dodo_knowledge_bases" 
ADD COLUMN IF NOT EXISTS "chunk_size" int4 DEFAULT 1000;

-- 添加分块重叠字段（默认 200）
ALTER TABLE "public"."dodo_knowledge_bases" 
ADD COLUMN IF NOT EXISTS "chunk_overlap" int4 DEFAULT 200;

-- 添加字段注释
COMMENT ON COLUMN "public"."dodo_knowledge_bases"."chunking_strategy" IS '分块策略: fixed/semantic/sentence';
COMMENT ON COLUMN "public"."dodo_knowledge_bases"."chunk_size" IS '分块大小';
COMMENT ON COLUMN "public"."dodo_knowledge_bases"."chunk_overlap" IS '分块重叠大小';
