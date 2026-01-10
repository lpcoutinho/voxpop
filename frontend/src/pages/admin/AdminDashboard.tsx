import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { statsService } from '@/services/admin';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Building2,
  Users,
  UserCheck,
  Megaphone,
  MessageSquare,
  TrendingUp,
  Plus,
  ArrowRight,
  Loader2,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export default function AdminDashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['admin', 'stats'],
    queryFn: statsService.get,
  });

  const statCards = [
    {
      title: 'Organizações',
      value: stats?.total_organizations ?? 0,
      subtitle: `${stats?.active_organizations ?? 0} ativas`,
      icon: Building2,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
    },
    {
      title: 'Usuários',
      value: stats?.total_users ?? 0,
      subtitle: 'cadastrados',
      icon: Users,
      color: 'text-purple-500',
      bgColor: 'bg-purple-500/10',
    },
    {
      title: 'Contatos',
      value: stats?.total_supporters ?? 0,
      subtitle: 'em todas orgs',
      icon: UserCheck,
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
    },
    {
      title: 'Campanhas',
      value: stats?.total_campaigns ?? 0,
      subtitle: 'criadas',
      icon: Megaphone,
      color: 'text-orange-500',
      bgColor: 'bg-orange-500/10',
    },
    {
      title: 'Mensagens',
      value: stats?.total_messages ?? 0,
      subtitle: 'enviadas',
      icon: MessageSquare,
      color: 'text-cyan-500',
      bgColor: 'bg-cyan-500/10',
    },
    {
      title: 'Este Mês',
      value: stats?.messages_this_month ?? 0,
      subtitle: 'mensagens',
      icon: TrendingUp,
      color: 'text-emerald-500',
      bgColor: 'bg-emerald-500/10',
    },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Painel Administrativo"
        description="Visão geral de todas as organizações e métricas do sistema"
        actions={
          <Button asChild>
            <Link to="/admin/organizations/new">
              <Plus className="h-4 w-4 mr-2" />
              Nova Organização
            </Link>
          </Button>
        }
      />

      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.title}
              className="bg-card rounded-xl p-4 shadow-card"
            >
              <div className={`w-10 h-10 rounded-lg ${stat.bgColor} flex items-center justify-center mb-3`}>
                <Icon className={`h-5 w-5 ${stat.color}`} />
              </div>
              <p className="text-2xl font-bold text-foreground">
                {stat.value.toLocaleString('pt-BR')}
              </p>
              <p className="text-xs text-muted-foreground mt-1">{stat.title}</p>
              <p className="text-xs text-muted-foreground">{stat.subtitle}</p>
            </div>
          );
        })}
      </div>

      {/* Recent Organizations */}
      <div className="bg-card rounded-xl p-6 shadow-card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-lg font-semibold text-foreground">Organizações Recentes</h2>
            <p className="text-sm text-muted-foreground">Últimas organizações cadastradas</p>
          </div>
          <Button variant="outline" size="sm" asChild>
            <Link to="/admin/organizations">
              Ver todas
              <ArrowRight className="h-4 w-4 ml-2" />
            </Link>
          </Button>
        </div>

        {stats?.recent_organizations && stats.recent_organizations.length > 0 ? (
          <div className="space-y-4">
            {stats.recent_organizations.map((org) => (
              <div
                key={org.id}
                className="flex items-center justify-between p-4 rounded-lg border bg-background"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Building2 className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-foreground">{org.name}</p>
                      <Badge variant={org.is_active ? 'default' : 'secondary'}>
                        {org.is_active ? 'Ativa' : 'Inativa'}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {org.owner?.email ?? 'Sem owner'}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <p className="text-sm font-medium text-foreground">
                      {org.supporters_count?.toLocaleString('pt-BR') ?? 0} contatos
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {org.plan?.name ?? 'Sem plano'}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(org.created_at), {
                        addSuffix: true,
                        locale: ptBR,
                      })}
                    </p>
                  </div>
                  <Button variant="ghost" size="sm" asChild>
                    <Link to={`/admin/organizations/${org.id}`}>
                      <ArrowRight className="h-4 w-4" />
                    </Link>
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Building2 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">Nenhuma organização cadastrada</p>
            <Button className="mt-4" asChild>
              <Link to="/admin/organizations/new">
                <Plus className="h-4 w-4 mr-2" />
                Criar primeira organização
              </Link>
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
