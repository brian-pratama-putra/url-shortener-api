-- ============================================================
-- URL SHORTENER API - DATABASE SCHEMA
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users
CREATE TABLE users (
    user_id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username    VARCHAR(100) NOT NULL UNIQUE,
    email       VARCHAR(150) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    created_at  TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta'),
    is_deleted  BOOLEAN NOT NULL DEFAULT false
);

-- Short URLs
CREATE TABLE short_urls (
    short_code      VARCHAR(20) PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES users(user_id),
    original_url    TEXT NOT NULL,
    click_count     INTEGER NOT NULL DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    expired_at      TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta'),
    is_deleted      BOOLEAN NOT NULL DEFAULT false
);

-- Click Logs
CREATE TABLE click_logs (
    log_id      BIGSERIAL PRIMARY KEY,
    short_code  VARCHAR(20) NOT NULL REFERENCES short_urls(short_code),
    ip_address  VARCHAR(50),
    user_agent  VARCHAR(500),
    referer     VARCHAR(500),
    clicked_at  TIMESTAMP NOT NULL DEFAULT (CURRENT_TIMESTAMP AT TIME ZONE 'Asia/Jakarta')
);

-- Index untuk performa query
CREATE INDEX idx_short_urls_user       ON short_urls(user_id);
CREATE INDEX idx_short_urls_click      ON short_urls(click_count DESC) WHERE is_deleted = false;
CREATE INDEX idx_click_logs_short_code ON click_logs(short_code);
CREATE INDEX idx_click_logs_clicked_at ON click_logs(clicked_at);
