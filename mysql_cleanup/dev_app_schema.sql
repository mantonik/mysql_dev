-- dev_app Database Schema
-- Creates tables for testing cleanup operations: trx, p_orders, p_travers

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS dev_app;

USE dev_app;

-- Drop tables if exist (for reloading)
DROP TABLE IF EXISTS trx;
DROP TABLE IF EXISTS p_orders;
DROP TABLE IF EXISTS p_travers;

-- Create trx table
CREATE TABLE trx (
    id INT AUTO_INCREMENT PRIMARY KEY,
    trx_date DATE NOT NULL,
    `key` VARCHAR(50) NOT NULL,
    `value` VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_trx_date (trx_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Sample transaction table for cleanup testing';

-- Create p_orders table
CREATE TABLE p_orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    order_date DATE NOT NULL,
    customer_id INT NOT NULL,
    order_number VARCHAR(50) NOT NULL,
    order_amount DECIMAL(10,2) DEFAULT 0.00,
    order_status VARCHAR(20) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_order_date (order_date),
    INDEX idx_customer_id (customer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Sample orders table for cleanup testing';

-- Create p_travers table
CREATE TABLE p_travers (
    travers_id INT AUTO_INCREMENT PRIMARY KEY,
    created_date DATE NOT NULL,
    travers_type VARCHAR(50) NOT NULL,
    source_system VARCHAR(50) DEFAULT NULL,
    reference_id VARCHAR(100) DEFAULT NULL,
    payload TEXT DEFAULT NULL,
    status VARCHAR(20) DEFAULT 'NEW',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_created_date (created_date),
    INDEX idx_travers_type (travers_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Sample traversal/messaging table for cleanup testing';
