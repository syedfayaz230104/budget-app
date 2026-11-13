-- ============================================================
-- YottaFlex Hackathon – MySQL 8.0+ Schema
-- All 9 core entities with FK constraints, indexes, enums
-- ============================================================

CREATE DATABASE IF NOT EXISTS hackathon_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE hackathon_db;

-- ─── Category ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS categories (
    id              VARCHAR(32)  PRIMARY KEY,
    name            VARCHAR(128) NOT NULL,
    parent_category VARCHAR(32)  NULL REFERENCES categories(id),
    description     TEXT         NULL
) ENGINE=InnoDB;

-- ─── CategoryRule ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS category_rules (
    id               INT          PRIMARY KEY AUTO_INCREMENT,
    merchant_pattern VARCHAR(255) NOT NULL,
    category_id      VARCHAR(32)  NOT NULL,
    priority         INT          DEFAULT 1,
    is_active        TINYINT(1)   DEFAULT 1,
    CONSTRAINT fk_rule_category FOREIGN KEY (category_id) REFERENCES categories(id)
) ENGINE=InnoDB;

-- ─── UserProfile ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_profiles (
    id         VARCHAR(16)  PRIMARY KEY,
    first_name VARCHAR(64)  NOT NULL,
    last_name  VARCHAR(64)  NOT NULL,
    email      VARCHAR(128) NOT NULL UNIQUE,
    phone      VARCHAR(20)  NULL,
    created_at DATETIME     DEFAULT CURRENT_TIMESTAMP,
    is_active  TINYINT(1)   DEFAULT 1
) ENGINE=InnoDB;

-- ─── Account ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS accounts (
    id           VARCHAR(24)  PRIMARY KEY,
    user_id      VARCHAR(16)  NOT NULL,
    account_type ENUM('checking','savings','credit') NOT NULL,
    balance      DOUBLE       DEFAULT 0.0,
    currency     VARCHAR(8)   DEFAULT 'USD',
    opened_at    DATETIME     DEFAULT CURRENT_TIMESTAMP,
    closed_at    DATETIME     NULL,
    status       ENUM('active','closed','frozen') DEFAULT 'active',
    CONSTRAINT fk_account_user FOREIGN KEY (user_id) REFERENCES user_profiles(id)
) ENGINE=InnoDB;

-- ─── Merchant ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS merchants (
    id          INT          PRIMARY KEY AUTO_INCREMENT,
    name        VARCHAR(255) NOT NULL,
    alias       VARCHAR(255) NULL,
    category_id VARCHAR(32)  NULL,
    city        VARCHAR(128) NULL,
    state       VARCHAR(64)  NULL,
    country     VARCHAR(64)  DEFAULT 'US',
    is_online   TINYINT(1)   DEFAULT 0,
    CONSTRAINT fk_merchant_category FOREIGN KEY (category_id) REFERENCES categories(id)
) ENGINE=InnoDB;

-- ─── RecurringSeries ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS recurring_series (
    id           VARCHAR(16) PRIMARY KEY,
    account_id   VARCHAR(24) NOT NULL,
    merchant_id  INT         NULL,
    category_id  VARCHAR(32) NULL,
    frequency    ENUM('weekly','monthly','annual') NOT NULL,
    amount       DOUBLE      NOT NULL,
    start_date   DATETIME    NOT NULL,
    end_date     DATETIME    NULL,
    day_of_month INT         NULL,
    is_active    TINYINT(1)  DEFAULT 1,
    CONSTRAINT fk_rec_account  FOREIGN KEY (account_id)  REFERENCES accounts(id),
    CONSTRAINT fk_rec_merchant FOREIGN KEY (merchant_id) REFERENCES merchants(id),
    CONSTRAINT fk_rec_category FOREIGN KEY (category_id) REFERENCES categories(id)
) ENGINE=InnoDB;

-- ─── Transaction ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS transactions (
    id                  VARCHAR(24)  PRIMARY KEY,
    account_id          VARCHAR(24)  NOT NULL,
    merchant_id         INT          NULL,
    category_id         VARCHAR(32)  NULL,
    recurring_series_id VARCHAR(16)  NULL,
    amount              DOUBLE       NOT NULL,
    txn_type            ENUM('debit','credit','transfer','refund') NOT NULL,
    status              ENUM('pending','cleared','failed') DEFAULT 'cleared',
    description         VARCHAR(512) NULL,
    txn_date            DATETIME     NOT NULL,
    posted_date         DATETIME     NULL,
    is_recurring        TINYINT(1)   DEFAULT 0,
    timezone            VARCHAR(64)  DEFAULT 'UTC',
    is_anomaly          TINYINT(1)   DEFAULT 0,
    ground_truth_label  VARCHAR(64)  NULL,
    CONSTRAINT fk_txn_account  FOREIGN KEY (account_id)          REFERENCES accounts(id),
    CONSTRAINT fk_txn_merchant FOREIGN KEY (merchant_id)         REFERENCES merchants(id),
    CONSTRAINT fk_txn_category FOREIGN KEY (category_id)         REFERENCES categories(id),
    CONSTRAINT fk_txn_rec      FOREIGN KEY (recurring_series_id) REFERENCES recurring_series(id),
    INDEX idx_txn_account_date (account_id, txn_date),
    INDEX idx_txn_category     (category_id)
) ENGINE=InnoDB;

-- ─── Budget ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS budgets (
    id              VARCHAR(48) PRIMARY KEY,
    user_id         VARCHAR(16) NOT NULL,
    category_id     VARCHAR(32) NOT NULL,
    period_month    INT         NOT NULL,
    period_year     INT         NOT NULL,
    amount_budgeted DOUBLE      NOT NULL,
    amount_spent    DOUBLE      DEFAULT 0.0,
    status          ENUM('on_track','over_budget','under_budget') DEFAULT 'on_track',
    CONSTRAINT fk_budget_user     FOREIGN KEY (user_id)     REFERENCES user_profiles(id),
    CONSTRAINT fk_budget_category FOREIGN KEY (category_id) REFERENCES categories(id),
    UNIQUE KEY uq_budget_user_cat_period (user_id, category_id, period_month, period_year)
) ENGINE=InnoDB;

-- ─── Insight ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS insights (
    id           INT         PRIMARY KEY AUTO_INCREMENT,
    user_id      VARCHAR(16) NOT NULL,
    category_id  VARCHAR(32) NULL,
    insight_type ENUM('over_budget','unusual_spend','recurring_missed',
                      'refund_detected','transfer_double','budget_mismatch') NOT NULL,
    description  TEXT        NOT NULL,
    severity     ENUM('low','medium','high') DEFAULT 'low',
    created_at   DATETIME    DEFAULT CURRENT_TIMESTAMP,
    is_resolved  TINYINT(1)  DEFAULT 0,
    CONSTRAINT fk_insight_user     FOREIGN KEY (user_id)     REFERENCES user_profiles(id),
    CONSTRAINT fk_insight_category FOREIGN KEY (category_id) REFERENCES categories(id)
) ENGINE=InnoDB;
