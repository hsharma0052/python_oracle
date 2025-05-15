import cx_Oracle
import pandas as pd
from sqlalchemy import create_engine, inspect, text
import sys
import os
import logging
from typing import Dict, List, Any, Tuple

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

class DatabaseComparator:
    def __init__(self, env):
        try:
            logger.debug(f"Initializing DatabaseComparator for environment: {env}")
            if env not in Config.INFORMATICA_DB_CONFIG:
                raise ValueError(f"Invalid environment: {env}")
            self.env = env
            self.info_config = Config.INFORMATICA_DB_CONFIG[env]
            self.python_config = Config.PYTHON_ETL_DB_CONFIG[env]
            logger.debug(f"Database configs loaded for {env}")
        except Exception as e:
            logger.error(f"Error initializing DatabaseComparator: {str(e)}", exc_info=True)
            raise
        
    def _get_connection(self, config):
        """Create an Oracle connection using cx_Oracle."""
        try:
            logger.debug(f"Attempting to connect to database: {config['database']}")
            # Create DSN using either service name or SID
            if config.get('service_name'):
                dsn = cx_Oracle.makedsn(
                    config['host'],
                    config['port'],
                    service_name=config['service_name']
                )
            else:
                dsn = cx_Oracle.makedsn(
                    config['host'],
                    config['port'],
                    sid=config['sid']
                )
            
            conn = cx_Oracle.connect(
                user=config['user'],
                password=config['password'],
                dsn=dsn
            )
            logger.debug("Database connection successful")
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}", exc_info=True)
            raise

    def _get_engine(self, config):
        """Create a SQLAlchemy engine for pandas."""
        try:
            logger.debug(f"Creating SQLAlchemy engine for database: {config['database']}")
            # Create Oracle connection string
            if config.get('service_name'):
                connection_string = f"oracle+cx_oracle://{config['user']}:{config['password']}@{config['host']}:{config['port']}/?service_name={config['service_name']}"
            else:
                connection_string = f"oracle+cx_oracle://{config['user']}:{config['password']}@{config['host']}:{config['port']}/?sid={config['sid']}"
            
            engine = create_engine(connection_string)
            logger.debug("SQLAlchemy engine created successfully")
            return engine
        except Exception as e:
            logger.error(f"Error creating SQLAlchemy engine: {str(e)}", exc_info=True)
            raise

    def _get_table_schema(self, engine, table_name: str) -> Dict[str, Any]:
        """Get detailed schema information for a table."""
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        primary_keys = inspector.get_pk_constraint(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)
        indexes = inspector.get_indexes(table_name)
        
        return {
            'columns': [
                {
                    'name': col['name'],
                    'type': str(col['type']),
                    'nullable': col['nullable'],
                    'default': str(col['default']) if col['default'] is not None else None
                }
                for col in columns
            ],
            'primary_keys': primary_keys.get('constrained_columns', []),
            'foreign_keys': [
                {
                    'constrained_columns': fk['constrained_columns'],
                    'referred_table': fk['referred_table'],
                    'referred_columns': fk['referred_columns']
                }
                for fk in foreign_keys
            ],
            'indexes': [
                {
                    'name': idx['name'],
                    'columns': idx['column_names'],
                    'unique': idx['unique']
                }
                for idx in indexes
            ]
        }

    def _compare_schemas(self, info_schema: Dict, python_schema: Dict) -> Dict[str, Any]:
        """Compare schemas between two tables."""
        differences = {
            'column_differences': [],
            'primary_key_differences': [],
            'foreign_key_differences': [],
            'index_differences': []
        }

        # Compare columns
        info_cols = {col['name']: col for col in info_schema['columns']}
        python_cols = {col['name']: col for col in python_schema['columns']}

        # Check for missing columns
        for col_name in set(info_cols.keys()) - set(python_cols.keys()):
            differences['column_differences'].append({
                'type': 'missing_in_python',
                'column': col_name,
                'details': info_cols[col_name]
            })
        for col_name in set(python_cols.keys()) - set(info_cols.keys()):
            differences['column_differences'].append({
                'type': 'missing_in_informatica',
                'column': col_name,
                'details': python_cols[col_name]
            })

        # Compare common columns
        for col_name in set(info_cols.keys()) & set(python_cols.keys()):
            info_col = info_cols[col_name]
            python_col = python_cols[col_name]
            if info_col != python_col:
                differences['column_differences'].append({
                    'type': 'different_definition',
                    'column': col_name,
                    'informatica': info_col,
                    'python': python_col
                })

        # Compare primary keys
        if info_schema['primary_keys'] != python_schema['primary_keys']:
            differences['primary_key_differences'] = {
                'informatica': info_schema['primary_keys'],
                'python': python_schema['primary_keys']
            }

        # Compare foreign keys
        info_fks = {tuple(fk['constrained_columns']): fk for fk in info_schema['foreign_keys']}
        python_fks = {tuple(fk['constrained_columns']): fk for fk in python_schema['foreign_keys']}
        
        for fk_key in set(info_fks.keys()) - set(python_fks.keys()):
            differences['foreign_key_differences'].append({
                'type': 'missing_in_python',
                'columns': fk_key,
                'details': info_fks[fk_key]
            })
        for fk_key in set(python_fks.keys()) - set(info_fks.keys()):
            differences['foreign_key_differences'].append({
                'type': 'missing_in_informatica',
                'columns': fk_key,
                'details': python_fks[fk_key]
            })

        # Compare indexes
        info_idx = {idx['name']: idx for idx in info_schema['indexes']}
        python_idx = {idx['name']: idx for idx in python_schema['indexes']}
        
        for idx_name in set(info_idx.keys()) - set(python_idx.keys()):
            differences['index_differences'].append({
                'type': 'missing_in_python',
                'index': idx_name,
                'details': info_idx[idx_name]
            })
        for idx_name in set(python_idx.keys()) - set(info_idx.keys()):
            differences['index_differences'].append({
                'type': 'missing_in_informatica',
                'index': idx_name,
                'details': python_idx[idx_name]
            })

        return differences

    def _compare_data(self, info_df: pd.DataFrame, python_df: pd.DataFrame) -> Dict[str, Any]:
        """Compare data between two dataframes."""
        differences = {
            'row_count_difference': len(info_df) - len(python_df),
            'missing_rows': [],
            'value_mismatches': []
        }

        # Convert DataFrames to dictionaries for easier comparison
        info_dict = info_df.to_dict('records')
        python_dict = python_df.to_dict('records')

        # Create sets of tuples for each row for efficient comparison
        info_rows = {tuple(sorted(row.items())) for row in info_dict}
        python_rows = {tuple(sorted(row.items())) for row in python_dict}

        # Find missing rows
        for row in info_rows - python_rows:
            differences['missing_rows'].append({
                'type': 'missing_in_python',
                'row': dict(row)
            })
        for row in python_rows - info_rows:
            differences['missing_rows'].append({
                'type': 'missing_in_informatica',
                'row': dict(row)
            })

        # Find value mismatches for common columns
        common_cols = set(info_df.columns) & set(python_df.columns)
        for col in common_cols:
            info_values = info_df[col].fillna('NULL').astype(str)
            python_values = python_df[col].fillna('NULL').astype(str)
            
            # Find rows where values differ
            mask = info_values != python_values
            if mask.any():
                for idx in mask[mask].index:
                    if idx in info_df.index and idx in python_df.index:
                        differences['value_mismatches'].append({
                            'column': col,
                            'row_index': idx,
                            'informatica_value': str(info_df.loc[idx, col]),
                            'python_value': str(python_df.loc[idx, col])
                        })

        return differences

    def compare_tables(self, table_name: str) -> Dict[str, Any]:
        """Compare data and schema between Informatica and Python ETL tables."""
        info_engine = self._get_engine(self.info_config)
        python_engine = self._get_engine(self.python_config)

        try:
            # Get schema information
            info_schema = self._get_table_schema(info_engine, table_name)
            python_schema = self._get_table_schema(python_engine, table_name)
            schema_differences = self._compare_schemas(info_schema, python_schema)

            # Get data from both tables
            info_df = pd.read_sql(f"SELECT * FROM {table_name}", info_engine)
            python_df = pd.read_sql(f"SELECT * FROM {table_name}", python_engine)
            data_differences = self._compare_data(info_df, python_df)

            # Prepare summary statistics
            summary = {
                'table_name': table_name,
                'row_counts': {
                    'informatica': len(info_df),
                    'python': len(python_df)
                },
                'column_counts': {
                    'informatica': len(info_df.columns),
                    'python': len(python_df.columns)
                },
                'has_schema_differences': any(
                    len(diff) > 0 for diff in schema_differences.values()
                ),
                'has_data_differences': (
                    data_differences['row_count_difference'] != 0 or
                    len(data_differences['missing_rows']) > 0 or
                    len(data_differences['value_mismatches']) > 0
                )
            }

            return {
                'summary': summary,
                'schema_differences': schema_differences,
                'data_differences': data_differences
            }

        finally:
            info_engine.dispose()
            python_engine.dispose()

    def get_category_tables(self, category):
        """Get all tables for a specific category."""
        return Config.TABLE_CATEGORIES.get(category, [])

    def compare_category(self, category):
        """Compare all tables in a category."""
        tables = self.get_category_tables(category)
        results = {}
        
        for table in tables:
            results[table] = self.compare_tables(table)
            
        return results

    @staticmethod
    def get_available_environments():
        """Get list of available environments."""
        try:
            logger.debug("Getting available environments")
            envs = list(Config.INFORMATICA_DB_CONFIG.keys())
            logger.debug(f"Available environments: {envs}")
            return envs
        except Exception as e:
            logger.error(f"Error getting available environments: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def get_available_categories():
        """Get list of available categories."""
        try:
            logger.debug("Getting available categories")
            cats = list(Config.TABLE_CATEGORIES.keys())
            logger.debug(f"Available categories: {cats}")
            return cats
        except Exception as e:
            logger.error(f"Error getting available categories: {str(e)}", exc_info=True)
            raise 