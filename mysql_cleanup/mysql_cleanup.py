#!/usr/bin/env python3
"""
MySQL Cleanup Script
Automated database cleanup based on configuration table.

This script connects to a configuration database, retrieves cleanup configurations,
and executes batch deletes on target tables based on retention policies.

Usage:
    python mysql_cleanup.py [--group-id GROUP_ID] [--config CONFIG_FILE] [--dry-run]
"""

import sys
import argparse
import configparser
import logging
import subprocess
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class MySQLConnection:
    """MySQL connection handler using mysql command-line client with login-path."""

    def __init__(self, login_path: str):
        """
        Initialize MySQL connection with login-path.

        Args:
            login_path: MySQL login path configured with mysql_config_editor
        """
        self.login_path = login_path
        logger.debug(f"Initialized MySQL connection with login-path: {login_path}")

    def execute_query(self, query: str, database: Optional[str] = None) -> List[Dict]:
        """
        Execute a SELECT query and return results as list of dictionaries.

        Args:
            query: SQL SELECT query to execute
            database: Optional database name to use

        Returns:
            List of dictionaries containing query results
        """
        cmd = ['mysql', f'--login-path={self.login_path}', '--batch', '--skip-column-names']

        if database:
            cmd.append(database)

        # Add query
        cmd.extend(['-e', query])

        logger.debug(f"Executing query: {query}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            if not result.stdout.strip():
                return []

            # Parse tab-separated output
            lines = result.stdout.strip().split('\n')

            # Get column names by executing DESCRIBE or using first row assumption
            # For simplicity, we'll return raw rows and handle in calling code
            rows = []
            for line in lines:
                rows.append(line.split('\t'))

            return rows

        except subprocess.CalledProcessError as e:
            logger.error(f"Query execution failed: {e.stderr}")
            raise

    def execute_query_with_columns(self, query: str, database: Optional[str] = None) -> Tuple[List[str], List[List]]:
        """
        Execute a SELECT query and return column names and results.

        Args:
            query: SQL SELECT query to execute
            database: Optional database name to use

        Returns:
            Tuple of (column_names, rows)
        """
        cmd = ['mysql', f'--login-path={self.login_path}', '--batch']

        if database:
            cmd.append(database)

        cmd.extend(['-e', query])

        logger.debug(f"Executing query with columns: {query}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            if not result.stdout.strip():
                return [], []

            lines = result.stdout.strip().split('\n')

            # First line is column names
            column_names = lines[0].split('\t')

            # Rest are data rows
            rows = []
            for line in lines[1:]:
                rows.append(line.split('\t'))

            return column_names, rows

        except subprocess.CalledProcessError as e:
            logger.error(f"Query execution failed: {e.stderr}")
            raise

    def execute_update(self, query: str, database: Optional[str] = None) -> int:
        """
        Execute an UPDATE/DELETE query and return affected rows.

        Args:
            query: SQL UPDATE/DELETE query to execute
            database: Optional database name to use

        Returns:
            Number of affected rows
        """
        cmd = ['mysql', f'--login-path={self.login_path}']

        if database:
            cmd.append(database)

        cmd.extend(['-e', query])

        logger.debug(f"Executing update: {query}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            # Parse affected rows from stderr (mysql outputs warnings/info to stderr)
            # We'll need to query ROW_COUNT() or parse output
            # For simplicity, return 0 and handle in calling code
            return 0

        except subprocess.CalledProcessError as e:
            logger.error(f"Update execution failed: {e.stderr}")
            raise

    def execute_batch_delete(self, delete_query: str, database: str,
                            binlog_on_off: int, max_iterations: int = 1000) -> int:
        """
        Execute DELETE query in batches until no more rows affected.

        Args:
            delete_query: DELETE query with LIMIT clause
            database: Database name
            binlog_on_off: 1=enable binlog, 0=disable binlog
            max_iterations: Maximum number of iterations to prevent infinite loops

        Returns:
            Total number of rows deleted
        """
        total_deleted = 0
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Build complete SQL with binlog control if needed
            if binlog_on_off == 0:
                full_query = f"SET sql_log_bin=0; {delete_query} SELECT ROW_COUNT() as affected_rows;"
            else:
                full_query = f"{delete_query} SELECT ROW_COUNT() as affected_rows;"

            cmd = ['mysql', f'--login-path={self.login_path}', database, '--batch', '-e', full_query]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )

                # Parse ROW_COUNT() output
                lines = result.stdout.strip().split('\n')
                affected_rows = 0

                # Look for affected_rows in output
                for line in lines:
                    if line and line.strip().isdigit():
                        affected_rows = int(line.strip())
                        break

                if affected_rows == 0:
                    logger.info(f"No more rows to delete. Total deleted: {total_deleted}")
                    break

                total_deleted += affected_rows
                logger.info(f"Iteration {iteration}: Deleted {affected_rows} rows (Total: {total_deleted})")

            except subprocess.CalledProcessError as e:
                logger.error(f"Delete execution failed: {e.stderr}")
                raise

        if iteration >= max_iterations:
            logger.warning(f"Reached maximum iterations ({max_iterations}). Total deleted: {total_deleted}")

        return total_deleted


class CleanupConfig:
    """Configuration data class for cleanup operations."""

    def __init__(self, config_dict: Dict):
        """Initialize from dictionary."""
        self.config_id = config_dict['config_id']
        self.login_path = config_dict['login_path']
        self.oracle_tns_name = config_dict['oracle_tns_name']
        self.db_schema = config_dict['db_schema']
        self.table_name = config_dict['table_name']
        self.where_condition = config_dict['where_condition']
        self.retension_days = config_dict['retension_days']
        self.cleanup_group = config_dict['cleanup_group']
        self.group_id = config_dict['group_id']
        self.status = config_dict['status']
        self.binlog_on_off = config_dict['binlog_on_off']
        self.delete_limit = config_dict['delete_limit']

    def build_delete_statement(self) -> str:
        """
        Build DELETE statement by replacing RETENSION keyword with retension_days.

        Returns:
            Complete DELETE statement with LIMIT clause
        """
        # Replace RETENSION keyword with actual retention days
        where_clause = self.where_condition.replace('RETENSION', str(self.retension_days))

        # Build complete DELETE statement
        delete_stmt = f"DELETE FROM {self.db_schema}.{self.table_name} WHERE {where_clause} LIMIT {self.delete_limit};"

        return delete_stmt

    def __str__(self):
        return f"CleanupConfig(id={self.config_id}, table={self.db_schema}.{self.table_name}, retention={self.retension_days}d)"


class MySQLCleanupScript:
    """Main cleanup script orchestrator."""

    def __init__(self, config_file: str = 'cleanup.cfg'):
        """
        Initialize cleanup script with configuration file.

        Args:
            config_file: Path to cleanup.cfg file
        """
        self.config_file = config_file
        self.config = self._read_config()
        self.config_db_connection = None

    def _read_config(self) -> configparser.ConfigParser:
        """Read and parse cleanup.cfg file."""
        config = configparser.ConfigParser()

        try:
            config.read(self.config_file)
            logger.info(f"Loaded configuration from: {self.config_file}")
            return config
        except Exception as e:
            logger.error(f"Failed to read config file {self.config_file}: {e}")
            sys.exit(1)

    def connect_to_config_db(self):
        """Establish connection to configuration database."""
        login_path = self.config.get('mysql', 'login_path')
        self.config_db_connection = MySQLConnection(login_path)
        logger.info(f"Connected to config database using login-path: {login_path}")

    def get_cleanup_configs(self, group_id: Optional[int] = None) -> List[CleanupConfig]:
        """
        Retrieve cleanup configurations from database.

        Args:
            group_id: Optional group ID filter

        Returns:
            List of CleanupConfig objects
        """
        config_database = self.config.get('database', 'config_database')
        config_table = self.config.get('database', 'config_table')

        # Build query based on group_id parameter
        if group_id is not None:
            where_clause = f"WHERE group_id = {group_id} AND status = 1 AND login_path IS NOT NULL"
            logger.info(f"Fetching cleanup configs for group_id: {group_id}")
        else:
            where_clause = "WHERE status = 1 AND login_path IS NOT NULL"
            logger.info("Fetching all active cleanup configs")

        query = f"""
            SELECT
                config_id,
                login_path,
                oracle_tns_name,
                db_schema,
                table_name,
                where_condition,
                retension_days,
                cleanup_group,
                group_id,
                status,
                binlog_on_off,
                delete_limit
            FROM {config_table}
            {where_clause}
            ORDER BY group_id, config_id
        """

        try:
            column_names, rows = self.config_db_connection.execute_query_with_columns(query, config_database)

            if not rows:
                logger.warning("No cleanup configurations found matching criteria")
                return []

            # Convert rows to CleanupConfig objects
            configs = []
            for row in rows:
                config_dict = dict(zip(column_names, row))

                # Convert numeric fields
                config_dict['config_id'] = int(config_dict['config_id'])
                config_dict['retension_days'] = int(config_dict['retension_days'])
                config_dict['group_id'] = int(config_dict['group_id'])
                config_dict['status'] = int(config_dict['status'])
                config_dict['binlog_on_off'] = int(config_dict['binlog_on_off'])
                config_dict['delete_limit'] = int(config_dict['delete_limit'])

                # Handle NULL oracle_tns_name
                if config_dict['oracle_tns_name'] == 'NULL' or config_dict['oracle_tns_name'] == '\\N':
                    config_dict['oracle_tns_name'] = None

                configs.append(CleanupConfig(config_dict))

            logger.info(f"Found {len(configs)} cleanup configuration(s)")
            return configs

        except Exception as e:
            logger.error(f"Failed to retrieve cleanup configs: {e}")
            raise

    def execute_cleanup(self, cleanup_config: CleanupConfig, dry_run: bool = False) -> int:
        """
        Execute cleanup for a single configuration.

        Args:
            cleanup_config: CleanupConfig object
            dry_run: If True, only log what would be deleted without executing

        Returns:
            Total number of rows deleted
        """
        logger.info(f"Processing: {cleanup_config}")

        # Build DELETE statement
        delete_stmt = cleanup_config.build_delete_statement()

        binlog_status = "DISABLED (No Replication)" if cleanup_config.binlog_on_off == 0 else "ENABLED (Replicate)"

        logger.info(f"  Database: {cleanup_config.db_schema}")
        logger.info(f"  Table: {cleanup_config.table_name}")
        logger.info(f"  Retention: {cleanup_config.retension_days} days")
        logger.info(f"  Batch Limit: {cleanup_config.delete_limit}")
        logger.info(f"  Binary Log: {binlog_status}")
        logger.info(f"  DELETE Statement: {delete_stmt}")

        if dry_run:
            logger.info("  [DRY RUN] Skipping actual deletion")
            return 0

        # Connect to target database
        target_conn = MySQLConnection(cleanup_config.login_path)

        try:
            # Execute batch delete
            total_deleted = target_conn.execute_batch_delete(
                delete_stmt,
                cleanup_config.db_schema,
                cleanup_config.binlog_on_off
            )

            logger.info(f"  Successfully deleted {total_deleted} row(s)")

            # Update last_run_at in config table
            self._update_last_run(cleanup_config.config_id)

            return total_deleted

        except Exception as e:
            logger.error(f"  Failed to execute cleanup: {e}")
            raise

    def _update_last_run(self, config_id: int):
        """Update last_run_at timestamp in configuration table."""
        config_database = self.config.get('database', 'config_database')
        config_table = self.config.get('database', 'config_table')

        update_query = f"""
            UPDATE {config_table}
            SET last_run_at = NOW()
            WHERE config_id = {config_id}
        """

        try:
            self.config_db_connection.execute_update(update_query, config_database)
            logger.debug(f"Updated last_run_at for config_id: {config_id}")
        except Exception as e:
            logger.warning(f"Failed to update last_run_at: {e}")

    def run(self, group_id: Optional[int] = None, dry_run: bool = False):
        """
        Main execution method.

        Args:
            group_id: Optional group ID filter
            dry_run: If True, simulate without executing deletes
        """
        logger.info("=" * 80)
        logger.info("MySQL Cleanup Script Started")
        logger.info("=" * 80)

        if dry_run:
            logger.info("*** DRY RUN MODE - No data will be deleted ***")

        # Connect to config database
        self.connect_to_config_db()

        # Get cleanup configurations
        configs = self.get_cleanup_configs(group_id)

        if not configs:
            logger.info("No cleanup tasks to execute")
            return

        # Execute cleanup for each configuration
        total_configs = len(configs)
        successful = 0
        failed = 0
        total_rows_deleted = 0

        for idx, config in enumerate(configs, 1):
            logger.info("")
            logger.info(f"[{idx}/{total_configs}] " + "=" * 70)

            try:
                rows_deleted = self.execute_cleanup(config, dry_run)
                total_rows_deleted += rows_deleted
                successful += 1
            except Exception as e:
                logger.error(f"Cleanup failed for config_id {config.config_id}: {e}")
                failed += 1

        # Summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("Cleanup Summary")
        logger.info("=" * 80)
        logger.info(f"Total Configurations: {total_configs}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Total Rows Deleted: {total_rows_deleted}")
        logger.info("=" * 80)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='MySQL Cleanup Script - Automated database cleanup based on retention policies',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run cleanup for all active configurations
  python mysql_cleanup.py

  # Run cleanup for specific group ID
  python mysql_cleanup.py --group-id 1

  # Dry run (no actual deletion)
  python mysql_cleanup.py --group-id 1 --dry-run

  # Use custom config file
  python mysql_cleanup.py --config /path/to/cleanup.cfg --group-id 1
        """
    )

    parser.add_argument(
        '--group-id',
        type=int,
        help='Group ID to filter cleanup configurations (optional, default: all active configs)'
    )

    parser.add_argument(
        '--config',
        type=str,
        default='cleanup.cfg',
        help='Path to cleanup configuration file (default: cleanup.cfg)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate cleanup without actually deleting data'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()

    # Set logging level
    if args.debug:
        logger.setLevel(logging.DEBUG)

    # Run cleanup script
    try:
        script = MySQLCleanupScript(config_file=args.config)
        script.run(group_id=args.group_id, dry_run=args.dry_run)
    except KeyboardInterrupt:
        logger.info("\nScript interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Script failed with error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
