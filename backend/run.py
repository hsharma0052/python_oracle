from flask import Flask, jsonify, request
from flask_cors import CORS
from app.comparison_utils import get_comparison_summary
import cx_Oracle
import os
from dotenv import load_dotenv
import logging
from contextlib import contextmanager
from typing import Dict, Optional, Generator
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Database configuration for different environments
DB_CONFIG = {
    'Development': {
        'informatica': {
            'user': os.getenv('DEV_INFORMATICA_USER', 'system'),
            'password': os.getenv('DEV_INFORMATICA_PASSWORD', 'oracle'),
            'dsn': os.getenv('DEV_INFORMATICA_DSN', 'localhost:1521/XE')
        },
        'python_etl': {
            'user': os.getenv('DEV_PYTHON_ETL_USER', 'system'),
            'password': os.getenv('DEV_PYTHON_ETL_PASSWORD', 'oracle'),
            'dsn': os.getenv('DEV_PYTHON_ETL_DSN', 'localhost:1521/XE')
        }
    },
    'Pre-Production': {
        'informatica': {
            'user': os.getenv('PREPROD_INFORMATICA_USER', 'system'),
            'password': os.getenv('PREPROD_INFORMATICA_PASSWORD', 'oracle'),
            'dsn': os.getenv('PREPROD_INFORMATICA_DSN', 'localhost:1521/XE')
        },
        'python_etl': {
            'user': os.getenv('PREPROD_PYTHON_ETL_USER', 'system'),
            'password': os.getenv('PREPROD_PYTHON_ETL_PASSWORD', 'oracle'),
            'dsn': os.getenv('PREPROD_PYTHON_ETL_DSN', 'localhost:1521/XE')
        }
    },
    'Production': {
        'informatica': {
            'user': os.getenv('PROD_INFORMATICA_USER', 'system'),
            'password': os.getenv('PROD_INFORMATICA_PASSWORD', 'oracle'),
            'dsn': os.getenv('PROD_INFORMATICA_DSN', 'localhost:1521/XE')
        },
        'python_etl': {
            'user': os.getenv('PROD_PYTHON_ETL_USER', 'system'),
            'password': os.getenv('PROD_PYTHON_ETL_PASSWORD', 'oracle'),
            'dsn': os.getenv('PROD_PYTHON_ETL_DSN', 'localhost:1521/XE')
        }
    }
}

# Connection pools for different environments and sources
connection_pools: Dict[str, Dict[str, Optional[cx_Oracle.SessionPool]]] = {
    env: {'informatica': None, 'python_etl': None} 
    for env in ['Development', 'Pre-Production', 'Production']
}

def init_connection_pool(environment: str, source: str) -> None:
    """Initialize connection pool for specific environment and source."""
    try:
        config = DB_CONFIG[environment][source]
        min_connections = 2
        max_connections = 5
        increment = 1
        
        connection_pools[environment][source] = cx_Oracle.SessionPool(
            user=config['user'],
            password=config['password'],
            dsn=config['dsn'],
            min=min_connections,
            max=max_connections,
            increment=increment,
            encoding="UTF-8"
        )
        logger.info(f"Initialized connection pool for {environment} - {source}")
    except Exception as e:
        logger.error(f"Failed to initialize connection pool for {environment} - {source}: {str(e)}")
        raise

@contextmanager
def get_db_connection(environment: str, source: str) -> Generator[cx_Oracle.Connection, None, None]:
    """Get database connection from pool with automatic cleanup."""
    pool = connection_pools[environment][source]
    if pool is None:
        init_connection_pool(environment, source)
        pool = connection_pools[environment][source]
    
    connection = None
    try:
        connection = pool.acquire()
        yield connection
    except cx_Oracle.Error as e:
        error_obj, = e.args
        logger.error(f"Oracle Error: {error_obj.message} (Code: {error_obj.code})")
        raise
    except Exception as e:
        logger.error(f"Database connection error for {environment} - {source}: {str(e)}")
        raise
    finally:
        if connection:
            try:
                pool.release(connection)
            except Exception as e:
                logger.error(f"Error releasing connection: {str(e)}")

@app.route('/api/check-connections', methods=['GET'])
def check_connections():
    """Check database connections for both sources in the specified environment."""
    environment = request.headers.get('Environment')
    if not environment:
        return jsonify({'error': 'Environment not specified'}), 400

    status = {
        'informatica': False,
        'pythonEtl': False,
        'timestamp': time.time()
    }

    for source, status_key in [('informatica', 'informatica'), ('python_etl', 'pythonEtl')]:
        try:
            with get_db_connection(environment, source) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM DUAL")
                cursor.fetchone()
                status[status_key] = True
        except Exception as e:
            logger.error(f"{source.title()} connection error: {str(e)}")
            status[f"{status_key}Error"] = str(e)

    return jsonify(status)

@app.route('/api/tables', methods=['GET'])
def get_tables():
    """Get list of available tables filtered by category and environment."""
    try:
        environment = request.args.get('environment')
        category = request.args.get('category')

        if not environment or not category:
            return jsonify({'error': 'Environment and category are required'}), 400

        with get_db_connection(environment, 'informatica') as connection:
            cursor = connection.cursor()
            category_pattern = f"%{category.upper()}%"
            
            # Get tables based on category with metadata
            cursor.execute("""
                SELECT 
                    t.table_name,
                    t.num_rows,
                    t.last_analyzed,
                    c.comments
                FROM user_tables t
                LEFT JOIN user_tab_comments c ON t.table_name = c.table_name
                WHERE t.table_name LIKE 'INFORMATICA_%'
                AND t.table_name LIKE :category
                AND EXISTS (
                    SELECT 1 
                    FROM user_tables 
                    WHERE table_name = REPLACE(t.table_name, 'INFORMATICA_', 'PYTHON_')
                )
                ORDER BY t.table_name
            """, category=category_pattern)
            
            tables = [{
                'name': row[0].split('_', 1)[1],
                'rowCount': row[1],
                'lastAnalyzed': row[2].isoformat() if row[2] else None,
                'description': row[3]
            } for row in cursor.fetchall()]
            
            return jsonify(tables)
    except Exception as e:
        logger.error(f"Error fetching tables: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/compare/batch', methods=['POST'])
def compare_batch():
    """Compare multiple tables between Informatica and Python ETL sources."""
    try:
        data = request.get_json()
        tables = data.get('tables', [])
        environment = data.get('environment')
        
        if not tables:
            return jsonify({'error': 'No tables specified'}), 400
        
        if not environment:
            return jsonify({'error': 'Environment not specified'}), 400
        
        results = {}
        total_tables = len(tables)
        processed = 0
        
        for table in tables:
            try:
                comparison = get_comparison_summary(table, environment)
                results[table] = {
                    **comparison,
                    'progress': (processed + 1) / total_tables * 100
                }
                processed += 1
            except Exception as e:
                logger.error(f"Error comparing table {table}: {str(e)}")
                results[table] = {
                    'error': str(e),
                    'progress': (processed + 1) / total_tables * 100
                }
                processed += 1
        
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error in batch comparison: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize connection pools for all environments
    for env in connection_pools:
        for source in connection_pools[env]:
            try:
                init_connection_pool(env, source)
            except Exception as e:
                logger.error(f"Failed to initialize pool for {env} - {source}: {str(e)}")
    
    app.run(debug=True) 