-- dev_app Data Generation
-- Generates sample data for trx, p_orders, and p_travers tables
-- Data spans from January 2025 to January 2026

USE dev_app;

DELIMITER $$

DROP PROCEDURE IF EXISTS generate_trx_data$$

CREATE PROCEDURE generate_trx_data()
BEGIN
    DECLARE v_counter INT DEFAULT 0;
    DECLARE v_total_records INT DEFAULT 300;
    DECLARE v_start_date DATE DEFAULT '2025-01-01';
    DECLARE v_end_date DATE DEFAULT '2026-01-18';
    DECLARE v_date_range INT;
    DECLARE v_random_date DATE;
    DECLARE v_random_key VARCHAR(50);
    DECLARE v_random_value VARCHAR(255);
    DECLARE v_key_types VARCHAR(100);

    -- Calculate the number of days between start and end date
    SET v_date_range = DATEDIFF(v_end_date, v_start_date);

    -- Clear existing data
    TRUNCATE TABLE trx;

    -- Generate records
    WHILE v_counter < v_total_records DO
        -- Generate random date within the range
        SET v_random_date = DATE_ADD(v_start_date, INTERVAL FLOOR(RAND() * v_date_range) DAY);

        -- Generate random key from a set of common transaction types
        SET v_key_types = ELT(FLOOR(1 + RAND() * 10),
            'PAYMENT', 'REFUND', 'TRANSFER', 'DEPOSIT', 'WITHDRAWAL',
            'FEE', 'ADJUSTMENT', 'INTEREST', 'CHARGE', 'REVERSAL');
        SET v_random_key = CONCAT(v_key_types, '_', LPAD(FLOOR(RAND() * 10000), 5, '0'));

        -- Generate random value
        SET v_random_value = CONCAT('Amount: $', ROUND(RAND() * 10000, 2),
                                   ' | Ref: ', UPPER(SUBSTRING(MD5(RAND()), 1, 8)));

        -- Insert the record
        INSERT INTO trx (trx_date, `key`, `value`)
        VALUES (v_random_date, v_random_key, v_random_value);

        SET v_counter = v_counter + 1;
    END WHILE;

    -- Display summary
    SELECT
        COUNT(*) as total_records,
        MIN(trx_date) as earliest_date,
        MAX(trx_date) as latest_date,
        COUNT(DISTINCT trx_date) as unique_dates
    FROM trx;

END$$

DELIMITER ;

-- Execute the procedure to generate data
CALL generate_trx_data();

-- Show sample data
SELECT * FROM trx ORDER BY trx_date LIMIT 20;

-- Show data distribution by month
SELECT
    DATE_FORMAT(trx_date, '%Y-%m') as month,
    COUNT(*) as record_count
FROM trx
GROUP BY DATE_FORMAT(trx_date, '%Y-%m')
ORDER BY month;

-- ========================================
-- Generate p_orders table data
-- ========================================

DELIMITER $$

DROP PROCEDURE IF EXISTS generate_orders_data$$

CREATE PROCEDURE generate_orders_data()
BEGIN
    DECLARE v_counter INT DEFAULT 0;
    DECLARE v_total_records INT DEFAULT 250;
    DECLARE v_start_date DATE DEFAULT '2025-01-01';
    DECLARE v_end_date DATE DEFAULT '2026-01-18';
    DECLARE v_date_range INT;
    DECLARE v_random_date DATE;
    DECLARE v_order_number VARCHAR(50);
    DECLARE v_order_status VARCHAR(20);

    -- Calculate the number of days between start and end date
    SET v_date_range = DATEDIFF(v_end_date, v_start_date);

    -- Clear existing data
    TRUNCATE TABLE p_orders;

    -- Generate records
    WHILE v_counter < v_total_records DO
        -- Generate random date within the range
        SET v_random_date = DATE_ADD(v_start_date, INTERVAL FLOOR(RAND() * v_date_range) DAY);

        -- Generate order number
        SET v_order_number = CONCAT('ORD-', YEAR(v_random_date), '-', LPAD(v_counter + 1, 6, '0'));

        -- Generate random order status
        SET v_order_status = ELT(FLOOR(1 + RAND() * 5),
            'PENDING', 'CONFIRMED', 'SHIPPED', 'DELIVERED', 'CANCELLED');

        -- Insert the record
        INSERT INTO p_orders (order_date, customer_id, order_number, order_amount, order_status)
        VALUES (
            v_random_date,
            FLOOR(1000 + RAND() * 9000),
            v_order_number,
            ROUND(10 + RAND() * 5000, 2),
            v_order_status
        );

        SET v_counter = v_counter + 1;
    END WHILE;

    -- Display summary
    SELECT
        COUNT(*) as total_records,
        MIN(order_date) as earliest_date,
        MAX(order_date) as latest_date,
        COUNT(DISTINCT order_date) as unique_dates
    FROM p_orders;

END$$

DELIMITER ;

-- Execute the procedure to generate data
CALL generate_orders_data();

-- Show sample data
SELECT * FROM p_orders ORDER BY order_date LIMIT 20;

-- ========================================
-- Generate p_travers table data
-- ========================================

DELIMITER $$

DROP PROCEDURE IF EXISTS generate_travers_data$$

CREATE PROCEDURE generate_travers_data()
BEGIN
    DECLARE v_counter INT DEFAULT 0;
    DECLARE v_total_records INT DEFAULT 400;
    DECLARE v_start_date DATE DEFAULT '2025-01-01';
    DECLARE v_end_date DATE DEFAULT '2026-01-18';
    DECLARE v_date_range INT;
    DECLARE v_random_date DATE;
    DECLARE v_travers_type VARCHAR(50);
    DECLARE v_source_system VARCHAR(50);
    DECLARE v_status VARCHAR(20);

    -- Calculate the number of days between start and end date
    SET v_date_range = DATEDIFF(v_end_date, v_start_date);

    -- Clear existing data
    TRUNCATE TABLE p_travers;

    -- Generate records
    WHILE v_counter < v_total_records DO
        -- Generate random date within the range
        SET v_random_date = DATE_ADD(v_start_date, INTERVAL FLOOR(RAND() * v_date_range) DAY);

        -- Generate random travers type
        SET v_travers_type = ELT(FLOOR(1 + RAND() * 8),
            'API_CALL', 'WEBHOOK', 'BATCH_JOB', 'USER_ACTION',
            'SYSTEM_EVENT', 'NOTIFICATION', 'DATA_SYNC', 'AUDIT_LOG');

        -- Generate random source system
        SET v_source_system = ELT(FLOOR(1 + RAND() * 5),
            'WEB_APP', 'MOBILE_APP', 'ADMIN_PORTAL', 'BATCH_PROCESSOR', 'EXTERNAL_API');

        -- Generate random status
        SET v_status = ELT(FLOOR(1 + RAND() * 4),
            'NEW', 'PROCESSING', 'COMPLETED', 'FAILED');

        -- Insert the record
        INSERT INTO p_travers (created_date, travers_type, source_system, reference_id, payload, status)
        VALUES (
            v_random_date,
            v_travers_type,
            v_source_system,
            CONCAT('REF-', UPPER(SUBSTRING(MD5(RAND()), 1, 12))),
            CONCAT('{"event_id": "', UPPER(SUBSTRING(MD5(RAND()), 1, 8)),
                   '", "timestamp": "', NOW(), '", "data": "sample_payload"}'),
            v_status
        );

        SET v_counter = v_counter + 1;
    END WHILE;

    -- Display summary
    SELECT
        COUNT(*) as total_records,
        MIN(created_date) as earliest_date,
        MAX(created_date) as latest_date,
        COUNT(DISTINCT created_date) as unique_dates
    FROM p_travers;

END$$

DELIMITER ;

-- Execute the procedure to generate data
CALL generate_travers_data();

-- Show sample data
SELECT * FROM p_travers ORDER BY created_date LIMIT 20;

-- ========================================
-- Summary of all tables
-- ========================================

SELECT 'Summary of all tables' as info;

SELECT
    'trx' as table_name,
    COUNT(*) as total_records,
    MIN(trx_date) as earliest_date,
    MAX(trx_date) as latest_date
FROM trx
UNION ALL
SELECT
    'p_orders' as table_name,
    COUNT(*) as total_records,
    MIN(order_date) as earliest_date,
    MAX(order_date) as latest_date
FROM p_orders
UNION ALL
SELECT
    'p_travers' as table_name,
    COUNT(*) as total_records,
    MIN(created_date) as earliest_date,
    MAX(created_date) as latest_date
FROM p_travers;
