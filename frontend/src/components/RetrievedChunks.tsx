import React from 'react';

interface RetrievedChunk {
  rank: number;
  chunk_id: number;
  chunk_text: string;
  similarity_score: number;
  distance_type: string;
}

interface RetrievedChunksProps {
  chunks: RetrievedChunk[];
  className?: string;
}

const RetrievedChunks: React.FC<RetrievedChunksProps> = ({ chunks, className = '' }) => {
  const getScoreColor = (score: number) => {
    if (score < 0.5) return 'text-success-600 bg-success-50';
    if (score < 1.0) return 'text-accent-600 bg-accent-50';
    return 'text-gray-600 bg-gray-50';
  };

  const getScoreLabel = (score: number) => {
    if (score < 0.5) return 'High';
    if (score < 1.0) return 'Medium';
    return 'Low';
  };

  if (!chunks || chunks.length === 0) {
    return (
      <div className={`bg-card rounded-lg border border-card-border shadow-card ${className}`}>
        <div className="p-4">
          <h3 className="text-sm font-semibold text-text-primary mb-3">Retrieved Chunks</h3>
          <div className="text-center text-text-secondary py-6">
            <svg
              className="mx-auto h-8 w-8 text-text-muted mb-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <p className="text-sm text-text-primary">No chunks retrieved yet</p>
            <p className="text-xs text-text-muted mt-1">Ask a question to see relevant chunks</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-card rounded-lg border border-card-border shadow-card ${className}`}>
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-text-primary">Retrieved Chunks</h3>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-success-500 rounded-full"></div>
            <span className="text-xs text-text-secondary">{chunks.length} chunks found</span>
          </div>
        </div>
        
        <div className="space-y-3 max-h-64 overflow-y-auto">
          {chunks.map((chunk) => (
            <div
              key={chunk.chunk_id}
              className="border border-card-border bg-card-light rounded-lg p-3 hover:bg-card-hover hover:shadow-card-hover transition-all duration-200"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-medium text-text-secondary">#{chunk.rank}</span>
                  <span className="text-xs text-text-muted">ID: {chunk.chunk_id}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={`px-2 py-1 rounded-full text-xs font-medium ${getScoreColor(chunk.similarity_score)}`}>
                    {getScoreLabel(chunk.similarity_score)}
                  </div>
                  <span className="text-xs text-text-secondary">
                    {chunk.similarity_score.toFixed(2)}
                  </span>
                </div>
              </div>
              
              <div className="text-sm text-text-primary leading-relaxed mb-2">
                {chunk.chunk_text.length > 150 
                  ? `${chunk.chunk_text.substring(0, 150)}...`
                  : chunk.chunk_text
                }
              </div>
              
              <div className="flex items-center justify-between text-xs text-text-muted">
                <span>{chunk.distance_type}</span>
                <div className="flex items-center space-x-4">
                  <span>Words: {chunk.chunk_text.split(' ').length}</span>
                  <span>Chars: {chunk.chunk_text.length}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {/* Summary Stats */}
        <div className="mt-4 pt-3 border-t border-card-border">
          <div className="grid grid-cols-3 gap-2 text-center">
            <div>
              <p className="text-xs text-text-muted">Avg Distance</p>
              <p className="text-sm font-medium text-text-primary">
                {(chunks.reduce((sum, chunk) => sum + chunk.similarity_score, 0) / chunks.length).toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-xs text-text-muted">Min Distance</p>
              <p className="text-sm font-medium text-success-400">
                {Math.min(...chunks.map(c => c.similarity_score)).toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-xs text-text-muted">Max Distance</p>
              <p className="text-sm font-medium text-primary-400">
                {Math.max(...chunks.map(c => c.similarity_score)).toFixed(2)}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RetrievedChunks;
