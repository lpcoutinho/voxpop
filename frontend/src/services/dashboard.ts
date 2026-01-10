import { api } from './api';

export interface DashboardStats {
  total_supporters: number;
  total_campaigns: number;
  active_campaigns: number;
  messages_sent: number;
  messages_delivered: number;
  messages_read: number;
  messages_failed: number;
  delivery_rate: number;
  read_rate: number;
}

export interface DashboardMetrics {
  date: string;
  sent: number;
  delivered: number;
  read: number;
  failed: number;
}

export interface RecentActivity {
  id: number;
  type: 'campaign' | 'import' | 'message' | 'supporter';
  title: string;
  time: string;
  status?: string;
}

export const dashboardService = {
  getStats: async (): Promise<DashboardStats> => {
    const { data } = await api.get<DashboardStats>('/dashboard/');
    return data;
  },

  getMetrics: async (params?: { start_date?: string; end_date?: string }): Promise<DashboardMetrics[]> => {
    const { data } = await api.get<DashboardMetrics[]>('/dashboard/metrics/', { params });
    return data;
  },

  getRecentActivities: async (limit?: number): Promise<RecentActivity[]> => {
    const { data } = await api.get<RecentActivity[]>('/dashboard/activities/', { params: { limit } });
    return data;
  },
};
