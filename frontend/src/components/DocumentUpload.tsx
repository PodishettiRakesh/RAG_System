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
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Document Upload</h2>
      
      {/* File Drop Zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="flex flex-col items-center space-y-4">
          <div className="text-gray-500">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
              aria-hidden="true"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>
          
          <div>
            <p className="text-lg text-gray-600">
              {isDragging ? 'Drop your file here' : 'Drag and drop your .txt file here'}
            </p>
            <p className="text-sm text-gray-500 mt-1">or</p>
          </div>
          
          <label className="cursor-pointer">
            <span className="mt-2 inline-block px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
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
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-800">{textFile.name}</p>
              <p className="text-sm text-gray-500">
                {(textFile.size / 1024).toFixed(2)} KB
              </p>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={handleUpload}
                disabled={isUploading}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isUploading ? 'Uploading...' : 'Upload'}
              </button>
              <button
                onClick={resetUpload}
                disabled={isUploading}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Clear
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Upload Progress */}
      {isUploading && (
        <div className="mt-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Processing document and creating chunks...</span>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {/* Upload Success */}
      {uploadResult && (
        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <h3 className="font-semibold text-green-800 mb-2">Upload Successful!</h3>
          <div className="space-y-1 text-sm text-green-700">
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
