const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface UploadResponse {
  total_words: number;
  total_chunks: number;
  chunks: string[];
  message: string;
}

export interface RAGRequest {
  query: string;
  k?: number;
  max_length?: number;
}

export interface RAGResponse {
  query: string;
  response: string;
  context_used: number;
  context_preview: string;
  model_info: {
    model: string;
    parameters: string;
    type: string;
  };
  tokens_used: number;
  retrieved_chunks: Array<{
    rank: number;
    chunk_id: number;
    chunk_text: string;
    similarity_score: number;
    distance_type: string;
  }>;
}

export type StreamEventType =
  | 'retrieval_started'
  | 'retrieval_completed'
  | 'generation_started'
  | 'token'
  | 'evaluation_complete'
  | 'completed'
  | 'error';

export interface StreamEvent {
  type: StreamEventType;
  data: Record<string, unknown>;
}

export interface StreamRagCallbacks {
  onEvent?: (event: StreamEvent) => void;
  onToken?: (text: string) => void;
  onComplete?: (data: Record<string, unknown>) => void;
  onError?: (message: string, stage?: string) => void;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  success: boolean;
}

function parseSSEChunk(chunk: string): StreamEvent | null {
  let eventType = 'message';
  const dataLines: string[] = [];

  for (const line of chunk.split('\n')) {
    if (line.startsWith('event:')) {
      eventType = line.slice(6).trim();
    } else if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trim());
    }
  }

  if (dataLines.length === 0) {
    return null;
  }

  try {
    const data = JSON.parse(dataLines.join('\n'));
    return { type: eventType as StreamEventType, data };
  } catch {
    return null;
  }
}

class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return { data, success: true };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Unknown error',
        success: false,
      };
    }
  }

  async uploadDocument(text: string): Promise<ApiResponse<UploadResponse>> {
    return this.request<UploadResponse>('/store-chunks', {
      method: 'POST',
      body: JSON.stringify({ text }),
    });
  }

  async getHealthCheck(): Promise<ApiResponse<any>> {
    return this.request<any>('/health');
  }

  async getStoreStats(): Promise<ApiResponse<any>> {
    return this.request<any>('/store-stats');
  }

  async ragQuery(request: RAGRequest): Promise<ApiResponse<RAGResponse>> {
    return this.request<RAGResponse>('/rag', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async streamRagQuery(
    request: RAGRequest,
    callbacks: StreamRagCallbacks,
    signal?: AbortSignal
  ): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/rag/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: request.query,
        k: request.k ?? 3,
        max_length: request.max_length ?? 200,
      }),
      signal,
    });

    if (!response.ok) {
      callbacks.onError?.(`HTTP error! status: ${response.status}`, 'connection');
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      callbacks.onError?.('Streaming not supported by browser', 'connection');
      return;
    }

    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split('\n\n');
        buffer = parts.pop() || '';

        for (const part of parts) {
          const event = parseSSEChunk(part.trim());
          if (!event) continue;

          callbacks.onEvent?.(event);

          switch (event.type) {
            case 'token':
              callbacks.onToken?.((event.data.text as string) || '');
              break;
            case 'completed':
              callbacks.onComplete?.(event.data);
              break;
            case 'error':
              callbacks.onError?.(
                (event.data.message as string) || 'Stream error',
                event.data.stage as string
              );
              break;
            default:
              break;
          }
        }
      }
    } catch (err) {
      if (signal?.aborted) {
        return;
      }
      callbacks.onError?.(
        err instanceof Error ? err.message : 'Stream connection failed',
        'connection'
      );
    }
  }
}

export const apiService = new ApiService();
