# MySQL Cleanup Configuration Table Reference

## Overview
This document describes the `dev_support.c_sup_cleanup_config` table used to configure automated database cleanup operations.

## Table: c_sup_cleanup_config

### Location
- **Development**: `dev_support.c_sup_cleanup_config`
- **QA**: `qa_support.c_sup_cleanup_config` (or `support.c_sup_cleanup_config`)
- **Production**: `support.c_sup_cleanup_config`

### Table Schema

```sql
CREATE TABLE c_sup_cleanup_config (
    config_id INT AUTO_INCREMENT PRIMARY KEY,
    login_path VARCHAR(100) NOT NULL,
    oracle_tns_name VARCHAR(100) DEFAULT NULL,
    db_schema VARCHAR(100) NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    where_condition TEXT NOT NULL,
    retension_days INT NOT NULL,
    cleanup_group VARCHAR(50) NOT NULL,
    group_id INT NOT NULL,
    status TINYINT(1) DEFAULT 1,
    binlog_on_off TINYINT(1) DEFAULT 1,
    delete_limit INT DEFAULT 1000,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    last_run_at TIMESTAMP NULL DEFAULT NULL,
    INDEX idx_group (cleanup_group),
    INDEX idx_group_id (group_id),
    INDEX idx_status (status),
    INDEX idx_binlog (binlog_on_off),
    UNIQUE KEY unique_cleanup (db_schema, table_name, cleanup_group)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## Column Descriptions

### Primary Key
- **config_id**: `INT AUTO_INCREMENT PRIMARY KEY`
  - Auto-incrementing unique identifier for each cleanup configuration

### Connection Parameters
- **login_path**: `VARCHAR(100) NOT NULL`
  - MySQL login path configured using `mysql_config_editor`
  - Used to connect to the target database
  - Example: `devclaude`, `prod_app`, `qa_readonly`
  - Configure with: `mysql_config_editor set --login-path=NAME --host=HOST --port=PORT --user=USER --password`

- **oracle_tns_name**: `VARCHAR(100) DEFAULT NULL`
  - Oracle TNS name for Oracle database connections
  - Set to NULL for MySQL databases
  - Used when cleanup script supports Oracle databases

### Target Database/Table
- **db_schema**: `VARCHAR(100) NOT NULL`
  - Target database schema name where the table resides
  - Example: `dev_app`, `production_db`, `analytics`

- **table_name**: `VARCHAR(100) NOT NULL`
  - Name of the table to perform cleanup operations on
  - Example: `trx`, `p_orders`, `audit_logs`

### Cleanup Logic
- **where_condition**: `TEXT NOT NULL`
  - WHERE clause for the DELETE statement
  - Must include the keyword `RETENSION` which will be replaced by `retension_days` value
  - Example: `trx_date < DATE_ADD(CURDATE(), INTERVAL -RETENSION DAY)`
  - Example: `created_date < DATE_ADD(CURDATE(), INTERVAL -RETENSION DAY) AND status = 'ARCHIVED'`

- **retension_days**: `INT NOT NULL`
  - Number of days to retain data
  - Replaces the `RETENSION` keyword in `where_condition`
  - Example: 300 means keep data for 300 days, delete older records

### Grouping and Control
- **cleanup_group**: `VARCHAR(50) NOT NULL`
  - Logical group name for organizing cleanup jobs
  - Example: `daily_cleanup`, `weekly_archive`, `monthly_purge`
  - Used for filtering which cleanups to run

- **group_id**: `INT NOT NULL`
  - Numeric group identifier to execute multiple tables in one process run
  - All configurations with the same `group_id` will be processed together
  - Example: group_id=1 might include trx, p_orders, p_travers tables

- **status**: `TINYINT(1) DEFAULT 1`
  - Controls whether this configuration is active
  - **1** = ACTIVE (cleanup will be executed)
  - **0** = INACTIVE (cleanup will be skipped)
  - Use this to temporarily disable a cleanup without deleting the configuration

### Replication Control
- **binlog_on_off**: `TINYINT(1) DEFAULT 1`
  - Controls binary logging for delete operations
  - **1** = Binary logging ENABLED (deletes will replicate to slaves)
  - **0** = Binary logging DISABLED (execute `SET sql_log_bin=0` before delete)
  - When set to 0, the cleanup script will:
    1. Execute `SET sql_log_bin=0` in the session
    2. Perform the delete operations
    3. Deletes will NOT be recorded in binary log
    4. Slave servers will NOT replicate these deletes

### Batch Control
- **delete_limit**: `INT DEFAULT 1000`
  - Number of records to delete per batch operation
  - Smaller values reduce lock contention but increase execution time
  - Larger values are faster but may cause longer locks
  - Recommended: 500-2000 depending on table size and load

### Audit Columns
- **created_at**: `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
  - Timestamp when the configuration was created

- **updated_at**: `TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP`
  - Timestamp when the configuration was last modified

- **last_run_at**: `TIMESTAMP NULL DEFAULT NULL`
  - Timestamp of the last successful cleanup execution
  - Updated by the cleanup script after successful completion

## Sample Configurations

### Example 1: Transaction Table with Replication
```sql
INSERT INTO c_sup_cleanup_config
    (login_path, oracle_tns_name, db_schema, table_name, where_condition,
     retension_days, cleanup_group, group_id, status, binlog_on_off, delete_limit)
VALUES
    ('devclaude', NULL, 'dev_app', 'trx',
     'trx_date < DATE_ADD(CURDATE(), INTERVAL -RETENSION DAY)',
     300, 'daily_cleanup', 1, 1, 1, 1000);
```
**Result**: Delete from `dev_app.trx` where `trx_date < DATE_ADD(CURDATE(), INTERVAL -300 DAY)` in batches of 1000, with replication enabled.

### Example 2: Orders Table without Replication
```sql
INSERT INTO c_sup_cleanup_config
    (login_path, oracle_tns_name, db_schema, table_name, where_condition,
     retension_days, cleanup_group, group_id, status, binlog_on_off, delete_limit)
VALUES
    ('devclaude', NULL, 'dev_app', 'p_orders',
     'order_date < DATE_ADD(CURDATE(), INTERVAL -RETENSION DAY)',
     180, 'daily_cleanup', 1, 1, 0, 500);
```
**Result**: Delete from `dev_app.p_orders` where `order_date < DATE_ADD(CURDATE(), INTERVAL -180 DAY)` in batches of 500, WITHOUT replication (binlog disabled).

### Example 3: Complex WHERE Condition
```sql
INSERT INTO c_sup_cleanup_config
    (login_path, oracle_tns_name, db_schema, table_name, where_condition,
     retension_days, cleanup_group, group_id, status, binlog_on_off, delete_limit)
VALUES
    ('devclaude', NULL, 'dev_app', 'audit_logs',
     'log_date < DATE_ADD(CURDATE(), INTERVAL -RETENSION DAY) AND log_level = ''DEBUG'' AND archived = 1',
     90, 'daily_cleanup', 2, 1, 1, 2000);
```
**Result**: Delete archived debug logs older than 90 days.

### Example 4: Inactive Configuration
```sql
INSERT INTO c_sup_cleanup_config
    (login_path, oracle_tns_name, db_schema, table_name, where_condition,
     retension_days, cleanup_group, group_id, status, binlog_on_off, delete_limit)
VALUES
    ('devclaude', NULL, 'dev_app', 'temp_data',
     'created_date < DATE_ADD(CURDATE(), INTERVAL -RETENSION DAY)',
     7, 'daily_cleanup', 1, 0, 1, 500);
```
**Result**: This configuration is INACTIVE (status=0) and will be skipped by the cleanup script.

## Query Examples

### View All Active Configurations
```sql
SELECT
    config_id,
    db_schema,
    table_name,
    retension_days,
    cleanup_group,
    group_id,
    CASE status WHEN 1 THEN 'ACTIVE' WHEN 0 THEN 'INACTIVE' END as status_desc,
    CASE binlog_on_off WHEN 1 THEN 'REPLICATE' WHEN 0 THEN 'NO REPLICATE' END as binlog_desc,
    delete_limit
FROM c_sup_cleanup_config
WHERE status = 1
ORDER BY group_id, config_id;
```

### View Configurations by Group ID
```sql
SELECT
    config_id,
    login_path,
    db_schema,
    table_name,
    where_condition,
    retension_days,
    delete_limit,
    binlog_on_off
FROM c_sup_cleanup_config
WHERE group_id = 1
  AND status = 1
ORDER BY config_id;
```

### View Configurations by Cleanup Group Name
```sql
SELECT
    config_id,
    db_schema,
    table_name,
    retension_days,
    last_run_at
FROM c_sup_cleanup_config
WHERE cleanup_group = 'daily_cleanup'
  AND status = 1
ORDER BY last_run_at;
```

### Check Last Run Times
```sql
SELECT
    config_id,
    db_schema,
    table_name,
    cleanup_group,
    last_run_at,
    TIMESTAMPDIFF(HOUR, last_run_at, NOW()) as hours_since_last_run
FROM c_sup_cleanup_config
WHERE status = 1
ORDER BY last_run_at DESC;
```

## How the Cleanup Script Uses This Configuration

### Step 1: Read cleanup.cfg
The script reads the configuration file to get:
- `login_path`: Which login path to use for connecting to the config database
- `config_database`: Database name where `c_sup_cleanup_config` table exists

### Step 2: Query Configuration Table
```sql
SELECT
    config_id,
    login_path,
    db_schema,
    table_name,
    where_condition,
    retension_days,
    binlog_on_off,
    delete_limit
FROM c_sup_cleanup_config
WHERE group_id = ?
  AND status = 1
ORDER BY config_id;
```

### Step 3: Build DELETE Statement
For each configuration:
1. Replace `RETENSION` keyword with `retension_days` value
2. Build final DELETE statement

Example transformation:
```
where_condition: "trx_date < DATE_ADD(CURDATE(), INTERVAL -RETENSION DAY)"
retension_days: 300

Final DELETE:
DELETE FROM dev_app.trx
WHERE trx_date < DATE_ADD(CURDATE(), INTERVAL -300 DAY)
LIMIT 1000;
```

### Step 4: Execute Delete with Binlog Control
```sql
-- If binlog_on_off = 0
SET sql_log_bin = 0;

-- Execute delete in loop
DELETE FROM dev_app.trx
WHERE trx_date < DATE_ADD(CURDATE(), INTERVAL -300 DAY)
LIMIT 1000;

-- Repeat until affected rows = 0
```

### Step 5: Update Last Run Timestamp
```sql
UPDATE c_sup_cleanup_config
SET last_run_at = NOW()
WHERE config_id = ?;
```

## Important Notes

### RETENSION Keyword
- **MUST** be uppercase: `RETENSION`
- **Case-sensitive** replacement
- Can appear multiple times in `where_condition`
- Will be replaced with the `retension_days` value

### Binary Log Control (binlog_on_off)
- **binlog_on_off = 1**: Deletes replicate to all slaves (default, safest)
- **binlog_on_off = 0**: Deletes do NOT replicate
  - Use when you want to clean up master but not slaves
  - Use when slaves are read-only and don't need the cleanup
  - Requires `SUPER` privilege to execute `SET sql_log_bin=0`

### Status Flag
- Use `status = 0` to temporarily disable a cleanup
- Configuration remains in the table for future use
- Can be re-enabled by setting `status = 1`

### Group Management
- **group_id**: Numeric identifier for batch processing
- **cleanup_group**: Descriptive name for organization
- Use `group_id` for script execution (e.g., run all group_id=1 together)
- Use `cleanup_group` for human-readable organization

### Delete Limits
- Start with conservative values (500-1000)
- Monitor performance and lock contention
- Adjust based on table size, indexes, and workload
- Smaller batches = less lock time but slower overall
- Larger batches = faster but longer locks

### Unique Constraint
- **UNIQUE KEY**: (db_schema, table_name, cleanup_group)
- Cannot have duplicate entries for same table and group
- Allows multiple cleanup configs for same table with different groups

## Maintenance Queries

### Disable All Cleanups for a Database
```sql
UPDATE c_sup_cleanup_config
SET status = 0
WHERE db_schema = 'dev_app';
```

### Enable Specific Cleanup
```sql
UPDATE c_sup_cleanup_config
SET status = 1
WHERE config_id = 1;
```

### Change Retention Period
```sql
UPDATE c_sup_cleanup_config
SET retension_days = 365
WHERE db_schema = 'dev_app'
  AND table_name = 'trx';
```

### Disable Replication for All Group 1 Cleanups
```sql
UPDATE c_sup_cleanup_config
SET binlog_on_off = 0
WHERE group_id = 1;
```

### View Configuration History
```sql
SELECT
    config_id,
    db_schema,
    table_name,
    created_at,
    updated_at,
    last_run_at
FROM c_sup_cleanup_config
ORDER BY updated_at DESC;
```

## Troubleshooting

### Issue: Cleanup Not Running
**Check**: Is status = 1?
```sql
SELECT config_id, db_schema, table_name, status
FROM c_sup_cleanup_config
WHERE config_id = ?;
```

### Issue: Deletes Replicating When They Shouldn't
**Check**: Is binlog_on_off = 0?
```sql
SELECT config_id, binlog_on_off
FROM c_sup_cleanup_config
WHERE config_id = ?;
```

### Issue: DELETE Statement Syntax Error
**Check**: WHERE condition syntax
```sql
SELECT config_id, where_condition, retension_days
FROM c_sup_cleanup_config
WHERE config_id = ?;
```
Verify that RETENSION keyword is spelled correctly and replacement makes valid SQL.

### Issue: No Rows Being Deleted
**Check**: Does the WHERE condition match any rows?
```sql
-- Test the condition manually
SELECT COUNT(*)
FROM dev_app.trx
WHERE trx_date < DATE_ADD(CURDATE(), INTERVAL -300 DAY);
```

## Environment Differences

| Environment | Config Database | Login Path Example |
|-------------|----------------|-------------------|
| Development | dev_support | devclaude |
| QA | qa_support or support | qa_app_user |
| Production | support | prod_app_user |

Update the `cleanup.cfg` file for each environment to point to the correct database and login path.

## Related Files
- **cleanup.cfg**: Main configuration file with login_path and config_database
- **dev_support_schema.sql**: DDL to create the configuration table
- **dev_support_insert.sql**: Sample configuration data
- **cleanup_script.py**: Main cleanup script that reads this configuration

---
**Last Updated**: 2026-01-18
**Version**: 1.0
