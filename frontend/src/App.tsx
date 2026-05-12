import React, { useState } from 'react';
import './App.css';
import DocumentUpload from './components/DocumentUpload';
import ChatInterface from './components/ChatInterface';
import RetrievedChunks from './components/RetrievedChunks';
import Metrics from './components/Metrics';
import { UploadResponse } from './services/api';

function App() {
  const [retrievedChunks, setRetrievedChunks] = useState<any[]>([]);

  const handleUploadSuccess = (response: UploadResponse) => {
    console.log('Document uploaded successfully:', response);
  };

  const handleRetrievedChunks = (chunks: any[]) => {
    setRetrievedChunks(chunks);
  };

  return (
    <div className="min-h-screen bg-gradient-dark">
      {/* Professional Header */}
      <header className="bg-card border-b border-card-border shadow-card">
        <div className="max-w-full px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center shadow-purple-glow">
                  <span className="text-white font-bold text-sm">RAG</span>
                </div>
                <div>
                  <h1 className="text-xl font-bold text-text-primary">RAG System</h1>
                  <p className="text-xs text-text-secondary">Production-Oriented</p>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2 text-sm text-text-secondary">
                <div className="w-2 h-2 bg-success-500 rounded-full"></div>
                <span>System Active</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="h-[calc(100vh-73px)]">
        <div className="h-full flex">
          {/* Left Panel - Document Upload */}
          <div className="w-1/4 border-r border-card-border bg-card">
            <div className="h-full flex flex-col">
              <div className="px-4 py-3 border-b border-card-border bg-card-light">
                <h2 className="text-sm font-semibold text-text-primary">Document Upload</h2>
                <p className="text-xs text-text-secondary mt-1">Upload and process text documents</p>
              </div>
              <div className="flex-1 overflow-auto p-4">
                <DocumentUpload onUploadSuccess={handleUploadSuccess} />
              </div>
            </div>
          </div>

          {/* Middle Panel - Chat Interface */}
          <div className="w-1/2 border-r border-card-border bg-card">
            <div className="h-full flex flex-col">
              <div className="px-6 py-4 border-b border-card-border bg-card-light">
                <h2 className="text-lg font-semibold text-text-primary">Chat Interface</h2>
                <p className="text-sm text-text-secondary mt-1">Ask questions about your documents</p>
              </div>
              <div className="flex-1 overflow-hidden">
                <ChatInterface 
                  className="h-full border-none rounded-none" 
                  onRetrievedChunks={handleRetrievedChunks}
                />
              </div>
            </div>
          </div>

          {/* Right Panel - Metrics */}
          <div className="w-1/4 bg-card">
            <div className="h-full flex flex-col">
              <div className="px-4 py-3 border-b border-card-border bg-card-light">
                <h2 className="text-sm font-semibold text-text-primary">System Metrics</h2>
                <p className="text-xs text-text-secondary mt-1">Real-time performance data</p>
              </div>
              <div className="flex-1 overflow-auto p-4">
                <Metrics />
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Retrieved Chunks Panel - Bottom of Layout */}
      {retrievedChunks.length > 0 && (
        <div className="border-t border-card-border bg-card-light px-6 py-4">
          <RetrievedChunks chunks={retrievedChunks} />
        </div>
      )}
    </div>
  );
}

export default App;
