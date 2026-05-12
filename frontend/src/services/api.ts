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

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  success: boolean;
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
}

export const apiService = new ApiService();
