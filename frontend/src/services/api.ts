/**
 * NeuroLens API Service
 * Centralized API client with JWT authentication
 */

import axios, { type AxiosError, type AxiosInstance, type InternalAxiosRequestConfig, type AxiosResponse } from 'axios';

// API base URL - proxied through Vite config
const API_BASE_URL = '/api';

// Polling interval for async operations (2 seconds as per spec)
export const POLLING_INTERVAL = 2000;

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - attach JWT token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle 401 errors
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Clear tokens and redirect to login
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_data');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ========================================
// Auth API
// ========================================

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface SignupData {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user?: {
    username: string;
    email: string;
    role: string;
  };
}

export const authAPI = {
  login: async (username: string, password: string): Promise<AuthResponse> => {
    const response = await api.post('/auth/token/', { username, password });
    return response.data;
  },

  register: async (username: string, email: string, password: string): Promise<AuthResponse> => {
    const response = await api.post('/auth/register/', { username, email, password });
    return response.data;
  },

  refreshToken: async (refresh: string): Promise<{ access: string }> => {
    const response = await api.post('/auth/token/refresh/', { refresh });
    return response.data;
  },

  getProfile: async () => {
    const response = await api.get('/v1/auth/profile/');
    return response.data;
  },
};

// ========================================
// Health API
// ========================================

export const healthAPI = {
  check: async () => {
    const response = await api.get('/health/');
    return response.data;
  },

  getHealth: async () => {
    try {
      const [general, ml] = await Promise.all([
        api.get('/health/').catch(() => ({ data: { status: 'unknown' } })),
        api.get('/inference/health/').catch(() => ({ data: { status: 'unknown' } })),
      ]);
      return {
        status: general.data.status || 'healthy',
        database: general.data.database || 'connected',
        cache: general.data.cache || 'connected',
        celery: general.data.celery || 'healthy',
        ml_model: ml.data.status || 'loaded',
      };
    } catch {
      return null;
    }
  },

  mlHealth: async () => {
    const response = await api.get('/inference/health/');
    return response.data;
  },
};

// ========================================
// Datasets API
// ========================================

export interface Dataset {
  id: number;
  name: string;
  description?: string;
  file_count: number;
  image_count?: number;
  size?: number;
  status: string;
  created_at: string;
  updated_at?: string;
}

export interface UploadProgressEvent {
  loaded: number;
  total?: number;
}

export const datasetsAPI = {
  list: async (): Promise<Dataset[]> => {
    const response = await api.get('/v1/datasets/');
    return Array.isArray(response.data) ? response.data : response.data.results || [];
  },

  get: async (id: number): Promise<Dataset> => {
    const response = await api.get(`/v1/datasets/${id}/`);
    return response.data;
  },

  create: async (formData: FormData, onProgress?: (event: UploadProgressEvent) => void): Promise<Dataset> => {
    const response = await api.post('/v1/datasets/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: onProgress,
    });
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/v1/datasets/${id}/`);
  },
};

// ========================================
// Inference API
// ========================================

export interface InferenceRequest {
  dataset_id?: number;
  image?: File;
  model?: string;
}

export interface InferenceResult {
  id: number;
  dataset_id?: number;
  dataset_name?: string;
  image_name?: string;
  model: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  prediction?: string;
  confidence?: number;
  error_message?: string;
  results?: Array<{
    image_id: number;
    image_name: string;
    image_url?: string;
    prediction: string;
    confidence: number;
    severity_level: number;
    heatmap_url?: string | null;
  }>;
  error?: string;
  created_at: string;
  completed_at?: string | null;
}

export const inferenceAPI = {
  list: async (): Promise<InferenceResult[]> => {
    const response = await api.get('/v1/inferences/');
    return Array.isArray(response.data) ? response.data : response.data.results || [];
  },

  get: async (id: number): Promise<InferenceResult> => {
    const response = await api.get(`/v1/inferences/${id}/`);
    return response.data;
  },

  submit: async (datasetId: number): Promise<InferenceResult> => {
    const response = await api.post('/v1/inferences/', { dataset_id: datasetId });
    return response.data;
  },

  create: async (data: InferenceRequest): Promise<InferenceResult> => {
    if (data.image) {
      const formData = new FormData();
      formData.append('image', data.image);
      if (data.model) formData.append('model', data.model);

      const response = await api.post('/v1/inferences/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    }

    const response = await api.post('/v1/inferences/', {
      dataset_id: data.dataset_id,
      model: data.model,
    });
    return response.data;
  },

  predict: async (formData: FormData): Promise<InferenceResult> => {
    const response = await api.post('/inference/predict/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// ========================================
// Dashboard Stats API
// ========================================

export interface DashboardStats {
  total_datasets: number;
  total_inferences: number;
  pending_inferences: number;
  completed_inferences: number;
  failed_inferences: number;
}

export const statsAPI = {
  getDashboardStats: async (): Promise<DashboardStats> => {
    try {
      const response = await api.get('/v1/stats/dashboard/');
      return response.data;
    } catch {
      // Fallback: calculate from individual endpoints
      const [datasets, inferences] = await Promise.all([
        datasetsAPI.list().catch(() => []),
        inferenceAPI.list().catch(() => []),
      ]);

      return {
        total_datasets: datasets.length,
        total_inferences: inferences.length,
        pending_inferences: inferences.filter((i) => i.status === 'pending').length,
        completed_inferences: inferences.filter((i) => i.status === 'completed').length,
        failed_inferences: inferences.filter((i) => i.status === 'failed').length,
      };
    }
  },
};

// ========================================
// Token Management Helpers
// ========================================

export const TokenManager = {
  getAccess: (): string | null => localStorage.getItem('access_token'),
  getRefresh: (): string | null => localStorage.getItem('refresh_token'),

  setTokens: (access: string, refresh?: string): void => {
    localStorage.setItem('access_token', access);
    if (refresh) {
      localStorage.setItem('refresh_token', refresh);
    }
  },

  clearTokens: (): void => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_data');
  },

  isAuthenticated: (): boolean => !!localStorage.getItem('access_token'),
};

export const UserManager = {
  getUser: (): { username: string; email?: string; role?: string } | null => {
    const data = localStorage.getItem('user_data');
    return data ? JSON.parse(data) : null;
  },

  setUser: (data: { username: string; email?: string; role?: string }): void => {
    localStorage.setItem('user_data', JSON.stringify(data));
  },

  clearUser: (): void => {
    localStorage.removeItem('user_data');
  },
};

export default api;
