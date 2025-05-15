# Data Migration Validation Tool

A comprehensive tool for validating data migration from Informatica to Python ETL pipelines. This tool provides a web-based interface for comparing database schemas and data between source (Informatica) and target (Python ETL) Oracle databases.

## Features

- Real-time database connection status monitoring
- Multi-environment support (Development, QA, Production)
- Category-based table filtering
- Multi-table selection and comparison
- Detailed schema comparison (columns, data types, nullability)
- Row-by-row data comparison with difference reporting
- Progress tracking for batch operations
- Cross-platform compatibility (Windows, macOS, Linux)

## Prerequisites

- Python 3.8 or higher
- Node.js 14.x or higher
- Oracle Instant Client (version 21.3 or higher)
- Access to source and target Oracle databases

### Oracle Instant Client Setup

#### Windows
1. Download Oracle Instant Client Basic Package from Oracle's website
2. Extract to `C:\instantclient_21_3` (or your preferred location)
3. Add the path to your system's PATH environment variable
4. Set `ORACLE_CLIENT_PATH` environment variable to the client directory

#### macOS
1. Download Oracle Instant Client Basic Package for macOS
2. Extract to `/opt/oracle/instantclient_23_3`
3. Set environment variables:
   ```bash
   export ORACLE_HOME=/opt/oracle/instantclient_23_3
   export PATH=$ORACLE_HOME:$PATH
   export DYLD_LIBRARY_PATH=$ORACLE_HOME:$DYLD_LIBRARY_PATH
   ```

#### Linux
1. Download Oracle Instant Client Basic Package for Linux
2. Extract to `/opt/oracle/instantclient_23_3`
3. Set environment variables:
   ```bash
   export ORACLE_HOME=/opt/oracle/instantclient_23_3
   export PATH=$ORACLE_HOME:$PATH
   export LD_LIBRARY_PATH=$ORACLE_HOME:$LD_LIBRARY_PATH
   ```

## Windows-Specific Setup

1. Install Oracle Instant Client:
   - Download Oracle Instant Client Basic Package (64-bit) from Oracle's website
   - Extract to `C:\oracle\instantclient_21_3` or another location
   - Add the path to your system's PATH environment variable
   - Set `ORACLE_CLIENT_PATH` environment variable to the client directory

2. Install Python Dependencies:
   ```cmd
   cd backend
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements_windows.txt
   ```

3. Configure Environment:
   - Copy `.env.template` to `.env`
   - Update database credentials
   - Ensure Oracle client path is correct
   - Example `.env` for Windows:
   ```env
   ORACLE_CLIENT_PATH=C:\oracle\instantclient_21_3
   
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
   ```

4. Start the Application:
   ```cmd
   # Terminal 1 (Backend)
   cd backend
   venv\Scripts\activate
   python run.py
   
   # Terminal 2 (Frontend)
   cd frontend
   npm install
   npm start
   ```

## Configuration

Create a `.env` file in the backend directory with the following variables:

```env
# Development Environment
DEV_INFORMATICA_DB_USER=user
DEV_INFORMATICA_DB_PASSWORD=password
DEV_INFORMATICA_DB_HOST=host
DEV_INFORMATICA_DB_PORT=1521
DEV_INFORMATICA_DB_SERVICE=service_name
DEV_INFORMATICA_DB_SID=sid

DEV_PYTHON_DB_USER=user
DEV_PYTHON_DB_PASSWORD=password
DEV_PYTHON_DB_HOST=host
DEV_PYTHON_DB_PORT=1521
DEV_PYTHON_DB_SERVICE=service_name
DEV_PYTHON_DB_SID=sid

# QA Environment (Similar structure)
QA_INFORMATICA_DB_USER=user
...

# Production Environment (Similar structure)
PROD_INFORMATICA_DB_USER=user
...

# Oracle Client Configuration
ORACLE_CLIENT_PATH=/path/to/oracle/client
```

## Running the Application

1. Start the backend server:
   ```bash
   cd backend
   python run.py
   ```

2. Start the frontend development server:
   ```bash
   cd frontend
   npm start
   ```

3. Access the application at `http://localhost:3000`

## Usage

1. Select the environment (Development, QA, Production)
2. Choose a category (Security, Position, Account, Reference)
3. Select one or more tables for comparison
4. View the comparison results:
   - Schema differences
   - Row count discrepancies
   - Data content differences
   - Detailed error reports

## Testing

Run the test suite:
```bash
cd backend
python -m pytest test_*.py
```

## Troubleshooting

### Common Issues

1. Oracle Client Not Found
   - Verify Oracle Instant Client installation
   - Check environment variables (ORACLE_HOME, PATH)
   - Ensure client version matches system architecture

2. Database Connection Failed
   - Verify database credentials in .env file
   - Check network connectivity
   - Ensure database service/SID is correct

3. Port Conflicts
   - Default ports: Backend (5000), Frontend (3000)
   - Change ports in configuration if needed

## Troubleshooting Windows Issues

1. Oracle Client Not Found:
   - Verify Oracle Instant Client is installed
   - Check PATH environment variable includes client directory
   - Ensure ORACLE_CLIENT_PATH points to correct location
   - Try running as Administrator if permission issues occur

2. Database Connection Failed:
   - Check Windows Firewall settings
   - Verify TNS_ADMIN environment variable if using wallet
   - Test connection using SQL*Plus from command line
   - Check Windows Event Viewer for Oracle-related errors

3. Port Conflicts:
   - Check if ports 5000 (backend) or 3000 (frontend) are in use
   - Use `netstat -ano | findstr "5000"` to find conflicting processes
   - Kill process or change port in configuration

4. Python Environment Issues:
   - Use `python -m pip install --upgrade pip` to update pip
   - Try `pip install --no-cache-dir -r requirements_windows.txt`
   - Check Python version compatibility (3.8+ required)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 