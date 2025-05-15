import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [selectedEnvironment, setSelectedEnvironment] = useState('Development');
  const [selectedCategory, setSelectedCategory] = useState('Security');
  const [tables, setTables] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [informaticaConnected, setInformaticaConnected] = useState(false);
  const [pythonETLConnected, setPythonETLConnected] = useState(false);
  const [error, setError] = useState(null);
  const [comparisonResult, setComparisonResult] = useState(null);
  const [selectedTables, setSelectedTables] = useState([]);

  const environments = ['Development', 'QA', 'Production'];
  const categories = ['Security', 'Position', 'Account', 'Reference'];

  const checkConnections = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/check-connections');
      const data = await response.json();
      setInformaticaConnected(data.informatica_connected);
      setPythonETLConnected(data.python_etl_connected);
      setError(data.informatica_connected && data.python_etl_connected ? null : 'Failed to check database connections. Please verify both databases are accessible.');
    } catch (err) {
      setError('Failed to check database connections. Please verify both databases are accessible.');
      console.error('Error checking connections:', err);
    }
  };

  const fetchTablesByCategory = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`http://localhost:5000/api/tables?category=${selectedCategory}&environment=${selectedEnvironment}`);
      const data = await response.json();
      setTables(Array.isArray(data) ? data : []);
      setSelectedTables([]); // Reset selected tables when category changes
      setError(null);
    } catch (err) {
      setError('Failed to fetch tables');
      console.error('Error fetching tables:', err);
      setTables([]);
    } finally {
      setIsLoading(false);
    }
  };

  const compareData = async () => {
    if (selectedTables.length === 0) {
      setError('Please select at least one table to compare');
      return;
    }

    try {
      const promises = selectedTables.map(tableName => 
        fetch(`http://localhost:5000/api/compare/${selectedCategory.toLowerCase()}`)
          .then(res => res.json())
      );

      const results = await Promise.all(promises);
      const combinedResults = {
        summary: {
          row_counts: { informatica: 0, python: 0 },
          has_differences: false
        },
        schema_differences: {
          column_differences: [],
          primary_key_differences: null
        },
        data_differences: {
          missing_rows: [],
          value_mismatches: []
        }
      };

      results.forEach(result => {
        if (result.comparison) {
          // Update summary
          combinedResults.summary.has_differences = combinedResults.summary.has_differences || result.comparison.summary.has_differences;
          combinedResults.summary.row_counts.informatica += result.comparison.summary.row_counts.informatica;
          combinedResults.summary.row_counts.python += result.comparison.summary.row_counts.python;

          // Combine schema differences
          if (result.comparison.schema_differences?.column_differences) {
            combinedResults.schema_differences.column_differences.push(...result.comparison.schema_differences.column_differences);
          }

          // Combine data differences
          if (result.comparison.data_differences?.missing_rows) {
            combinedResults.data_differences.missing_rows.push(...result.comparison.data_differences.missing_rows);
          }
          if (result.comparison.data_differences?.value_mismatches) {
            combinedResults.data_differences.value_mismatches.push(...result.comparison.data_differences.value_mismatches);
          }
        }
      });

      setComparisonResult(combinedResults);
      setError(null);
    } catch (err) {
      setError('Failed to compare data');
      console.error('Error comparing data:', err);
    }
  };

  const handleTableSelect = (tableName) => {
    setSelectedTables(prev => {
      if (prev.includes(tableName)) {
        return prev.filter(t => t !== tableName);
      } else {
        return [...prev, tableName];
      }
    });
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedTables(tables.map(table => table.name));
    } else {
      setSelectedTables([]);
    }
  };

  useEffect(() => {
    checkConnections();
    const interval = setInterval(checkConnections, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    fetchTablesByCategory();
  }, [selectedCategory, selectedEnvironment]);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Data Migration Validation Tool</h1>
      </header>

      <div className="connection-status">
        <div className={`status-indicator ${informaticaConnected ? 'connected' : 'disconnected'}`}>
          Informatica DB: {informaticaConnected ? 'Connected' : 'Disconnected'}
        </div>
        <div className={`status-indicator ${pythonETLConnected ? 'connected' : 'disconnected'}`}>
          Python ETL DB: {pythonETLConnected ? 'Connected' : 'Disconnected'}
        </div>
      </div>

      {error && <div className="error-message">Error: {error}</div>}

      <div className="controls">
        <div className="control-group">
          <label>Environment:</label>
          <select value={selectedEnvironment} onChange={(e) => setSelectedEnvironment(e.target.value)}>
            {environments.map(env => (
              <option key={env} value={env}>{env}</option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Category:</label>
          <select value={selectedCategory} onChange={(e) => setSelectedCategory(e.target.value)}>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="tables-section">
        <h2>Tables</h2>
        {isLoading ? (
          <div className="loading">Loading tables...</div>
        ) : (
          <>
            <div className="select-all-container">
              <label>
                <input
                  type="checkbox"
                  checked={selectedTables.length === tables.length && tables.length > 0}
                  onChange={handleSelectAll}
                />
                Select All Tables
              </label>
            </div>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Select</th>
                  <th>Table Name</th>
                  <th>Source Count</th>
                  <th>Target Count</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {Array.isArray(tables) && tables.map((table, index) => (
                  <tr key={index}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selectedTables.includes(table.name)}
                        onChange={() => handleTableSelect(table.name)}
                      />
                    </td>
                    <td>{table.name}</td>
                    <td>{table.source_count}</td>
                    <td>{table.target_count}</td>
                    <td>{table.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {tables.length > 0 && (
              <div className="compare-button-container">
                <button 
                  onClick={compareData}
                  disabled={selectedTables.length === 0}
                  className={selectedTables.length === 0 ? 'disabled' : ''}
                >
                  Compare Selected Tables
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {comparisonResult && (
        <div className="comparison-results">
          <h2>Comparison Results</h2>
          
          {/* Summary Section */}
          <div className="comparison-section">
            <h3>Summary</h3>
            <div className="summary-grid">
              <div className={`status-card ${!comparisonResult.summary.has_differences ? 'success' : 'warning'}`}>
                <strong>Overall Status</strong>
                <span>{!comparisonResult.summary.has_differences ? 'No Differences Found' : 'Differences Detected'}</span>
              </div>
              <div className="status-card">
                <strong>Row Counts</strong>
                <div className="count-details">
                  <span>Informatica: {comparisonResult.summary.row_counts.informatica}</span>
                  <span>Python ETL: {comparisonResult.summary.row_counts.python}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Schema Differences */}
          {comparisonResult.schema_differences?.column_differences?.length > 0 && (
            <div className="comparison-section">
              <h3>Schema Differences</h3>
              <div className="differences-table">
                <table>
                  <thead>
                    <tr>
                      <th>Column</th>
                      <th>Issue</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparisonResult.schema_differences.column_differences.map((diff, idx) => (
                      <tr key={idx}>
                        <td>{diff.column}</td>
                        <td>{diff.issue}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Missing Rows */}
          {comparisonResult.data_differences?.missing_rows?.length > 0 && (
            <div className="comparison-section">
              <h3>Missing/Extra Rows</h3>
              <div className="differences-table">
                <table>
                  <thead>
                    <tr>
                      <th>Type</th>
                      <th>Row Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparisonResult.data_differences.missing_rows.map((diff, idx) => (
                      <tr key={idx}>
                        <td>{diff.type === 'missing_in_python' ? 'Missing in Python ETL' : 'Missing in Informatica'}</td>
                        <td>
                          <pre>{JSON.stringify(diff.row, null, 2)}</pre>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Value Mismatches */}
          {comparisonResult.data_differences?.value_mismatches?.length > 0 && (
            <div className="comparison-section">
              <h3>Value Mismatches</h3>
              <div className="differences-table">
                <table>
                  <thead>
                    <tr>
                      <th>Row ID</th>
                      <th>Column</th>
                      <th>Informatica Value</th>
                      <th>Python ETL Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {comparisonResult.data_differences.value_mismatches.map((diff, idx) => (
                      <tr key={idx}>
                        <td>{diff.row_index}</td>
                        <td>{diff.column}</td>
                        <td>{JSON.stringify(diff.informatica_value)}</td>
                        <td>{JSON.stringify(diff.python_value)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App; 