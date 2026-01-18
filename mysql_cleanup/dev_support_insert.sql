-- dev_support Data
-- Sample cleanup configuration records

USE dev_support;

-- Insert sample cleanup configurations

-- Configuration 1: dev_app.trx table - Delete records older than 300 days WITH binlog (replicate to slaves)
INSERT INTO c_sup_cleanup_config
    (login_path, oracle_tns_name, db_schema, table_name, where_condition,
     retension_days, cleanup_group, group_id, status, binlog_on_off, delete_limit)
VALUES
    ('devclaude', NULL, 'dev_app', 'trx',
     'trx_date < DATE_ADD(CURDATE(), INTERVAL -RETENSION DAY)',
     300, 'daily_cleanup', 1, 1, 1, 1000);

-- Configuration 2: dev_app.p_orders table - Delete records older than 180 days WITHOUT binlog
INSERT INTO c_sup_cleanup_config
    (login_path, oracle_tns_name, db_schema, table_name, where_condition,
     retension_days, cleanup_group, group_id, status, binlog_on_off, delete_limit)
VALUES
    ('devclaude', NULL, 'dev_app', 'p_orders',
     'order_date < DATE_ADD(CURDATE(), INTERVAL -RETENSION DAY)',
     180, 'daily_cleanup', 1, 1, 0, 500);

-- Configuration 3: dev_app.p_travers table - Delete records older than 90 days WITH binlog
INSERT INTO c_sup_cleanup_config
    (login_path, oracle_tns_name, db_schema, table_name, where_condition,
     retension_days, cleanup_group, group_id, status, binlog_on_off, delete_limit)
VALUES
    ('devclaude', NULL, 'dev_app', 'p_travers',
     'created_date < DATE_ADD(CURDATE(), INTERVAL -RETENSION DAY)',
     90, 'daily_cleanup', 1, 1, 1, 750);

-- Display inserted configurations
SELECT
    config_id,
    login_path,
    db_schema,
    table_name,
    where_condition,
    retension_days,
    cleanup_group,
    group_id,
    CASE status
        WHEN 1 THEN 'ACTIVE'
        WHEN 0 THEN 'INACTIVE'
    END as status_desc,
    CASE binlog_on_off
        WHEN 1 THEN 'ENABLED (Replicate)'
        WHEN 0 THEN 'DISABLED (No Replication)'
    END as binlog_status,
    delete_limit
FROM c_sup_cleanup_config
ORDER BY group_id, config_id;
