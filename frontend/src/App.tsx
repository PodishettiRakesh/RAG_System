import React from 'react';
import './App.css';
import DocumentUpload from './components/DocumentUpload';
import { UploadResponse } from './services/api';

function App() {
  const handleUploadSuccess = (response: UploadResponse) => {
    console.log('Document uploaded successfully:', response);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <h1 className="text-3xl font-bold text-gray-900">RAG System</h1>
              <span className="ml-3 px-3 py-1 text-xs font-medium text-blue-600 bg-blue-100 rounded-full">
                Production-Oriented
              </span>
            </div>
            <div className="text-sm text-gray-500">
              Retrieval-Augmented Generation with Evaluation & Observability
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          <div className="text-center">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Document Ingestion
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Upload your text documents to create searchable chunks for the RAG system. 
              Each document will be processed and stored with semantic embeddings.
            </p>
          </div>

          <DocumentUpload onUploadSuccess={handleUploadSuccess} />
        </div>
      </main>
    </div>
  );
}

export default App;
