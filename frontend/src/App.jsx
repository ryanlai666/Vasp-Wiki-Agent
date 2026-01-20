import { useState, useEffect } from 'react';
import QueryInput from './components/QueryInput';
import ResponseDisplay from './components/ResponseDisplay';
import CitationList from './components/CitationList';
import { queryAPI, healthCheck } from './services/api';
import './App.css';

function App() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [healthStatus, setHealthStatus] = useState(null);

  useEffect(() => {
    // Check health on mount
    healthCheck()
      .then((data) => {
        setHealthStatus(data);
        if (data.status !== 'healthy') {
          setError('RAG agent is not ready. Please ensure the index is built.');
        }
      })
      .catch((err) => {
        setError('Cannot connect to backend. Is the server running?');
        console.error('Health check failed:', err);
      });
  }, []);

  const handleQuery = async (queryText) => {
    setQuery(queryText);
    setError(null);
    setIsLoading(true);
    setResponse(null);

    try {
      const data = await queryAPI(queryText);
      setResponse(data);
    } catch (err) {
      setError(err.message || 'An error occurred while processing your query');
      console.error('Query error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>VASP Wiki RAG Agent</h1>
        <p className="subtitle">
          Ask questions about VASP (Vienna Ab initio Simulation Package)
        </p>
        {healthStatus && (
          <div className={`health-status ${healthStatus.status}`}>
            {healthStatus.status === 'healthy' ? '✓' : '⚠'} {healthStatus.message}
            {healthStatus.vector_store_stats && (
              <span className="stats">
                ({healthStatus.vector_store_stats.num_documents} documents indexed)
              </span>
            )}
          </div>
        )}
      </header>

      <main className="app-main">
        <QueryInput onQuery={handleQuery} isLoading={isLoading} />

        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        <ResponseDisplay response={response} isLoading={isLoading} />

        {response && response.sources && (
          <CitationList sources={response.sources} />
        )}
      </main>

      <footer className="app-footer">
        <p>
          Powered by Gemini 2.5 Flash API | VASP Wiki Documentation
        </p>
      </footer>
    </div>
  );
}

export default App;
