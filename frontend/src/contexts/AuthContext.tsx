import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { User, Tenant } from '@/types';

// Demo mode - set to true to bypass real API calls
const DEMO_MODE = false;

const demoUser: User = {
  id: 1,
  email: 'demo@voxpop.com.br',
  name: 'Usuário Demo',
  role: 'admin',
};

const demoTenants: Tenant[] = [
  { id: 1, name: 'Campanha 2024', slug: 'campanha-2024' },
];

interface AuthContextType {
  user: User | null;
  tenant: Tenant | null;
  tenants: Tenant[];
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  selectTenant: (tenant: Tenant) => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    if (DEMO_MODE) {
      // Demo mode - use mock data
      const isLoggedIn = localStorage.getItem('demo_logged_in') === 'true';
      if (isLoggedIn) {
        setUser(demoUser);
        setTenants(demoTenants);
        setTenant(demoTenants[0]);
      }
      return;
    }
    
    // Real API mode
    try {
      const { default: api } = await import('@/services/api');
      const [userResponse, tenantsResponse] = await Promise.all([
        api.get('/auth/me/'),
        api.get('/auth/me/tenants/'),
      ]);

      // Map user data
      const userData = userResponse.data;
      setUser({
        id: userData.id,
        email: userData.email,
        name: userData.full_name || `${userData.first_name} ${userData.last_name}`.trim(),
        first_name: userData.first_name,
        last_name: userData.last_name,
        avatar: userData.avatar,
        role: 'admin', // TODO: Get from membership
        is_superuser: userData.is_superuser,
        is_staff: userData.is_staff,
        is_verified: userData.is_verified,
        force_password_change: userData.force_password_change,
      });

      // Map tenant data from API format (tenant_id, tenant_name, tenant_slug) to frontend format (id, name, slug)
      const mappedTenants: Tenant[] = tenantsResponse.data.map((t: { tenant_id: number; tenant_name: string; tenant_slug: string }) => ({
        id: t.tenant_id,
        name: t.tenant_name,
        slug: t.tenant_slug,
      }));
      setTenants(mappedTenants);

      if (mappedTenants.length === 1) {
        const firstTenant = mappedTenants[0];
        setTenant(firstTenant);
        localStorage.setItem('selected_tenant_slug', firstTenant.slug);
      } else {
        const savedTenantId = localStorage.getItem('selected_tenant');
        if (savedTenantId) {
          const savedTenant = mappedTenants.find(
            (t: Tenant) => t.id === parseInt(savedTenantId)
          );
          if (savedTenant) {
            setTenant(savedTenant);
            localStorage.setItem('selected_tenant_slug', savedTenant.slug);
          }
        }
      }
    } catch (error) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
    }
  }, []);

  useEffect(() => {
    if (DEMO_MODE) {
      fetchUser().finally(() => setIsLoading(false));
    } else {
      const token = localStorage.getItem('access_token');
      if (token) {
        fetchUser().finally(() => setIsLoading(false));
      } else {
        setIsLoading(false);
      }
    }
  }, [fetchUser]);

  const login = async (email: string, password: string) => {
    if (DEMO_MODE) {
      // Demo login - accept any credentials
      localStorage.setItem('demo_logged_in', 'true');
      setUser(demoUser);
      setTenants(demoTenants);
      setTenant(demoTenants[0]);
      return;
    }
    
    // Real API login
    const { default: api } = await import('@/services/api');
    const response = await api.post('/auth/token/', { email, password });
    const { access, refresh } = response.data;
    
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    
    await fetchUser();
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('selected_tenant');
    localStorage.removeItem('selected_tenant_slug');
    localStorage.removeItem('demo_logged_in');
    setUser(null);
    setTenant(null);
    setTenants([]);
  };

  const selectTenant = (selectedTenant: Tenant) => {
    setTenant(selectedTenant);
    localStorage.setItem('selected_tenant', selectedTenant.id.toString());
    localStorage.setItem('selected_tenant_slug', selectedTenant.slug);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        tenant,
        tenants,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        selectTenant,
        refreshUser: fetchUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
