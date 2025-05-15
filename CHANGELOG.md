# Changelog

## [1.0.0] - 2025-05-15

### Added
- Real Oracle database integration replacing mock service
- Connection pooling for better performance
- Multi-table selection and comparison
- Progress tracking for batch operations
- Windows compatibility improvements
- Comprehensive logging system
- Environment-specific configurations
- Cross-platform Oracle client initialization

### Changed
- Moved from mock data to real Oracle database connections
- Enhanced error handling and reporting
- Improved database connection management
- Updated configuration validation
- Consolidated test files
- Reorganized project structure

### Removed
- `mock_db_service.py` - Replaced with real Oracle integration
- `app.py` - Functionality merged into run.py
- `start.py` - Redundant with run.py
- `schema.sql` - Schema now managed in Oracle databases
- `seed_data.sql` - Test data no longer needed
- `test_oracle.py` - Consolidated into new test suite
- `test_config.py` - Redundant tests removed
- Deployment scripts moved to separate repository

### Fixed
- Windows path handling issues
- Oracle client initialization on different platforms
- Connection pool management
- Error handling in database operations
- Cross-platform compatibility issues

## Setup Instructions

### Prerequisites Installation

1. Python Environment:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements_windows.txt

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Oracle Client Setup:
   ```bash
   # Windows
   - Download Oracle Instant Client Basic Package
   - Extract to C:\oracle\instantclient_21_3
   - Add to PATH
   - Set ORACLE_CLIENT_PATH environment variable

   # macOS
   - Download Oracle Instant Client
   - Extract to /opt/oracle/instantclient_23_3
   - Export environment variables:
     export ORACLE_HOME=/opt/oracle/instantclient_23_3
     export PATH=$ORACLE_HOME:$PATH
     export DYLD_LIBRARY_PATH=$ORACLE_HOME:$DYLD_LIBRARY_PATH

   # Linux
   - Download Oracle Instant Client
   - Extract to /opt/oracle/instantclient_23_3
   - Export environment variables:
     export ORACLE_HOME=/opt/oracle/instantclient_23_3
     export PATH=$ORACLE_HOME:$PATH
     export LD_LIBRARY_PATH=$ORACLE_HOME:$LD_LIBRARY_PATH
   ```

### Database Configuration

1. Create `.env` file:
   ```env
   # Oracle Client
   ORACLE_CLIENT_PATH=/path/to/oracle/client

   # Development Environment
   DEV_INFORMATICA_DB_USER=user
   DEV_INFORMATICA_DB_PASSWORD=password
   DEV_INFORMATICA_DB_HOST=host
   DEV_INFORMATICA_DB_PORT=1521
   DEV_INFORMATICA_DB_SERVICE=service_name

   DEV_PYTHON_DB_USER=user
   DEV_PYTHON_DB_PASSWORD=password
   DEV_PYTHON_DB_HOST=host
   DEV_PYTHON_DB_PORT=1521
   DEV_PYTHON_DB_SERVICE=service_name

   # Similar structure for QA and Production
   ```

### Running the Application

1. Backend:
   ```bash
   cd backend
   python run.py
   ```

2. Frontend:
   ```bash
   cd frontend
   npm install
   npm start
   ```

### Common Issues and Solutions

1. Oracle Client Not Found:
   - Verify installation path
   - Check environment variables
   - Ensure correct permissions

2. Database Connection Failed:
   - Verify credentials in .env
   - Check network connectivity
   - Validate service names

3. Port Conflicts:
   - Check if ports 5000/3000 are in use
   - Use different ports if needed
   - Kill conflicting processes

4. Python Environment Issues:
   - Update pip: python -m pip install --upgrade pip
   - Clear pip cache: pip install --no-cache-dir
   - Check Python version compatibility 