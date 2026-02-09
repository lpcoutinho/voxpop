import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/contexts/AuthContext';
import { teamMembersService, TeamMember } from '@/services/teamMembers';
import {
  User,
  Building2,
  CreditCard,
  Users,
  Ban,
  Construction,
  Mail,
  Phone,
  Shield,
  Crown,
  UserCog,
  Eye,
  Trash2,
  UserPlus,
  ExternalLink,
  Loader2,
} from 'lucide-react';
import { toast } from 'sonner';

type TabType = 'profile' | 'organization' | 'plan' | 'team';

export default function SettingsPage() {
  const { user, tenant } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>('profile');

  // Buscar membros da equipe
  const { data: teamMembersData, isLoading: isLoadingTeam } = useQuery({
    queryKey: ['team-members'],
    queryFn: () => teamMembersService.list(),
  });

  const teamMembers = teamMembersData?.results || [];

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const getRoleLabel = (role: string) => {
    const roles: Record<string, { label: string; color: string }> = {
      admin: { label: 'Administrador', color: 'bg-purple-500' },
      coordinator: { label: 'Coordenador', color: 'bg-purple-500' },
      operator: { label: 'Operador', color: 'bg-blue-500' },
      analyst: { label: 'Analista', color: 'bg-green-500' },
      volunteer: { label: 'Voluntário', color: 'bg-gray-500' },
    };
    return roles[role] || { label: role, color: 'bg-gray-500' };
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'admin':
        return Shield;
      case 'coordinator':
        return Crown;
      case 'operator':
        return UserCog;
      case 'analyst':
        return Eye;
      default:
        return Eye;
    }
  };

  const tabs = [
    { id: 'profile' as TabType, icon: User, label: 'Perfil' },
    { id: 'organization' as TabType, icon: Building2, label: 'Organização' },
    { id: 'plan' as TabType, icon: CreditCard, label: 'Plano de Uso' },
    { id: 'team' as TabType, icon: Users, label: 'Equipe' },
  ];

  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Configurações"
        description="Gerencie sua conta e preferências"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Configurações' },
        ]}
      />

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Sidebar */}
        <div className="lg:col-span-1">
          <nav className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                }`}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
              </button>
            ))}
          </nav>

          <Separator className="my-4" />

          {/* Quick Links */}
          <div className="space-y-1">
            <p className="px-4 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Links Rápidos
            </p>
            <Link
              to="/blacklist"
              className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
            >
              <Ban className="h-4 w-4" />
              Blacklist
              <ExternalLink className="h-3 w-3 ml-auto" />
            </Link>
          </div>
        </div>

        {/* Content */}
        <div className="lg:col-span-3 space-y-8">
          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <div className="bg-card rounded-xl p-6 shadow-card">
              <div className="flex items-center gap-3 mb-6">
                <User className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-semibold text-foreground">Perfil</h2>
              </div>

              <div className="flex items-center gap-6 mb-6">
                <Avatar className="h-20 w-20">
                  <AvatarImage src={user?.avatar} />
                  <AvatarFallback className="bg-primary text-primary-foreground text-xl">
                    {user?.name ? getInitials(user.name) : 'U'}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <Button variant="outline" size="sm">
                    Alterar foto
                  </Button>
                  <p className="text-xs text-muted-foreground mt-2">JPG, PNG. Máximo 2MB.</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Nome completo</Label>
                  <Input id="name" defaultValue={user?.name || ''} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" type="email" defaultValue={user?.email || ''} disabled />
                </div>
              </div>

              <Separator className="my-6" />

              <div className="space-y-4">
                <h3 className="font-medium text-foreground">Alterar senha</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="new-password">Nova senha</Label>
                    <Input id="new-password" type="password" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="confirm-password">Confirmar nova senha</Label>
                    <Input id="confirm-password" type="password" />
                  </div>
                </div>
              </div>

              <div className="flex justify-end mt-6">
                <Button>Salvar alterações</Button>
              </div>
            </div>
          )}

          {/* Organization Tab */}
          {activeTab === 'organization' && (
            <div className="bg-card rounded-xl p-6 shadow-card">
              <div className="flex items-center gap-3 mb-6">
                <Building2 className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-semibold text-foreground">Organização</h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="org-name">Nome da organização</Label>
                  <Input id="org-name" defaultValue={tenant?.name || ''} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="org-slug">Identificador (slug)</Label>
                  <Input id="org-slug" defaultValue={tenant?.slug || ''} disabled />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="org-cnpj">CNPJ</Label>
                  <Input id="org-cnpj" placeholder="00.000.000/0000-00" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="org-phone">Telefone</Label>
                  <Input id="org-phone" placeholder="(11) 9 9999-9999" />
                </div>
                <div className="space-y-2 md:col-span-2">
                  <Label htmlFor="org-email">Email de contato</Label>
                  <Input id="org-email" type="email" placeholder="contato@empresa.com.br" />
                </div>
              </div>

              <Separator className="my-6" />

              <div className="space-y-4">
                <h3 className="font-medium text-foreground">Endereço</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2 md:col-span-2">
                    <Label htmlFor="org-address">Logradouro</Label>
                    <Input id="org-address" placeholder="Rua, Avenida, etc." />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="org-city">Cidade</Label>
                    <Input id="org-city" placeholder="São Paulo" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="org-state">Estado</Label>
                    <Input id="org-state" placeholder="SP" />
                  </div>
                </div>
              </div>

              <div className="flex justify-end mt-6">
                <Button>Salvar alterações</Button>
              </div>
            </div>
          )}

          {/* Plan Tab - Under Construction */}
          {activeTab === 'plan' && (
            <div className="bg-card rounded-xl p-6 shadow-card">
              <div className="flex items-center gap-3 mb-6">
                <CreditCard className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-semibold text-foreground">Plano de Uso</h2>
              </div>

              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="rounded-full bg-yellow-100 p-4 mb-4">
                  <Construction className="h-12 w-12 text-yellow-600" />
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-2">Em Construção</h3>
                <p className="text-muted-foreground max-w-md">
                  Estamos trabalhando para trazer informações detalhadas sobre seu plano de uso,
                  limites e opções de upgrade. Em breve você poderá gerenciar sua assinatura por
                  aqui.
                </p>
                <Button variant="outline" className="mt-6" disabled>
                  Disponível em breve
                </Button>
              </div>
            </div>
          )}

          {/* Team Tab */}
          {activeTab === 'team' && (
            <div className="bg-card rounded-xl p-6 shadow-card">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <Users className="h-5 w-5 text-primary" />
                  <h2 className="text-lg font-semibold text-foreground">Equipe</h2>
                </div>
                <Button>
                  <UserPlus className="h-4 w-4 mr-2" />
                  Convidar membro
                </Button>
              </div>

              <p className="text-sm text-muted-foreground mb-6">
                Gerencie os membros da sua equipe e suas permissões de acesso.
              </p>

              {isLoadingTeam ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
              ) : teamMembers.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-muted-foreground">Nenhum membro na equipe ainda.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {teamMembers.map((member) => {
                    const roleInfo = getRoleLabel(member.role);
                    const RoleIcon = getRoleIcon(member.role);
                    return (
                      <div
                        key={member.id}
                        className="flex items-center justify-between p-4 rounded-lg border bg-background"
                      >
                        <div className="flex items-center gap-4">
                          <Avatar className="h-10 w-10">
                            <AvatarFallback className="bg-primary/10 text-primary">
                              {getInitials(member.display_name)}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="font-medium text-foreground">{member.display_name}</p>
                              {member.pending && (
                                <Badge variant="outline" className="text-yellow-600 border-yellow-600">
                                  Pendente
                                </Badge>
                              )}
                            </div>
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <Mail className="h-3 w-3" />
                              {member.user_email}
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-4">
                          <Badge className={`${roleInfo.color} text-white`}>
                            <RoleIcon className="h-3 w-3 mr-1" />
                            {roleInfo.label}
                          </Badge>

                          <div className="flex items-center gap-1">
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <UserCog className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8 text-destructive hover:text-destructive"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              <Separator className="my-6" />

              <div className="rounded-lg border border-dashed p-6 text-center">
                <h4 className="font-medium text-foreground mb-2">Papéis e Permissões</h4>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm text-muted-foreground mt-4">
                  <div className="flex items-center gap-2">
                    <Shield className="h-4 w-4 text-purple-500" />
                    <span>Admin - Acesso total</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Crown className="h-4 w-4 text-yellow-500" />
                    <span>Coordenador - Gerencia</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <UserCog className="h-4 w-4 text-blue-500" />
                    <span>Operador - Campanhas</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Eye className="h-4 w-4 text-green-500" />
                    <span>Analista - Dados</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-gray-500" />
                    <span>Voluntário - Visualização</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
