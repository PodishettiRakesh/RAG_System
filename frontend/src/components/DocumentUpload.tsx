import React, { useState, useCallback } from 'react';
import { apiService, UploadResponse } from '../services/api';

interface DocumentUploadProps {
  onUploadSuccess?: (response: UploadResponse) => void;
}

const DocumentUpload: React.FC<DocumentUploadProps> = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [textFile, setTextFile] = useState<File | null>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    const txtFile = files.find(file => file.type === 'text/plain' || file.name.endsWith('.txt'));
    
    if (txtFile) {
      handleFileSelect(txtFile);
    } else {
      setError('Please upload a .txt file');
    }
  }, []);

  const handleFileSelect = (file: File) => {
    setTextFile(file);
    setError(null);
    setUploadResult(null);
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const readFileContent = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        resolve(content);
      };
      reader.onerror = reject;
      reader.readAsText(file);
    });
  };

  const handleUpload = async () => {
    if (!textFile) return;

    setIsUploading(true);
    setError(null);

    try {
      const content = await readFileContent(textFile);
      const response = await apiService.uploadDocument(content);
      
      if (response.success && response.data) {
        setUploadResult(response.data);
        onUploadSuccess?.(response.data);
      } else {
        setError(response.error || 'Upload failed');
      }
    } catch (err) {
      setError('Failed to upload document');
    } finally {
      setIsUploading(false);
    }
  };

  const resetUpload = () => {
    setTextFile(null);
    setUploadResult(null);
    setError(null);
  };

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-lg font-semibold text-text-primary">Upload Documents</h3>
        <p className="text-sm text-text-secondary mt-1">Drag and drop or browse to upload text files</p>
      </div>
      
      {/* File Drop Zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-all duration-200 shadow-card ${
          isDragging
            ? 'border-primary-500 bg-card-light shadow-purple-glow'
            : 'border-card-border bg-card hover:border-primary-400 hover:bg-card-hover'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="flex flex-col items-center space-y-3">
          <div className="text-text-secondary">
            <svg
              className="h-8 w-8"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>
          
          <div>
            <p className="text-sm text-text-primary">
              {isDragging ? 'Drop your file here' : 'Drag and drop your .txt file here'}
            </p>
            <p className="text-xs text-text-secondary mt-1">or</p>
          </div>
          
          <label className="cursor-pointer">
            <span className="inline-block px-3 py-1.5 bg-primary-600 text-white text-sm rounded-md hover:bg-primary-700 transition-all duration-200 shadow-card hover:shadow-card-hover">
              Browse Files
            </span>
            <input
              type="file"
              className="hidden"
              accept=".txt,text/plain"
              onChange={handleFileInputChange}
            />
          </label>
        </div>
      </div>

      {/* Selected File Info */}
      {textFile && (
        <div className="p-4 bg-card-light rounded-lg border border-card-border shadow-card">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-primary-100 rounded flex items-center justify-center">
                <svg className="w-4 h-4 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-text-primary">{textFile.name}</p>
                <p className="text-xs text-text-secondary">
                  {(textFile.size / 1024).toFixed(2)} KB
                </p>
              </div>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={handleUpload}
                disabled={isUploading}
                className="px-3 py-1.5 bg-primary-600 text-white text-sm rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-card hover:shadow-card-hover"
              >
                {isUploading ? 'Uploading...' : 'Upload'}
              </button>
              <button
                onClick={resetUpload}
                disabled={isUploading}
                className="px-3 py-1.5 bg-card-hover text-text-primary text-sm rounded-md hover:bg-card-border disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-card"
              >
                Clear
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Upload Progress */}
      {isUploading && (
        <div className="p-4 bg-card-light rounded-lg border border-primary-500 shadow-purple-glow">
          <div className="flex items-center justify-center space-x-3">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-600"></div>
            <span className="text-sm text-primary-400">Processing document and creating chunks...</span>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-900/20 rounded-lg border border-red-500/30 shadow-card">
          <div className="flex items-center space-x-2">
            <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm text-red-400">{error}</p>
          </div>
        </div>
      )}

      {/* Upload Success */}
      {uploadResult && (
        <div className="p-4 bg-success-900/20 rounded-lg border border-success-500/30 shadow-card">
          <div className="flex items-center space-x-2 mb-3">
            <svg className="w-5 h-5 text-success-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-sm font-semibold text-success-400">Upload Successful!</h3>
          </div>
          <div className="space-y-1 text-xs text-success-300">
            <p>📄 Total words: {uploadResult.total_words}</p>
            <p>🧩 Chunks created: {uploadResult.total_chunks}</p>
            <p>✅ {uploadResult.message}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentUpload;
