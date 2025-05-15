import unittest
import cx_Oracle
import os
from dotenv import load_dotenv
from config import Config, setup_oracle_client
from app.db_utils import get_db_connection
from app.comparison_utils import get_comparison_summary

# Load environment variables
load_dotenv()

class TestOracleIntegration(unittest.TestCase):
    """Test Oracle database integration and comparison functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        try:
            setup_oracle_client()
        except Exception as e:
            print(f"Failed to setup Oracle client: {e}")
            raise
        
        # Validate environment variables
        Config.validate_config('DEV')
    
    def setUp(self):
        """Set up test case."""
        self.environment = 'Development'
        self.category = 'Security'
    
    def test_oracle_connection(self):
        """Test Oracle database connections."""
        # Test Informatica connection
        with get_db_connection(self.environment, 'informatica') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)
        
        # Test Python ETL connection
        with get_db_connection(self.environment, 'python_etl') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)
    
    def test_table_metadata(self):
        """Test table metadata retrieval."""
        with get_db_connection(self.environment, 'informatica') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT table_name 
                FROM user_tables 
                WHERE table_name LIKE 'INFORMATICA_%'
                AND ROWNUM = 1
            """)
            result = cursor.fetchone()
            self.assertIsNotNone(result)
    
    def test_data_comparison(self):
        """Test data comparison functionality."""
        # Get a test table
        with get_db_connection(self.environment, 'informatica') as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT table_name 
                FROM user_tables 
                WHERE table_name LIKE 'INFORMATICA_%'
                AND ROWNUM = 1
            """)
            table = cursor.fetchone()[0].split('_', 1)[1]
            
            # Test comparison
            comparison = get_comparison_summary(table, self.environment)
            self.assertIsInstance(comparison, dict)
            self.assertIn('summary', comparison)
            self.assertIn('schema_differences', comparison)
            self.assertIn('data_differences', comparison)
    
    def test_connection_pool(self):
        """Test connection pool functionality."""
        from run import init_connection_pool, connection_pools
        
        # Initialize pools
        init_connection_pool(self.environment, 'informatica')
        init_connection_pool(self.environment, 'python_etl')
        
        # Verify pools exist
        self.assertIsNotNone(connection_pools[self.environment]['informatica'])
        self.assertIsNotNone(connection_pools[self.environment]['python_etl'])
        
        # Test getting connections from pool
        with get_db_connection(self.environment, 'informatica') as conn1:
            with get_db_connection(self.environment, 'informatica') as conn2:
                self.assertIsNotNone(conn1)
                self.assertIsNotNone(conn2)
                self.assertNotEqual(conn1, conn2)

if __name__ == '__main__':
    unittest.main() 