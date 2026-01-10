import { api } from './api';
import { Campaign } from '@/types';

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

interface CampaignFilters {
  status?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export const campaignsService = {
  list: async (params?: CampaignFilters): Promise<Campaign[]> => {
    const { data } = await api.get<PaginatedResponse<Campaign> | Campaign[]>('/campaigns/', { params });
    return Array.isArray(data) ? data : data.results;
  },

  get: async (id: number): Promise<Campaign> => {
    const { data } = await api.get<Campaign>(`/campaigns/${id}/`);
    return data;
  },

  create: async (campaign: Partial<Campaign>): Promise<Campaign> => {
    const { data } = await api.post<Campaign>('/campaigns/', campaign);
    return data;
  },

  update: async (id: number, campaign: Partial<Campaign>): Promise<Campaign> => {
    const { data } = await api.patch<Campaign>(`/campaigns/${id}/`, campaign);
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/campaigns/${id}/`);
  },

  start: async (id: number): Promise<Campaign> => {
    const { data } = await api.post<Campaign>(`/campaigns/${id}/start/`);
    return data;
  },

  pause: async (id: number): Promise<Campaign> => {
    const { data } = await api.post<Campaign>(`/campaigns/${id}/pause/`);
    return data;
  },

  resume: async (id: number): Promise<Campaign> => {
    const { data } = await api.post<Campaign>(`/campaigns/${id}/resume/`);
    return data;
  },

  cancel: async (id: number): Promise<Campaign> => {
    const { data } = await api.post<Campaign>(`/campaigns/${id}/cancel/`);
    return data;
  },

  getMetrics: async (id: number): Promise<{
    total_recipients: number;
    messages_sent: number;
    messages_delivered: number;
    messages_read: number;
    messages_failed: number;
  }> => {
    const { data } = await api.get(`/campaigns/${id}/metrics/`);
    return data;
  },
};
