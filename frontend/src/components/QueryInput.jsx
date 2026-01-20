import { useState } from 'react';

const QueryInput = ({ onQuery, isLoading }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onQuery(query.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="query-input-form">
      <div className="input-container">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question about VASP..."
          disabled={isLoading}
          className="query-input"
        />
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className="query-button"
        >
          {isLoading ? 'Searching...' : 'Ask'}
        </button>
      </div>
    </form>
  );
};

export default QueryInput;
