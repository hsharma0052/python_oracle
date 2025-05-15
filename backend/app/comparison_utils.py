import cx_Oracle
from datetime import datetime
import logging
from typing import Dict, List, Any, Tuple

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get Oracle database connection."""
    try:
        username = "system"
        password = "oracle"
        host = "localhost"
        port = "1521"
        service = "XE"
        
        dsn = cx_Oracle.makedsn(host, port, service_name=service)
        connection = cx_Oracle.connect(username, password, dsn)
        return connection
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise

def compare_schemas(table_name: str) -> Dict[str, Any]:
    """Compare schema between Informatica and Python ETL tables."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get column information for both tables
        info_query = """
        SELECT column_name, data_type, data_length, nullable
        FROM user_tab_columns
        WHERE table_name = :table_name
        ORDER BY column_id
        """
        
        cursor.execute(info_query, table_name=f"INFORMATICA_{table_name.upper()}")
        info_columns = cursor.fetchall()
        
        cursor.execute(info_query, table_name=f"PYTHON_{table_name.upper()}")
        python_columns = cursor.fetchall()
        
        # Compare columns
        differences = {
            'missing_columns': [],
            'data_type_mismatches': [],
            'nullable_mismatches': []
        }
        
        info_cols = {col[0]: {'type': col[1], 'length': col[2], 'nullable': col[3]} for col in info_columns}
        python_cols = {col[0]: {'type': col[1], 'length': col[2], 'nullable': col[3]} for col in python_columns}
        
        # Check for missing columns
        for col in info_cols:
            if col not in python_cols:
                differences['missing_columns'].append({
                    'column': col,
                    'missing_in': 'PYTHON_ETL',
                    'details': info_cols[col]
                })
        
        for col in python_cols:
            if col not in info_cols:
                differences['missing_columns'].append({
                    'column': col,
                    'missing_in': 'INFORMATICA',
                    'details': python_cols[col]
                })
        
        # Check for data type and nullable mismatches
        for col in set(info_cols.keys()) & set(python_cols.keys()):
            if info_cols[col]['type'] != python_cols[col]['type'] or info_cols[col]['length'] != python_cols[col]['length']:
                differences['data_type_mismatches'].append({
                    'column': col,
                    'informatica': info_cols[col],
                    'python_etl': python_cols[col]
                })
            
            if info_cols[col]['nullable'] != python_cols[col]['nullable']:
                differences['nullable_mismatches'].append({
                    'column': col,
                    'informatica': info_cols[col]['nullable'],
                    'python_etl': python_cols[col]['nullable']
                })
        
        cursor.close()
        conn.close()
        
        return differences
    except Exception as e:
        logger.error(f"Error comparing schemas: {str(e)}")
        raise

def compare_data(table_name: str) -> Dict[str, Any]:
    """Compare data between Informatica and Python ETL tables."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get row counts
        count_query = "SELECT COUNT(*) FROM {}"
        cursor.execute(count_query.format(f"INFORMATICA_{table_name.upper()}"))
        info_count = cursor.fetchone()[0]
        
        cursor.execute(count_query.format(f"PYTHON_{table_name.upper()}"))
        python_count = cursor.fetchone()[0]
        
        # Compare actual data
        compare_query = f"""
        SELECT i.*, p.*
        FROM INFORMATICA_{table_name.upper()} i
        FULL OUTER JOIN PYTHON_{table_name.upper()} p
        ON i.security_id = p.security_id
        WHERE i.security_id IS NULL OR p.security_id IS NULL
        OR i.security_name != p.security_name
        OR i.security_type != p.security_type
        OR i.currency != p.currency
        """
        
        cursor.execute(compare_query)
        columns = [col[0].lower() for col in cursor.description]
        mismatches = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        differences = {
            'row_counts': {
                'informatica': info_count,
                'python_etl': python_count,
                'difference': info_count - python_count
            },
            'mismatches': mismatches
        }
        
        cursor.close()
        conn.close()
        
        return differences
    except Exception as e:
        logger.error(f"Error comparing data: {str(e)}")
        raise

def get_comparison_summary(table_name: str) -> Dict[str, Any]:
    """Get a complete comparison summary for a table."""
    try:
        schema_diff = compare_schemas(table_name)
        data_diff = compare_data(table_name)
        
        return {
            'table_name': table_name,
            'schema_comparison': schema_diff,
            'data_comparison': data_diff,
            'summary': {
                'has_schema_differences': any(len(diff) > 0 for diff in schema_diff.values()),
                'has_data_differences': data_diff['row_counts']['difference'] != 0 or len(data_diff['mismatches']) > 0,
                'total_differences': sum(len(diff) for diff in schema_diff.values()) + len(data_diff['mismatches'])
            }
        }
    except Exception as e:
        logger.error(f"Error getting comparison summary: {str(e)}")
        raise 