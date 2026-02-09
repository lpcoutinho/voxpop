import { api } from './api';

export interface TeamMember {
  id: number;
  display_name: string;
  user_email: string;
  role: string;
  role_display: string;
  department: string;
  department_display: string;
  is_active: boolean;
  pending: boolean;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface TeamMemberCreate {
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
  role: string;
  department: string;
  notes: string;
  send_whatsapp_credentials: boolean;
  is_active: boolean;
}

export interface TeamMemberUpdate {
  role: string;
  department: string;
  notes: string;
  is_active: boolean;
}

export interface PaginatedTeamMembers {
  count: number;
  next: string | null;
  previous: string | null;
  results: TeamMember[];
}

export const teamMembersService = {
  // Listar todos os membros
  list: async (params: {
    page?: number;
    search?: string;
    role?: string;
    department?: string;
    is_active?: boolean;
  } = {}): Promise<PaginatedTeamMembers> => {
    const searchParams = new URLSearchParams();

    if (params.page) searchParams.set('page', params.page.toString());
    if (params.search) searchParams.set('search', params.search);
    if (params.role) searchParams.set('role', params.role);
    if (params.department) searchParams.set('department', params.department);
    if (params.is_active !== undefined) searchParams.set('is_active', params.is_active.toString());

    const response = await api.get(`/teams/team-members/?${searchParams.toString()}`);
    return response.data;
  },

  // Obter membro específico
  get: async (id: number): Promise<TeamMember> => {
    const response = await api.get(`/teams/team-members/${id}/`);
    return response.data;
  },

  // Criar novo membro
  create: async (data: TeamMemberCreate): Promise<TeamMember> => {
    const response = await api.post('/teams/team-members/', data);
    return response.data;
  },

  // Atualizar membro
  update: async (id: number, data: TeamMemberUpdate): Promise<TeamMember> => {
    const response = await api.patch(`/teams/team-members/${id}/`, data);
    return response.data;
  },

  // Ativar membro
  activate: async (id: number): Promise<TeamMember> => {
    const response = await api.post(`/teams/team-members/${id}/activate/`);
    return response.data.data;
  },

  // Desativar membro
  deactivate: async (id: number): Promise<TeamMember> => {
    const response = await api.post(`/teams/team-members/${id}/deactivate/`);
    return response.data.data;
  },

  // Ativar múltiplos membros
  bulkActivate: async (memberIds: number[]): Promise<{ message: string; updated_count: number }> => {
    const response = await api.post(`/teams/team-members/bulk_activate/`, { member_ids: memberIds });
    return response.data;
  },

  // Desativar múltiplos membros
  bulkDeactivate: async (memberIds: number[]): Promise<{ message: string; updated_count: number }> => {
    const response = await api.post(`/teams/team-members/bulk_deactivate/`, { member_ids: memberIds });
    return response.data;
  },

  // Reenviar credenciais
  sendCredentials: async (id: number): Promise<{ message: string; phone: string }> => {
    const response = await api.post(`/teams/team-members/${id}/send_credentials/`);
    return response.data;
  },

  // Resumo por função
  getRoleSummary: async (): Promise<{ data: Array<{ role: string; count: number }>; total: number }> => {
    const response = await api.get(`/teams/team-members/role_summary/`);
    return response.data;
  },

  // Resumo por departamento
  getDepartmentSummary: async (): Promise<{ data: Array<{ department: string; count: number }>; total: number }> => {
    const response = await api.get(`/teams/team-members/department_summary/`);
    return response.data;
  },

  // Deletar membro
  delete: async (id: number): Promise<void> => {
    await api.delete(`/teams/team-members/${id}/`);
  },
};