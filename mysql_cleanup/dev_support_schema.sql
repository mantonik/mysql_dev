-- dev_support Database Schema
-- Creates the cleanup configuration table

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS dev_support;

USE dev_support;

-- Drop table if exists (for reloading)
DROP TABLE IF EXISTS c_sup_cleanup_config;

-- Create cleanup configuration table
CREATE TABLE c_sup_cleanup_config (
    config_id INT AUTO_INCREMENT PRIMARY KEY,
    login_path VARCHAR(100) NOT NULL COMMENT 'MySQL login path for connecting to target database',
    oracle_tns_name VARCHAR(100) DEFAULT NULL COMMENT 'Oracle TNS name (for Oracle databases, NULL for MySQL)',
    db_schema VARCHAR(100) NOT NULL COMMENT 'Target database schema name',
    table_name VARCHAR(100) NOT NULL COMMENT 'Target table name to cleanup',
    where_condition TEXT NOT NULL COMMENT 'WHERE clause with RETENSION keyword placeholder',
    retension_days INT NOT NULL COMMENT 'Number of days to retain data (replaces RETENSION keyword)',
    cleanup_group VARCHAR(50) NOT NULL COMMENT 'Group name for organizing cleanup jobs',
    group_id INT NOT NULL COMMENT 'Group ID to execute multiple tables in one process run',
    status TINYINT(1) DEFAULT 1 COMMENT 'Status: 1=active (execute cleanup), 0=inactive (skip)',
    binlog_on_off TINYINT(1) DEFAULT 1 COMMENT 'Binary log control: 1=enable binlog (replicate), 0=disable binlog (SET sql_log_bin=0)',
    delete_limit INT DEFAULT 1000 COMMENT 'Number of records to delete per batch',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_run_at TIMESTAMP NULL DEFAULT NULL COMMENT 'Last successful cleanup execution timestamp',
    INDEX idx_group (cleanup_group),
    INDEX idx_group_id (group_id),
    INDEX idx_status (status),
    INDEX idx_binlog (binlog_on_off),
    UNIQUE KEY unique_cleanup (db_schema, table_name, cleanup_group)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Configuration table for automated database cleanup operations';
