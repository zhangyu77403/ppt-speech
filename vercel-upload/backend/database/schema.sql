-- 讲稿工坊 数据库初始化脚本（MySQL 8.0+）
-- 用法：mysql -uroot -p < schema.sql

CREATE DATABASE IF NOT EXISTS `ppt_speech`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `ppt_speech`;

-- ---------------- 用户 ----------------
CREATE TABLE IF NOT EXISTS `users` (
  `id`            INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `username`      VARCHAR(64)  NOT NULL,
  `display_name`  VARCHAR(64)  NOT NULL DEFAULT '',
  `password_hash` VARCHAR(256) NOT NULL,
  `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_users_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------- 演示文稿 ----------------
CREATE TABLE IF NOT EXISTS `presentations` (
  `id`                INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`           INT UNSIGNED NOT NULL,
  `title`             VARCHAR(255) NOT NULL DEFAULT '未命名演示文稿',
  `original_filename` VARCHAR(255) NOT NULL DEFAULT '',
  `stored_path`       VARCHAR(512) NOT NULL DEFAULT '',
  `file_size`         INT UNSIGNED NOT NULL DEFAULT 0,
  `slide_count`       INT UNSIGNED NOT NULL DEFAULT 0,
  `created_at`        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_presentations_user` (`user_id`),
  CONSTRAINT `fk_presentations_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------- 幻灯片 ----------------
CREATE TABLE IF NOT EXISTS `slides` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `presentation_id` INT UNSIGNED NOT NULL,
  `slide_index`     INT UNSIGNED NOT NULL,
  `title`           VARCHAR(255) NOT NULL DEFAULT '',
  `body`            JSON         NULL,
  `notes`           TEXT         NULL,
  PRIMARY KEY (`id`),
  KEY `idx_slides_presentation` (`presentation_id`),
  CONSTRAINT `fk_slides_presentation` FOREIGN KEY (`presentation_id`) REFERENCES `presentations` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------- 讲稿 ----------------
CREATE TABLE IF NOT EXISTS `scripts` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`         INT UNSIGNED NOT NULL,
  `presentation_id` INT UNSIGNED NOT NULL,
  `title`           VARCHAR(255) NOT NULL DEFAULT '',
  `style_key`       VARCHAR(32)  NOT NULL DEFAULT 'formal',
  `style_name`      VARCHAR(32)  NOT NULL DEFAULT '正式严谨',
  `duration_min`    INT UNSIGNED NOT NULL DEFAULT 8,
  `audience`        VARCHAR(128) NOT NULL DEFAULT '',
  `language`        VARCHAR(16)  NOT NULL DEFAULT 'zh',
  `engine`          VARCHAR(32)  NOT NULL DEFAULT 'template',
  `word_count`      INT UNSIGNED NOT NULL DEFAULT 0,
  `content`         JSON         NULL,
  `created_at`      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_scripts_user` (`user_id`),
  KEY `idx_scripts_presentation` (`presentation_id`),
  CONSTRAINT `fk_scripts_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_scripts_presentation` FOREIGN KEY (`presentation_id`) REFERENCES `presentations` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 说明：表结构由 SQLAlchemy 模型（backend/app/models.py）定义，
-- 后端启动时会自动 create_all，本脚本用于手工初始化 / 交作业时展示 DDL。
