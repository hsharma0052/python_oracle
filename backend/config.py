import os
import sys
from dotenv import load_dotenv
import logging
import platform
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
logger.debug("Loading environment variables from .env file")
load_dotenv()
logger.debug("Environment variables loaded")

def get_default_oracle_client_path():
    """Get the default Oracle client path based on the platform."""
    system = platform.system().lower()
    if system == 'windows':
        # Common Windows Oracle client paths
        possible_paths = [
            r'C:\oracle\instantclient_21_3',
            r'C:\oracle\instantclient_19_19',
            r'C:\instantclient_21_3',
            r'C:\instantclient'
        ]
        # Check if any of these paths exist
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return possible_paths[0]  # Return first path as default if none found
    elif system == 'darwin':  # macOS
        return '/opt/oracle/instantclient_23_3'
    else:  # Linux
        return '/opt/oracle/instantclient_23_3'

def setup_oracle_client():
    """Setup Oracle client based on platform."""
    try:
        import cx_Oracle
        
        # Get client path from environment or default
        client_path = os.getenv('ORACLE_CLIENT_PATH', get_default_oracle_client_path())
        client_path = str(Path(client_path))  # Normalize path for current OS
        
        if not os.path.exists(client_path):
            error_msg = (
                f"Oracle client not found at {client_path}. "
                f"Please install Oracle Instant Client and set ORACLE_CLIENT_PATH "
                f"environment variable to its location."
            )
            logger.error(error_msg)
            raise Exception(error_msg)
        
        system = platform.system().lower()
        if system == 'windows':
            # Add Oracle client to PATH for Windows
            if client_path not in os.environ['PATH']:
                os.environ['PATH'] = f"{client_path};{os.environ['PATH']}"
        elif system == 'darwin':  # macOS
            os.environ['DYLD_LIBRARY_PATH'] = client_path
        else:  # Linux
            os.environ['LD_LIBRARY_PATH'] = client_path
        
        # Initialize Oracle client
        cx_Oracle.init_oracle_client(lib_dir=client_path)
        logger.info(f"Successfully initialized Oracle client at {client_path}")
        
    except ImportError:
        error_msg = (
            "cx_Oracle module not found. "
            "Please install it using: pip install cx_Oracle"
        )
        logger.error(error_msg)
        raise
    except Exception as e:
        logger.error(f"Failed to initialize Oracle client: {str(e)}")
        raise

# Initialize Oracle client
setup_oracle_client()

# Database configurations
class Config:
    # Common configurations
    ORACLE_CLIENT_PATH = os.getenv('ORACLE_CLIENT_PATH', 
                                 'C:\\instantclient_21_3' if os.name == 'nt' 
                                 else '/opt/oracle/instantclient_23_3')
    
    # Environment-specific configurations
    class Development:
        DEBUG = True
        INFORMATICA_DB_URL = os.getenv('DEV_INFORMATICA_DB_URL')
        PYTHON_ETL_DB_URL = os.getenv('DEV_PYTHON_ETL_DB_URL')

    class Production:
        DEBUG = False
        INFORMATICA_DB_URL = os.getenv('PROD_INFORMATICA_DB_URL')
        PYTHON_ETL_DB_URL = os.getenv('PROD_PYTHON_ETL_DB_URL')

    class Testing:
        TESTING = True
        INFORMATICA_DB_URL = os.getenv('TEST_INFORMATICA_DB_URL')
        PYTHON_ETL_DB_URL = os.getenv('TEST_PYTHON_ETL_DB_URL')

    # Database configurations
    INFORMATICA_DB_CONFIG = {
        'dev': {
            'user': os.getenv('DEV_INFORMATICA_DB_USER'),
            'password': os.getenv('DEV_INFORMATICA_DB_PASSWORD'),
            'host': os.getenv('DEV_INFORMATICA_DB_HOST'),
            'port': os.getenv('DEV_INFORMATICA_DB_PORT', '1521'),  # Default Oracle port
            'service_name': os.getenv('DEV_INFORMATICA_DB_SERVICE'),  # Oracle service name
            'sid': os.getenv('DEV_INFORMATICA_DB_SID'),  # Oracle SID
            'database': os.getenv('DEV_INFORMATICA_DB_NAME')
        },
        'qa': {
            'user': os.getenv('QA_INFORMATICA_DB_USER'),
            'password': os.getenv('QA_INFORMATICA_DB_PASSWORD'),
            'host': os.getenv('QA_INFORMATICA_DB_HOST'),
            'port': os.getenv('QA_INFORMATICA_DB_PORT', '1521'),
            'service_name': os.getenv('QA_INFORMATICA_DB_SERVICE'),
            'sid': os.getenv('QA_INFORMATICA_DB_SID'),
            'database': os.getenv('QA_INFORMATICA_DB_NAME')
        },
        'prod': {
            'user': os.getenv('PROD_INFORMATICA_DB_USER'),
            'password': os.getenv('PROD_INFORMATICA_DB_PASSWORD'),
            'host': os.getenv('PROD_INFORMATICA_DB_HOST'),
            'port': os.getenv('PROD_INFORMATICA_DB_PORT', '1521'),
            'service_name': os.getenv('PROD_INFORMATICA_DB_SERVICE'),
            'sid': os.getenv('PROD_INFORMATICA_DB_SID'),
            'database': os.getenv('PROD_INFORMATICA_DB_NAME')
        }
    }

    PYTHON_ETL_DB_CONFIG = {
        'dev': {
            'user': os.getenv('DEV_PYTHON_DB_USER'),
            'password': os.getenv('DEV_PYTHON_DB_PASSWORD'),
            'host': os.getenv('DEV_PYTHON_DB_HOST'),
            'port': os.getenv('DEV_PYTHON_DB_PORT', '1521'),
            'service_name': os.getenv('DEV_PYTHON_DB_SERVICE'),
            'sid': os.getenv('DEV_PYTHON_DB_SID'),
            'database': os.getenv('DEV_PYTHON_DB_NAME')
        },
        'qa': {
            'user': os.getenv('QA_PYTHON_DB_USER'),
            'password': os.getenv('QA_PYTHON_DB_PASSWORD'),
            'host': os.getenv('QA_PYTHON_DB_HOST'),
            'port': os.getenv('QA_PYTHON_DB_PORT', '1521'),
            'service_name': os.getenv('QA_PYTHON_DB_SERVICE'),
            'sid': os.getenv('QA_PYTHON_DB_SID'),
            'database': os.getenv('QA_PYTHON_DB_NAME')
        },
        'prod': {
            'user': os.getenv('PROD_PYTHON_DB_USER'),
            'password': os.getenv('PROD_PYTHON_DB_PASSWORD'),
            'host': os.getenv('PROD_PYTHON_DB_HOST'),
            'port': os.getenv('PROD_PYTHON_DB_PORT', '1521'),
            'service_name': os.getenv('PROD_PYTHON_DB_SERVICE'),
            'sid': os.getenv('PROD_PYTHON_DB_SID'),
            'database': os.getenv('PROD_PYTHON_DB_NAME')
        }
    }

    # Log the loaded configurations (without passwords)
    logger.debug("Loaded database configurations:")
    for env in ['dev', 'qa', 'prod']:
        logger.debug(f"Environment {env}:")
        logger.debug(f"  Informatica DB: {INFORMATICA_DB_CONFIG[env]['host']}:{INFORMATICA_DB_CONFIG[env]['port']}/{INFORMATICA_DB_CONFIG[env]['database']}")
        logger.debug(f"  Python ETL DB: {PYTHON_ETL_DB_CONFIG[env]['host']}:{PYTHON_ETL_DB_CONFIG[env]['port']}/{PYTHON_ETL_DB_CONFIG[env]['database']}")

    # Category to table mapping
    TABLE_CATEGORIES = {
        'securities': [
            'security_master',
            'security_prices',
            'security_attributes'
        ],
        'positions': [
            'position_master',
            'position_details',
            'position_history'
        ],
        'reference': [
            'currency_rates',
            'country_codes',
            'market_data'
        ],
        'accounts': [
            'account_master',
            'account_details',
            'account_balances'
        ]
    }

    logger.debug(f"Loaded table categories: {list(TABLE_CATEGORIES.keys())}")

    # Enhanced error logging for database configurations
    @classmethod
    def validate_config(cls, env):
        """Validate database configuration for an environment."""
        missing_vars = []
        required_vars = {
            'INFORMATICA': ['USER', 'PASSWORD', 'HOST', 'PORT', 'SERVICE'],
            'PYTHON': ['USER', 'PASSWORD', 'HOST', 'PORT', 'SERVICE']
        }
        
        for db_type, params in required_vars.items():
            for param in params:
                env_var = f"{env}_{db_type}_DB_{param}"
                if not os.getenv(env_var):
                    missing_vars.append(env_var)
        
        if missing_vars:
            error_msg = (
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                f"Please check your .env file and ensure all required variables are set."
            )
            logger.error(error_msg)
            raise ValueError(error_msg) 