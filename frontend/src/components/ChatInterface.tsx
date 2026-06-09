import React, { useState, useRef, useEffect, useCallback } from 'react';
import { apiService, RAGRequest } from '../services/api';

type PipelineStage =
  | 'idle'
  | 'retrieving'
  | 'generating'
  | 'evaluating'
  | 'done'
  | 'error';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  metadata?: {
    contextUsed?: number;
    tokensUsed?: number;
    retrievedChunks?: any[];
    modelInfo?: any;
    totalLatencyMs?: number;
    hallucinationDetected?: boolean;
    groundingScore?: number;
    confidenceLabel?: string;
  };
}

interface ChatInterfaceProps {
  className?: string;
  onRetrievedChunks?: (chunks: any[]) => void;
}

const PIPELINE_LABELS: Record<PipelineStage, string> = {
  idle: '',
  retrieving: 'Searching documents...',
  generating: 'Generating answer...',
  evaluating: 'Evaluating grounding...',
  done: '',
  error: '',
};

const SESSION_STORAGE_KEY = 'rag_session_id';

const ChatInterface: React.FC<ChatInterfaceProps> = ({ className = '', onRetrievedChunks }) => {
  const [sessionId, setSessionId] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [pipelineStage, setPipelineStage] = useState<PipelineStage>('idle');
  const [pipelineDetail, setPipelineDetail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const streamingMessageIdRef = useRef<string | null>(null);
  const shouldAutoScrollRef = useRef(true);

  useEffect(() => {
    const initializeSession = async () => {
      const existingSessionId = localStorage.getItem(SESSION_STORAGE_KEY);
      if (existingSessionId) {
        setSessionId(existingSessionId);
        const historyResponse = await apiService.getSessionHistory(existingSessionId);
        if (historyResponse.success && historyResponse.data) {
          setMessages(
            historyResponse.data.map((item) => ({
              id: item.message_id,
              type: item.role === 'assistant' ? 'assistant' : 'user',
              content: item.content,
              timestamp: new Date(item.timestamp),
              isStreaming: false,
            }))
          );
        }
        return;
      }

      const response = await apiService.getSessionId();
      if (response.success && response.data) {
        localStorage.setItem(SESSION_STORAGE_KEY, response.data);
        setSessionId(response.data);
        const historyResponse = await apiService.getSessionHistory(response.data);
        if (historyResponse.success && historyResponse.data) {
          setMessages(
            historyResponse.data.map((item) => ({
              id: item.message_id,
              type: item.role === 'assistant' ? 'assistant' : 'user',
              content: item.content,
              timestamp: new Date(item.timestamp),
              isStreaming: false,
            }))
          );
        }
      } else {
        console.error('Unable to obtain session ID:', response.error);
        setError('Unable to initialize session. Please refresh.');
      }
    };

    initializeSession();
  }, []);

  useEffect(() => {
    if (!sessionId) return;
  }, [messages, sessionId]);

  const isNearBottom = useCallback(() => {
    const el = messagesContainerRef.current;
    if (!el) return true;
    const threshold = 80;
    return el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
  }, []);

  const scrollChatToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    const el = messagesContainerRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior });
  }, []);

  useEffect(() => {
    if (shouldAutoScrollRef.current || isNearBottom()) {
      scrollChatToBottom(messages.length <= 2 ? 'auto' : 'smooth');
    }
  }, [messages, scrollChatToBottom, isNearBottom]);

  const generateMessageId = () => {
    return `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  };

  const updateStreamingMessage = useCallback(
    (updater: (msg: Message) => Message) => {
      const id = streamingMessageIdRef.current;
      if (!id) return;
      setMessages((prev) =>
        prev.map((m) => (m.id === id ? updater(m) : m))
      );
    },
    []
  );

  const handleStop = () => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setIsStreaming(false);
    setPipelineStage('idle');
    setPipelineDetail('');
    updateStreamingMessage((m) => ({
      ...m,
      isStreaming: false,
      content: m.content || '(Generation stopped)',
    }));
    streamingMessageIdRef.current = null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!inputValue.trim() || isStreaming) return;

    const userMessage: Message = {
      id: generateMessageId(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    const assistantId = generateMessageId();
    streamingMessageIdRef.current = assistantId;

    const assistantPlaceholder: Message = {
      id: assistantId,
      type: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMessage, assistantPlaceholder]);
    setInputValue('');
    setError(null);
    setIsStreaming(true);
    setPipelineStage('retrieving');
    setPipelineDetail('');
    shouldAutoScrollRef.current = true;

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    let currentSessionId = sessionId;
    if (!currentSessionId) {
      const sessionResponse = await apiService.getSessionId();
      if (sessionResponse.success && sessionResponse.data) {
        currentSessionId = sessionResponse.data;
        localStorage.setItem(SESSION_STORAGE_KEY, currentSessionId);
        setSessionId(currentSessionId);
      } else {
        setError('Unable to obtain session ID. Please try again.');
        setIsStreaming(false);
        return;
      }
    }

    const request: RAGRequest = {
      query: userMessage.content,
      k: 3,
      max_length: 200,
      session_id: currentSessionId,
    };

    try {
      await apiService.streamRagQuery(
        request,
        {
          onEvent: (event) => {
            switch (event.type) {
              case 'retrieval_started':
                setPipelineStage('retrieving');
                setPipelineDetail('');
                break;
              case 'retrieval_completed': {
                const chunks = (event.data.chunks as any[]) || [];
                const count = (event.data.count as number) || chunks.length;
                setPipelineDetail(`${count} chunk${count !== 1 ? 's' : ''} retrieved`);
                if (onRetrievedChunks) {
                  onRetrievedChunks(chunks);
                }
                updateStreamingMessage((m) => ({
                  ...m,
                  metadata: { ...m.metadata, retrievedChunks: chunks, contextUsed: count },
                }));
                break;
              }
              case 'generation_started':
                setPipelineStage('generating');
                break;
              case 'evaluation_complete':
                setPipelineStage('evaluating');
                updateStreamingMessage((m) => ({
                  ...m,
                  metadata: {
                    ...m.metadata,
                    hallucinationDetected: event.data.hallucination_detected as boolean,
                    groundingScore: event.data.grounding_score as number,
                    confidenceLabel: event.data.confidence_label as string,
                  },
                }));
                break;
              default:
                break;
            }
          },
          onToken: (text) => {
            updateStreamingMessage((m) => ({
              ...m,
              content: m.content + text,
            }));
          },
          onComplete: (data) => {
            setPipelineStage('done');
            setPipelineDetail('');
            updateStreamingMessage((m) => ({
              ...m,
              isStreaming: false,
              content: (data.response as string) || m.content,
              metadata: {
                ...m.metadata,
                tokensUsed: data.tokens_used as number,
                totalLatencyMs: Math.round(((data.total_latency_ms as number) / 1000) * 10) / 10,
                modelInfo: data.model_info,
                contextUsed: (data.context_used as number) || m.metadata?.contextUsed,
              },
            }));
          },
          onError: (message) => {
            setPipelineStage('error');
            setError(message);
            updateStreamingMessage((m) => ({
              ...m,
              isStreaming: false,
              content: m.content || `Error: ${message}`,
            }));
          },
        },
        abortController.signal
      );
    } catch {
      if (!abortController.signal.aborted) {
        setError('Failed to send message. Please try again.');
      }
    } finally {
      setIsStreaming(false);
      setPipelineStage('idle');
      setPipelineDetail('');
      streamingMessageIdRef.current = null;
      abortControllerRef.current = null;
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e as React.FormEvent);
    }
  };

  const clearChat = () => {
    if (isStreaming) {
      handleStop();
    }
    setMessages([]);
    setError(null);
    setPipelineStage('idle');
    setPipelineDetail('');
    if (sessionId) {
      apiService.clearSession(sessionId).catch(() => {
        console.error('Failed to clear session history');
      });
    }
  };

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const showPipelineStatus =
    isStreaming && pipelineStage !== 'idle' && pipelineStage !== 'done';

  return (
    <div className={`bg-card h-full flex flex-col ${className}`}>
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

      <div
        ref={messagesContainerRef}
        onScroll={() => {
          shouldAutoScrollRef.current = isNearBottom();
        }}
        className="flex-1 overflow-y-auto px-6 py-4 space-y-4 scrollbar-dark"
      >
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
            <div className="max-w-xs lg:max-w-md flex flex-col items-end space-y-1">
              {message.type === 'assistant' &&
                message.isStreaming &&
                showPipelineStatus &&
                streamingMessageIdRef.current === message.id && (
                  <div className="text-xs text-text-secondary px-1 flex items-center gap-2">
                    <span className="inline-block w-1.5 h-1.5 rounded-full bg-primary-500 animate-pulse" />
                    <span>{PIPELINE_LABELS[pipelineStage]}</span>
                    {pipelineDetail && (
                      <span className="text-text-muted">({pipelineDetail})</span>
                    )}
                  </div>
                )}

              <div
                className={`w-full px-4 py-3 rounded-lg shadow-card ${
                  message.type === 'user'
                    ? 'bg-card-light text-text-primary border border-card-border'
                    : 'bg-primary-600 text-white'
                }`}
              >
                <div className="whitespace-pre-wrap break-words">
                  {message.content}
                  {message.isStreaming && (
                    <span className="inline-block w-0.5 h-4 ml-0.5 bg-white animate-pulse align-middle" />
                  )}
                </div>

                {message.type === 'assistant' && message.metadata && !message.isStreaming && (
                  <div className="mt-2 text-xs text-primary-200 space-y-1">
                    <div className="flex flex-wrap items-center gap-3">
                      {message.metadata.contextUsed != null && (
                        <span>Context: {message.metadata.contextUsed} chunks</span>
                      )}
                      {message.metadata.tokensUsed != null && (
                        <span>Tokens: {message.metadata.tokensUsed}</span>
                      )}
                      {message.metadata.totalLatencyMs != null && (
                        <span>{message.metadata.totalLatencyMs} s</span>
                      )}
                    </div>
                    {message.metadata.hallucinationDetected != null && (
                      <span
                        className={
                          message.metadata.hallucinationDetected
                            ? 'text-yellow-300'
                            : 'text-green-300'
                        }
                      >
                        {message.metadata.hallucinationDetected
                          ? 'Possible ungrounded content'
                          : 'Grounded in retrieved context'}
                        {message.metadata.groundingScore != null &&
                          ` (${(message.metadata.groundingScore * 100).toFixed(0)}%)`}
                      </span>
                    )}
                    {message.metadata.modelInfo && (
                      <div>Model: {message.metadata.modelInfo.model}</div>
                    )}
                  </div>
                )}

                <div
                  className={`text-xs mt-1 ${
                    message.type === 'user' ? 'text-text-muted' : 'text-primary-200'
                  }`}
                >
                  {formatTimestamp(message.timestamp)}
                </div>
              </div>
            </div>
          </div>
        ))}

        {error && (
          <div className="flex justify-center">
            <div className="bg-red-900/20 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg max-w-md shadow-card">
              <p className="text-sm">{error}</p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

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
              disabled={isStreaming}
            />
            {isStreaming ? (
              <button
                type="button"
                onClick={handleStop}
                className="absolute bottom-3 right-3 px-3 py-1.5 bg-red-600 text-white rounded-md hover:bg-red-700 transition-all duration-200 shadow-card text-xs font-medium"
              >
                Stop
              </button>
            ) : (
              <button
                type="submit"
                disabled={!inputValue.trim()}
                className="absolute bottom-3 right-3 px-3 py-1.5 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-card hover:shadow-card-hover"
              >
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
              </button>
            )}
          </div>
          <div className="text-xs text-text-muted">
            Press Enter to send, Shift+Enter for new line
            {isStreaming && ' · Streaming response'}
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
