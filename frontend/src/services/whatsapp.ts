import { api } from './api';
import { WhatsAppSession } from '@/types';

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

interface ConnectResponse {
  qr_code?: string;
  status: string;
  message?: string;
}

export const whatsappService = {
  list: async (): Promise<WhatsAppSession[]> => {
    const { data } = await api.get<PaginatedResponse<WhatsAppSession> | WhatsAppSession[]>('/whatsapp/sessions/');
    return Array.isArray(data) ? data : data.results;
  },

  get: async (id: number): Promise<WhatsAppSession> => {
    const { data } = await api.get<WhatsAppSession>(`/whatsapp/sessions/${id}/`);
    return data;
  },

  create: async (session: { name: string; daily_message_limit?: number }): Promise<WhatsAppSession> => {
    const { data } = await api.post<WhatsAppSession>('/whatsapp/sessions/', session);
    return data;
  },

  update: async (id: number, session: Partial<WhatsAppSession>): Promise<WhatsAppSession> => {
    const { data } = await api.patch<WhatsAppSession>(`/whatsapp/sessions/${id}/`, session);
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/whatsapp/sessions/${id}/`);
  },

  connect: async (id: number): Promise<ConnectResponse> => {
    const { data } = await api.post<ConnectResponse>(`/whatsapp/sessions/${id}/connect/`);
    return data;
  },

  disconnect: async (id: number): Promise<void> => {
    await api.post(`/whatsapp/sessions/${id}/disconnect/`);
  },

  getStatus: async (id: number): Promise<{ status: string; phone_number?: string }> => {
    const { data } = await api.get<{ status: string; phone_number?: string }>(`/whatsapp/sessions/${id}/status/`);
    return data;
  },
};
