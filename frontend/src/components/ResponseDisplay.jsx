import ReactMarkdown from 'react-markdown';

const ResponseDisplay = ({ response, isLoading }) => {
  if (isLoading) {
    return (
      <div className="response-container loading">
        <div className="spinner"></div>
        <p>Searching the VASP Wiki and generating response...</p>
      </div>
    );
  }

  if (!response) {
    return (
      <div className="response-container empty">
        <p>Enter a question above to get started.</p>
      </div>
    );
  }

  return (
    <div className="response-container">
      <div className="answer-section">
        <h2>Answer</h2>
        <div className="answer-content">
          <ReactMarkdown>{response.answer}</ReactMarkdown>
        </div>
        {response.retrieval_time && (
          <p className="metadata">
            Generated in {response.retrieval_time.toFixed(2)} seconds
          </p>
        )}
      </div>
    </div>
  );
};

export default ResponseDisplay;
