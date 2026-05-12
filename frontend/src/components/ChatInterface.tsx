import React, { useState, useRef, useEffect } from 'react';
import { apiService, RAGRequest, RAGResponse } from '../services/api';
import RetrievedChunks from './RetrievedChunks';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: {
    contextUsed?: number;
    tokensUsed?: number;
    retrievedChunks?: any[];
    modelInfo?: any;
  };
}

interface ChatInterfaceProps {
  className?: string;
  onRetrievedChunks?: (chunks: any[]) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ className = '', onRetrievedChunks }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentRetrievedChunks, setCurrentRetrievedChunks] = useState<any[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const generateMessageId = () => {
    return `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: generateMessageId(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setError(null);
    setIsLoading(true);

    try {
      const request: RAGRequest = {
        query: userMessage.content,
        k: 3,
        max_length: 200,
      };

      const response = await apiService.ragQuery(request);
      
      if (response.success && response.data) {
        // Store retrieved chunks and pass to parent
        const retrievedChunks = response.data.retrieved_chunks || [];
        setCurrentRetrievedChunks(retrievedChunks);
        if (onRetrievedChunks) {
          onRetrievedChunks(retrievedChunks);
        }
        
        const assistantMessage: Message = {
          id: generateMessageId(),
          type: 'assistant',
          content: response.data.response,
          timestamp: new Date(),
          metadata: {
            contextUsed: response.data.context_used,
            tokensUsed: response.data.tokens_used,
            retrievedChunks: response.data.retrieved_chunks,
            modelInfo: response.data.model_info,
          },
        };

        setMessages(prev => [...prev, assistantMessage]);
      } else {
        setError(response.error || 'Failed to get response from RAG system');
      }
    } catch (err) {
      setError('Failed to send message. Please try again.');
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError(null);
  };

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className={`bg-card h-full flex flex-col ${className}`}>
      {/* Header */}
      <div className="border-b border-card-border px-6 py-4 flex-shrink-0 bg-card-light">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse"></div>
            <h3 className="text-lg font-semibold text-text-primary">Chat Interface</h3>
          </div>
          <button
            onClick={clearChat}
            className="px-3 py-1 text-sm text-text-secondary hover:text-text-primary hover:bg-card-hover rounded-md transition-all duration-200 shadow-card"
          >
            Clear Chat
          </button>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 scrollbar-dark">
        {messages.length === 0 && (
          <div className="text-center text-text-secondary py-8">
            <div className="mb-4">
              <svg
                className="mx-auto h-12 w-12 text-text-muted"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                />
              </svg>
            </div>
            <p className="text-lg font-medium text-text-primary">Start a conversation</p>
            <p className="text-sm text-text-secondary mt-1">
              Ask questions about your uploaded documents
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-start' : 'justify-end'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg shadow-card ${
                message.type === 'user'
                  ? 'bg-card-light text-text-primary border border-card-border'
                  : 'bg-primary-600 text-white'
              }`}
            >
              <div className="whitespace-pre-wrap break-words">
                {message.content}
              </div>
              
              {/* Metadata for assistant messages */}
              {message.type === 'assistant' && message.metadata && (
                <div className={`mt-2 text-xs text-primary-200`}>
                  <div className="flex items-center space-x-4">
                    {message.metadata.contextUsed && (
                      <span>Context: {message.metadata.contextUsed} chunks</span>
                    )}
                    {message.metadata.tokensUsed && (
                      <span>Tokens: {message.metadata.tokensUsed}</span>
                    )}
                  </div>
                  {message.metadata.modelInfo && (
                    <div className="mt-1">
                      Model: {message.metadata.modelInfo.model}
                    </div>
                  )}
                </div>
              )}
              
              <div className={`text-xs mt-1 ${
                message.type === 'user' ? 'text-text-muted' : 'text-primary-200'
              }`}>
                {formatTimestamp(message.timestamp)}
              </div>
            </div>
          </div>
        ))}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-card-light text-text-primary px-4 py-3 rounded-lg max-w-xs lg:max-w-md border border-card-border shadow-card">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-600"></div>
                <span className="text-sm">Thinking...</span>
              </div>
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="flex justify-center">
            <div className="bg-red-900/20 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg max-w-md shadow-card">
              <p className="text-sm">{error}</p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="border-t border-card-border px-6 py-4 flex-shrink-0 bg-card-light">
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="relative">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your documents..."
              className="w-full px-4 py-3 bg-card border border-card-border rounded-lg resize-none focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none text-text-primary placeholder-text-text-muted"
              rows={2}
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || isLoading}
              className="absolute bottom-3 right-3 px-3 py-1.5 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-card hover:shadow-card-hover"
            >
              {isLoading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              )}
            </button>
          </div>
          <div className="text-xs text-text-muted">
            Press Enter to send, Shift+Enter for new line
          </div>
        </form>
      </div>

          </div>
  );
};

export default ChatInterface;
