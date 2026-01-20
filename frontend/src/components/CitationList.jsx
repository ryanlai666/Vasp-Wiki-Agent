const CitationList = ({ sources }) => {
  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div className="citations-section">
      <h3>Sources ({sources.length})</h3>
      <div className="citations-list">
        {sources.map((source, index) => (
          <div key={index} className="citation-item">
            <div className="citation-header">
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="citation-link"
              >
                {source.title}
                {source.heading && ` - ${source.heading}`}
              </a>
              <span className="similarity-score">
                {(source.similarity * 100).toFixed(1)}% match
              </span>
            </div>
            <p className="citation-snippet">{source.snippet}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CitationList;
