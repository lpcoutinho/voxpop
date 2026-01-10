import { api } from './api';
import { MessageTemplate } from '@/types';

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export const templatesService = {
  list: async (): Promise<MessageTemplate[]> => {
    const { data } = await api.get<PaginatedResponse<MessageTemplate> | MessageTemplate[]>('/messages/templates/');
    return Array.isArray(data) ? data : data.results;
  },

  get: async (id: number): Promise<MessageTemplate> => {
    const { data } = await api.get<MessageTemplate>(`/messages/templates/${id}/`);
    return data;
  },

  create: async (template: Partial<MessageTemplate>): Promise<MessageTemplate> => {
    const { data } = await api.post<MessageTemplate>('/messages/templates/', template);
    return data;
  },

  update: async (id: number, template: Partial<MessageTemplate>): Promise<MessageTemplate> => {
    const { data } = await api.patch<MessageTemplate>(`/messages/templates/${id}/`, template);
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/messages/templates/${id}/`);
  },

  preview: async (id: number, context: Record<string, string>): Promise<{ rendered: string }> => {
    const { data } = await api.post<{ rendered: string }>(`/messages/templates/${id}/preview/`, context);
    return data;
  },

  duplicate: async (id: number): Promise<MessageTemplate> => {
    const { data } = await api.post<MessageTemplate>(`/messages/templates/${id}/duplicate/`);
    return data;
  },
};
