import api from './api';
import { Supporter, Tag, PaginatedResponse } from '@/types';

export interface SupportersFilters {
  search?: string;
  tag_ids?: number[];
  contact_status?: 'lead' | 'apoiador' | 'blacklist';
  city?: string;
  state?: string;
  whatsapp_opt_in?: boolean;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export interface CreateSupporterData {
  name: string;
  phone: string;
  email?: string;
  cpf?: string;
  city?: string;
  state?: string;
  neighborhood?: string;
  zip_code?: string;
  electoral_zone?: string;
  electoral_section?: string;
  birth_date?: string;
  gender?: 'M' | 'F' | 'O';
  whatsapp_opt_in?: boolean;
  tag_ids?: number[];
  initial_status?: 'lead' | 'apoiador';
}

export interface UpdateSupporterData extends Partial<CreateSupporterData> {}

export interface BulkActionResponse {
  success: boolean;
  message: string;
  updated_count: number;
}

export interface StatusChangeResponse {
  detail: string;
  contact_status: string;
}

export const supportersService = {
  // List supporters with filters
  list: async (filters: SupportersFilters = {}): Promise<PaginatedResponse<Supporter>> => {
    const params = new URLSearchParams();

    if (filters.search) params.append('search', filters.search);
    if (filters.contact_status) params.append('contact_status', filters.contact_status);
    if (filters.city) params.append('city', filters.city);
    if (filters.state) params.append('state', filters.state);
    if (filters.whatsapp_opt_in !== undefined) params.append('whatsapp_opt_in', String(filters.whatsapp_opt_in));
    if (filters.ordering) params.append('ordering', filters.ordering);
    if (filters.page) params.append('page', String(filters.page));
    if (filters.page_size) params.append('page_size', String(filters.page_size));
    if (filters.tag_ids?.length) {
      filters.tag_ids.forEach(id => params.append('tags', String(id)));
    }

    const response = await api.get(`/supporters/?${params.toString()}`);
    return response.data;
  },

  // Get single supporter
  get: async (id: number): Promise<Supporter> => {
    const response = await api.get(`/supporters/${id}/`);
    return response.data;
  },

  // Create supporter
  create: async (data: CreateSupporterData): Promise<Supporter> => {
    const response = await api.post('/supporters/', data);
    return response.data;
  },

  // Update supporter
  update: async (id: number, data: UpdateSupporterData): Promise<Supporter> => {
    const response = await api.patch(`/supporters/${id}/`, data);
    return response.data;
  },

  // Delete supporter (soft delete)
  delete: async (id: number): Promise<void> => {
    await api.delete(`/supporters/${id}/`);
  },

  // Add tags to supporter
  addTags: async (id: number, tagIds: number[]): Promise<{ detail: string; tags_added: number }> => {
    const response = await api.post(`/supporters/${id}/tags/`, { tag_ids: tagIds });
    return response.data;
  },

  // Remove tags from supporter
  removeTags: async (id: number, tagIds: number[]): Promise<{ detail: string; tags_removed: number }> => {
    const response = await api.delete(`/supporters/${id}/tags/`, { data: { tag_ids: tagIds } });
    return response.data;
  },

  // Individual status actions
  promote: async (id: number): Promise<StatusChangeResponse> => {
    const response = await api.post(`/supporters/${id}/promote/`);
    return response.data;
  },

  demote: async (id: number): Promise<StatusChangeResponse> => {
    const response = await api.post(`/supporters/${id}/demote/`);
    return response.data;
  },

  blacklist: async (id: number): Promise<StatusChangeResponse> => {
    const response = await api.post(`/supporters/${id}/blacklist/`);
    return response.data;
  },

  unblacklist: async (id: number): Promise<StatusChangeResponse> => {
    const response = await api.post(`/supporters/${id}/unblacklist/`);
    return response.data;
  },

  // Bulk actions
  bulkPromote: async (supporterIds: number[]): Promise<BulkActionResponse> => {
    const response = await api.post('/supporters/bulk-promote/', { supporter_ids: supporterIds });
    return response.data;
  },

  bulkDemote: async (supporterIds: number[]): Promise<BulkActionResponse> => {
    const response = await api.post('/supporters/bulk-demote/', { supporter_ids: supporterIds });
    return response.data;
  },

  bulkBlacklist: async (supporterIds: number[]): Promise<BulkActionResponse> => {
    const response = await api.post('/supporters/bulk-blacklist/', { supporter_ids: supporterIds });
    return response.data;
  },

  bulkUnblacklist: async (supporterIds: number[]): Promise<BulkActionResponse> => {
    const response = await api.post('/supporters/bulk-unblacklist/', { supporter_ids: supporterIds });
    return response.data;
  },
};

export const tagsService = {
  // List tags
  list: async (): Promise<Tag[]> => {
    const response = await api.get('/supporters/tags/');
    return response.data.results || response.data;
  },

  // Get system tags
  getSystemTags: async (): Promise<Tag[]> => {
    const response = await api.get('/supporters/tags/?is_system=true');
    return response.data.results || response.data;
  },

  // Get single tag
  get: async (id: number): Promise<Tag> => {
    const response = await api.get(`/supporters/tags/${id}/`);
    return response.data;
  },

  // Create tag
  create: async (data: { name: string; color: string; description?: string }): Promise<Tag> => {
    const response = await api.post('/supporters/tags/', data);
    return response.data;
  },

  // Update tag
  update: async (id: number, data: { name?: string; color?: string; description?: string }): Promise<Tag> => {
    const response = await api.patch(`/supporters/tags/${id}/`, data);
    return response.data;
  },

  // Delete tag
  delete: async (id: number): Promise<void> => {
    await api.delete(`/supporters/tags/${id}/`);
  },
};

export default supportersService;
