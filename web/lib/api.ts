import axios from 'axios';
import type {
  ArticleRequest,
  ArticleResponse,
  JobResponse,
  JobCreateResponse,
  SERPAnalysis,
  ArticleOutline,
  JobStatus,
} from '@/types/api';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiClient = {
  // Health check
  async healthCheck() {
    const response = await api.get('/');
    return response.data;
  },

  // Generate article synchronously
  async generateArticle(request: ArticleRequest): Promise<ArticleResponse> {
    const response = await api.post<ArticleResponse>('/generate', request);
    return response.data;
  },

  // Job management
  async createJob(request: ArticleRequest): Promise<JobCreateResponse> {
    const response = await api.post<JobCreateResponse>('/jobs', request);
    return response.data;
  },

  async getJob(jobId: string): Promise<JobResponse> {
    const response = await api.get<JobResponse>(`/jobs/${jobId}`);
    return response.data;
  },

  async listJobs(status?: JobStatus, limit: number = 50): Promise<JobResponse[]> {
    const params: Record<string, any> = { limit };
    if (status) {
      params.status = status;
    }
    const response = await api.get<JobResponse[]>('/jobs', { params });
    return response.data;
  },

  async resumeJob(jobId: string): Promise<JobResponse> {
    const response = await api.post<JobResponse>(`/jobs/${jobId}/resume`);
    return response.data;
  },

  // Research
  async researchTopic(topic: string): Promise<SERPAnalysis> {
    const response = await api.get<SERPAnalysis>(`/research/${encodeURIComponent(topic)}`);
    return response.data;
  },

  async generateOutline(request: ArticleRequest): Promise<ArticleOutline> {
    const response = await api.post<ArticleOutline>('/outline', request);
    return response.data;
  },
};
