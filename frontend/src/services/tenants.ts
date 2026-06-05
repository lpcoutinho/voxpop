import { api } from './api';
import { TenantConfig } from '@/types';

export const tenantsService = {
  getConfig: async (): Promise<TenantConfig> => {
    const { data } = await api.get<TenantConfig>('/tenants/config/');
    return data;
  },

  updateConfig: async (config: TenantConfig): Promise<TenantConfig> => {
    const { data } = await api.put<TenantConfig>('/tenants/config/', config);
    return data;
  },
};
