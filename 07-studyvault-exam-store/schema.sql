-- Sessiya tayyorgarlik bot — PostgreSQL sxema (MySQL'dan ko'chirilgan, toza)
-- Jadvallar: users, settings, payments, products, referrals

-- Foydalanuvchilar (chat_id asosiy kalit; step + temp_data FSM uchun)
CREATE TABLE IF NOT EXISTS users (
    chat_id     BIGINT PRIMARY KEY,
    username    TEXT,
    first_name  TEXT,
    last_name   TEXT,
    phone       TEXT,
    step        TEXT        NOT NULL DEFAULT 'none',
    temp_data   JSONB       NOT NULL DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- Mavjud jadvalga ustun qo'shish (idempotent)
ALTER TABLE users ADD COLUMN IF NOT EXISTS username   TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS first_name TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_name  TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone      TEXT;

-- Sozlamalar (key/value JSON: config, stats, global_tag...)
CREATE TABLE IF NOT EXISTS settings (
    key_name      TEXT PRIMARY KEY,
    value_content JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- Mahsulotlar (fan bazalari — Telegram fayllar)
CREATE TABLE IF NOT EXISTS products (
    id          BIGSERIAL PRIMARY KEY,
    code        TEXT UNIQUE NOT NULL,
    name        TEXT        NOT NULL DEFAULT '',
    course      TEXT        NOT NULL DEFAULT '',
    subject     TEXT        NOT NULL DEFAULT '',
    description TEXT        NOT NULL DEFAULT '',
    file_id     TEXT        NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_products_course_subject ON products (course, subject);

-- To'lovlar (Click — HWID asosida aktivlashtirish)
CREATE TABLE IF NOT EXISTS payments (
    id             BIGSERIAL PRIMARY KEY,
    chat_id        BIGINT      NOT NULL,
    hwid           TEXT        NOT NULL DEFAULT '',
    base_num       TEXT        NOT NULL DEFAULT '',
    amount         INTEGER     NOT NULL DEFAULT 0,
    status         TEXT        NOT NULL DEFAULT 'created',
    click_trans_id TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    paid_at        TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_payments_chat_status ON payments (chat_id, status);
CREATE UNIQUE INDEX IF NOT EXISTS uniq_payments_click_trans_id
    ON payments (click_trans_id) WHERE click_trans_id IS NOT NULL;

-- Referallar (taklif qilingan foydalanuvchilar)
CREATE TABLE IF NOT EXISTS referrals (
    id           BIGSERIAL PRIMARY KEY,
    referrer_id  BIGINT      NOT NULL,
    invited_id   BIGINT      NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (referrer_id, invited_id)
);
CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals (referrer_id);
