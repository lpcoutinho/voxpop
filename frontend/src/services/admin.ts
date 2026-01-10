import api from './api';
import { Organization, Plan, AdminStats, AdminUser, PaginatedResponse } from '@/types';

// ============================================
// Organizations
// ============================================

export interface OrganizationFilters {
  search?: string;
  is_active?: boolean;
  plan_id?: number;
  page?: number;
  page_size?: number;
}

export interface CreateOrganizationData {
  organization: {
    name: string;
    slug?: string;
    document?: string;
    email?: string;
    phone?: string;
    plan_id?: number;
  };
  admin: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
  };
}

export interface UpdateOrganizationData {
  name?: string;
  document?: string;
  email?: string;
  phone?: string;
  plan_id?: number;
  is_active?: boolean;
}

// Base path for admin endpoints
const ADMIN_BASE = '/tenants/admin';

export const organizationsService = {
  list: async (filters?: OrganizationFilters): Promise<PaginatedResponse<Organization>> => {
    const params = new URLSearchParams();
    if (filters?.search) params.append('search', filters.search);
    if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
    if (filters?.plan_id) params.append('plan_id', String(filters.plan_id));
    if (filters?.page) params.append('page', String(filters.page));
    if (filters?.page_size) params.append('page_size', String(filters.page_size));

    const response = await api.get(`${ADMIN_BASE}/organizations/?${params.toString()}`);
    return response.data;
  },

  get: async (id: number): Promise<Organization> => {
    const response = await api.get(`${ADMIN_BASE}/organizations/${id}/`);
    return response.data;
  },

  create: async (data: CreateOrganizationData): Promise<Organization> => {
    const response = await api.post(`${ADMIN_BASE}/organizations/`, data);
    return response.data;
  },

  update: async (id: number, data: UpdateOrganizationData): Promise<Organization> => {
    const response = await api.patch(`${ADMIN_BASE}/organizations/${id}/`, data);
    return response.data;
  },

  toggleStatus: async (id: number): Promise<Organization> => {
    const response = await api.post(`${ADMIN_BASE}/organizations/${id}/toggle-status/`);
    return response.data;
  },
};

// ============================================
// Plans
// ============================================

export interface CreatePlanData {
  name: string;
  slug?: string;
  description?: string;
  max_supporters: number;
  max_messages_month: number;
  max_campaigns: number;
  max_whatsapp_sessions: number;
  price: number;
  is_active?: boolean;
  is_public?: boolean;
}

export interface UpdatePlanData extends Partial<CreatePlanData> {}

export const plansService = {
  list: async (): Promise<Plan[]> => {
    const response = await api.get(`${ADMIN_BASE}/plans/`);
    return response.data;
  },

  get: async (id: number): Promise<Plan> => {
    const response = await api.get(`${ADMIN_BASE}/plans/${id}/`);
    return response.data;
  },

  create: async (data: CreatePlanData): Promise<Plan> => {
    const response = await api.post(`${ADMIN_BASE}/plans/`, data);
    return response.data;
  },

  update: async (id: number, data: UpdatePlanData): Promise<Plan> => {
    const response = await api.patch(`${ADMIN_BASE}/plans/${id}/`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`${ADMIN_BASE}/plans/${id}/`);
  },
};

// ============================================
// Users
// ============================================

export interface UserFilters {
  search?: string;
  is_active?: boolean;
  is_superuser?: boolean;
  organization_id?: number;
  page?: number;
  page_size?: number;
}

export interface UpdateUserData {
  first_name?: string;
  last_name?: string;
  is_active?: boolean;
  is_verified?: boolean;
}

export const usersService = {
  list: async (filters?: UserFilters): Promise<PaginatedResponse<AdminUser>> => {
    const params = new URLSearchParams();
    if (filters?.search) params.append('search', filters.search);
    if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active));
    if (filters?.is_superuser !== undefined) params.append('is_superuser', String(filters.is_superuser));
    if (filters?.organization_id) params.append('organization_id', String(filters.organization_id));
    if (filters?.page) params.append('page', String(filters.page));
    if (filters?.page_size) params.append('page_size', String(filters.page_size));

    const response = await api.get(`${ADMIN_BASE}/users/?${params.toString()}`);
    return response.data;
  },

  get: async (id: number): Promise<AdminUser> => {
    const response = await api.get(`${ADMIN_BASE}/users/${id}/`);
    return response.data;
  },

  update: async (id: number, data: UpdateUserData): Promise<AdminUser> => {
    const response = await api.patch(`${ADMIN_BASE}/users/${id}/`, data);
    return response.data;
  },

  resetPassword: async (id: number): Promise<{ message: string; temporary_password?: string }> => {
    const response = await api.post(`${ADMIN_BASE}/users/${id}/reset-password/`);
    return response.data;
  },
};

// ============================================
// Stats
// ============================================

export const statsService = {
  get: async (): Promise<AdminStats> => {
    const response = await api.get(`${ADMIN_BASE}/stats/`);
    return response.data;
  },
};

// Export all services
export const adminService = {
  organizations: organizationsService,
  plans: plansService,
  users: usersService,
  stats: statsService,
};
