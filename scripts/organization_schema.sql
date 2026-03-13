-- ====================================================================
-- 组织管理相关表
-- ====================================================================

-- 删除旧表（按依赖顺序）
DROP TABLE IF EXISTS "public"."dodo_organization_members" CASCADE;
DROP TABLE IF EXISTS "public"."dodo_organizations" CASCADE;

-- 删除序列
DROP SEQUENCE IF EXISTS "public"."dodo_organizations_id_seq" CASCADE;
DROP SEQUENCE IF EXISTS "public"."dodo_organization_members_id_seq" CASCADE;

-- 创建序列
CREATE SEQUENCE "public"."dodo_organizations_id_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;
CREATE SEQUENCE "public"."dodo_organization_members_id_seq" INCREMENT 1 MINVALUE 1 MAXVALUE 2147483647 START 1 CACHE 1;

-- 组织表
CREATE TABLE "public"."dodo_organizations" (
    "id" int4 NOT NULL DEFAULT nextval('dodo_organizations_id_seq'::regclass),
    "name" varchar(100) NOT NULL,
    "description" text,
    "created_by" int4 NOT NULL,
    "created_at" timestamptz(6) DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("created_by") REFERENCES "public"."dodo_users" ("id") ON DELETE NO ACTION
);
CREATE INDEX "idx_dodo_organizations_created_by" ON "public"."dodo_organizations" ("created_by");
COMMENT ON TABLE "public"."dodo_organizations" IS '组织表';
COMMENT ON COLUMN "public"."dodo_organizations"."name" IS '组织名称';
COMMENT ON COLUMN "public"."dodo_organizations"."description" IS '组织描述';
COMMENT ON COLUMN "public"."dodo_organizations"."created_by" IS '创建者用户ID';

-- 组织成员表
CREATE TABLE "public"."dodo_organization_members" (
    "id" int4 NOT NULL DEFAULT nextval('dodo_organization_members_id_seq'::regclass),
    "org_id" int4 NOT NULL,
    "user_id" int4 NOT NULL,
    "role" varchar(20) NOT NULL DEFAULT 'member',
    "joined_at" timestamptz(6) DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id"),
    FOREIGN KEY ("org_id") REFERENCES "public"."dodo_organizations" ("id") ON DELETE CASCADE,
    FOREIGN KEY ("user_id") REFERENCES "public"."dodo_users" ("id") ON DELETE CASCADE,
    UNIQUE ("org_id", "user_id")
);
CREATE INDEX "idx_dodo_organization_members_org_id" ON "public"."dodo_organization_members" ("org_id");
CREATE INDEX "idx_dodo_organization_members_user_id" ON "public"."dodo_organization_members" ("user_id");
COMMENT ON TABLE "public"."dodo_organization_members" IS '组织成员表';
COMMENT ON COLUMN "public"."dodo_organization_members"."role" IS '角色：admin(管理员)/member(成员)';
