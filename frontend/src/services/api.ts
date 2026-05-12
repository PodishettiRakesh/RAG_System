const API_BASE_URL = 'http://localhost:8000';

export interface UploadResponse {
  total_words: number;
  total_chunks: number;
  chunks: string[];
  message: string;
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
}

export const apiService = new ApiService();
