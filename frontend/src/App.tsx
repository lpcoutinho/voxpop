import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { AppLayout } from "@/components/layout/AppLayout";

// Auth Pages
import LoginPage from "@/pages/auth/LoginPage";
import SelectTenantPage from "@/pages/auth/SelectTenantPage";
import ChangePasswordPage from "@/pages/auth/ChangePasswordPage";

// App Pages
import DashboardPage from "@/pages/dashboard/DashboardPage";
import LeadsPage from "@/pages/leads/LeadsPage";
import SupportersPage from "@/pages/supporters/SupportersPage";
import SegmentsPage from "@/pages/segments/SegmentsPage";
import TagsPage from "@/pages/tags/TagsPage";
import TemplatesPage from "@/pages/templates/TemplatesPage";
import WhatsAppPage from "@/pages/whatsapp/WhatsAppPage";
import CampaignsPage from "@/pages/campaigns/CampaignsPage";
import CampaignCreatePage from "@/pages/campaigns/CampaignCreatePage";
import CampaignDetailsPage from "@/pages/campaigns/CampaignDetailsPage";
import ReportsPage from "@/pages/reports/ReportsPage";
import SettingsPage from "@/pages/settings/SettingsPage";
import BlacklistPage from "@/pages/blacklist/BlacklistPage";
import TeamMembersPage from "@/pages/teams/TeamMembersPage";
import NotFound from "@/pages/NotFound";

// Admin Pages
import AdminLayout from "@/pages/admin/AdminLayout";
import AdminDashboard from "@/pages/admin/AdminDashboard";
import OrganizationsPage from "@/pages/admin/OrganizationsPage";
import OrganizationFormPage from "@/pages/admin/OrganizationFormPage";
import PlansPage from "@/pages/admin/PlansPage";
import UsersPage from "@/pages/admin/UsersPage";
import { useAuth } from "@/contexts/AuthContext";

const queryClient = new QueryClient();

const ForcePasswordChangeWrapper = ({ children }: { children: React.ReactNode }) => {
  const { user, isLoading } = useAuth();
  
  if (isLoading) return <div>Carregando...</div>;
  
  if (user?.force_password_change) {
    return <Navigate to="/change-password" replace />;
  }
  
  return <>{children}</>;
};

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuth();
  
  if (isLoading) return <div>Carregando...</div>;
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<LoginPage />} />
            
            {/* Forced Password Change Route */}
            <Route path="/change-password" element={
              <ProtectedRoute>
                <ChangePasswordPage />
              </ProtectedRoute>
            } />
            
            {/* Protected Routes */}
            <Route path="/select-tenant" element={
              <ForcePasswordChangeWrapper>
                <SelectTenantPage />
              </ForcePasswordChangeWrapper>
            } />
            
            <Route element={
              <ForcePasswordChangeWrapper>
                <AppLayout />
              </ForcePasswordChangeWrapper>
            }>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/leads" element={<LeadsPage />} />
              <Route path="/supporters" element={<SupportersPage />} />
              <Route path="/segments" element={<SegmentsPage />} />
              <Route path="/tags" element={<TagsPage />} />
              <Route path="/templates" element={<TemplatesPage />} />
              <Route path="/whatsapp" element={<WhatsAppPage />} />
              <Route path="/campaigns" element={<CampaignsPage />} />
              <Route path="/campaigns/new" element={<CampaignCreatePage />} />
              <Route path="/campaigns/:id" element={<CampaignDetailsPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/teams" element={<TeamMembersPage />} />
              <Route path="/blacklist" element={<BlacklistPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Route>

            {/* Admin Routes (superuser only) */}
            <Route element={
              <ForcePasswordChangeWrapper>
                <AdminLayout />
              </ForcePasswordChangeWrapper>
            }>
              <Route path="/admin" element={<Navigate to="/admin/dashboard" replace />} />
              <Route path="/admin/dashboard" element={<AdminDashboard />} />
              <Route path="/admin/organizations" element={<OrganizationsPage />} />
              <Route path="/admin/organizations/new" element={<OrganizationFormPage />} />
              <Route path="/admin/organizations/:id" element={<OrganizationFormPage />} />
              <Route path="/admin/plans" element={<PlansPage />} />
              <Route path="/admin/users" element={<UsersPage />} />
            </Route>

            {/* Redirects */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            
            {/* 404 */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
