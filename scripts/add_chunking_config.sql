-- ====================================================================
-- 知识库分块配置迁移脚本
-- 为 dodo_knowledge_bases 表添加分块策略配置字段
-- ====================================================================

-- 添加分块策略字段
ALTER TABLE "public"."dodo_knowledge_bases" 
ADD COLUMN IF NOT EXISTS "chunking_strategy" varchar(20) DEFAULT 'fixed';

-- 添加分块大小字段
ALTER TABLE "public"."dodo_knowledge_bases" 
ADD COLUMN IF NOT EXISTS "chunk_size" int4 DEFAULT 1000;

-- 添加分块重叠字段
ALTER TABLE "public"."dodo_knowledge_bases" 
ADD COLUMN IF NOT EXISTS "chunk_overlap" int4 DEFAULT 200;

-- 添加注释
COMMENT ON COLUMN "public"."dodo_knowledge_bases"."chunking_strategy" IS '分块策略: fixed-固定长度, semantic-语义分块, sentence-句子分块';
COMMENT ON COLUMN "public"."dodo_knowledge_bases"."chunk_size" IS '分块大小(字符数)';
COMMENT ON COLUMN "public"."dodo_knowledge_bases"."chunk_overlap" IS '分块重叠大小(字符数)';

-- 更新现有数据，设置默认值
UPDATE "public"."dodo_knowledge_bases" 
SET "chunking_strategy" = 'fixed',
    "chunk_size" = 1000,
    "chunk_overlap" = 200
WHERE "chunking_strategy" IS NULL;

-- ====================================================================
-- 完成！
-- ====================================================================
