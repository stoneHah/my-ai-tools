/*
 Navicat Premium Data Transfer

 Source Server         : docker-mysql
 Source Server Type    : MySQL
 Source Server Version : 50744 (5.7.44)
 Source Host           : localhost:3306
 Source Schema         : ai_tools

 Target Server Type    : MySQL
 Target Server Version : 50744 (5.7.44)
 File Encoding         : 65001

 Date: 07/04/2025 08:56:59
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for tts_clone_tasks
-- ----------------------------
DROP TABLE IF EXISTS `tts_clone_tasks`;
CREATE TABLE `tts_clone_tasks`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `task_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `user_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `app_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `sample_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `voice_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `result_voice_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `platform_id` int(11) NOT NULL,
  `created_at` datetime NULL DEFAULT NULL,
  `updated_at` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `task_id`(`task_id`) USING BTREE,
  INDEX `ix_tts_clone_tasks_app_id`(`app_id`) USING BTREE,
  INDEX `ix_tts_clone_tasks_user_id`(`user_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for tts_clone_voice_languages
-- ----------------------------
DROP TABLE IF EXISTS `tts_clone_voice_languages`;
CREATE TABLE `tts_clone_voice_languages`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `clone_voice_id` int(11) NOT NULL,
  `language_id` int(11) NOT NULL,
  `created_at` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for tts_clone_voices
-- ----------------------------
DROP TABLE IF EXISTS `tts_clone_voices`;
CREATE TABLE `tts_clone_voices`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `voice_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL,
  `user_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `app_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `platform_id` int(11) NOT NULL,
  `original_sample_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL,
  `is_streaming` tinyint(1) NULL DEFAULT NULL,
  `is_active` tinyint(1) NULL DEFAULT NULL,
  `created_at` datetime NULL DEFAULT NULL,
  `updated_at` datetime NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `voice_id`(`voice_id`) USING BTREE,
  INDEX `ix_tts_clone_voices_app_id`(`app_id`) USING BTREE,
  INDEX `ix_tts_clone_voices_user_id`(`user_id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 6 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for tts_languages
-- ----------------------------
DROP TABLE IF EXISTS `tts_languages`;
CREATE TABLE `tts_languages`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '语言名称',
  `code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '语言代码',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `code`(`code`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for tts_platforms
-- ----------------------------
DROP TABLE IF EXISTS `tts_platforms`;
CREATE TABLE `tts_platforms`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '平台名称',
  `code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '平台代码',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '平台描述',
  `api_base_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'API基础URL',
  `is_active` tinyint(1) NULL DEFAULT NULL COMMENT '是否激活',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `code`(`code`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 3 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for tts_voice_categories
-- ----------------------------
DROP TABLE IF EXISTS `tts_voice_categories`;
CREATE TABLE `tts_voice_categories`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '分类名称',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '分类描述',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for tts_voices
-- ----------------------------
DROP TABLE IF EXISTS `tts_voices`;
CREATE TABLE `tts_voices`  (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `voice_id` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '音色ID',
  `name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '音色名称',
  `gender` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '性别',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '音色描述',
  `platform_id` int(11) NOT NULL COMMENT '平台ID',
  `category_id` int(11) NULL DEFAULT NULL COMMENT '分类ID',
  `is_streaming` tinyint(1) NULL DEFAULT NULL COMMENT '是否支持流式接口',
  `is_active` tinyint(1) NULL DEFAULT NULL COMMENT '是否激活',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `avatar_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '音色头像URL',
  `sample_audio_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '音色试听URL',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `voice_id`(`voice_id`) USING BTREE,
  INDEX `platform_id`(`platform_id`) USING BTREE,
  INDEX `category_id`(`category_id`) USING BTREE,
  CONSTRAINT `tts_voices_ibfk_1` FOREIGN KEY (`platform_id`) REFERENCES `tts_platforms` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `tts_voices_ibfk_2` FOREIGN KEY (`category_id`) REFERENCES `tts_voice_categories` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 62 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for voice_language_association
-- ----------------------------
DROP TABLE IF EXISTS `voice_language_association`;
CREATE TABLE `voice_language_association`  (
  `voice_id` int(11) NOT NULL,
  `language_id` int(11) NOT NULL,
  PRIMARY KEY (`voice_id`, `language_id`) USING BTREE,
  INDEX `language_id`(`language_id`) USING BTREE,
  CONSTRAINT `voice_language_association_ibfk_1` FOREIGN KEY (`voice_id`) REFERENCES `tts_voices` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `voice_language_association_ibfk_2` FOREIGN KEY (`language_id`) REFERENCES `tts_languages` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
