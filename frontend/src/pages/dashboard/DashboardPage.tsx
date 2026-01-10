import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { StatCard } from '@/components/shared/StatCard';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Users, MessageSquare, Send, Eye, Megaphone, TrendingUp, Loader2 } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from 'recharts';
import { dashboardService, DashboardStats, DashboardMetrics, RecentActivity } from '@/services/dashboard';
import { campaignsService } from '@/services/campaigns';

export default function DashboardPage() {
  // Fetch dashboard stats
  const { data: stats, isLoading: isLoadingStats } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: dashboardService.getStats,
  });

  // Fetch metrics for chart (last 7 days)
  const { data: metrics = [], isLoading: isLoadingMetrics } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: () => dashboardService.getMetrics(),
  });

  // Fetch recent activities
  const { data: recentActivities = [], isLoading: isLoadingActivities } = useQuery({
    queryKey: ['dashboard-activities'],
    queryFn: () => dashboardService.getRecentActivities(5),
  });

  // Fetch campaigns for top campaigns chart
  const { data: campaigns = [], isLoading: isLoadingCampaigns } = useQuery({
    queryKey: ['dashboard-campaigns'],
    queryFn: () => campaignsService.list({ status: 'completed' }),
  });

  const isLoading = isLoadingStats || isLoadingMetrics || isLoadingActivities || isLoadingCampaigns;

  // Format metrics for line chart
  const messagesData = metrics.map((m: DashboardMetrics) => ({
    date: new Date(m.date).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }),
    sent: m.sent,
    delivered: m.delivered,
    read: m.read,
  }));

  // Calculate status data for pie chart
  const statusData = stats ? [
    { name: 'Entregues', value: stats.messages_delivered || 0, color: 'hsl(142, 71%, 45%)' },
    { name: 'Lidas', value: stats.messages_read || 0, color: 'hsl(239, 84%, 67%)' },
    { name: 'Falhas', value: stats.messages_failed || 0, color: 'hsl(0, 84%, 60%)' },
  ] : [];

  // Calculate campaigns engagement data
  const campaignsData = campaigns.slice(0, 5).map((campaign) => {
    const totalRecipients = campaign.total_recipients || 1;
    const messagesRead = campaign.messages_read || 0;
    const engagement = Math.round((messagesRead / totalRecipients) * 100);
    return {
      name: campaign.name.length > 15 ? campaign.name.substring(0, 15) + '...' : campaign.name,
      engagement,
    };
  }).sort((a, b) => b.engagement - a.engagement);

  // Format stats for display
  const formatNumber = (num: number | undefined) => {
    if (num === undefined) return '0';
    return num.toLocaleString('pt-BR');
  };

  const formatPercentage = (num: number | undefined) => {
    if (num === undefined) return '0%';
    return `${num.toFixed(1)}%`;
  };

  if (isLoading) {
    return (
      <div className="animate-fade-in">
        <PageHeader
          title="Dashboard"
          description="Visão geral da sua campanha"
        />
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Dashboard"
        description="Visão geral da sua campanha"
      />

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        <StatCard
          title="Total de Apoiadores"
          value={formatNumber(stats?.total_supporters)}
          icon={Users}
        />
        <StatCard
          title="Mensagens (Mês)"
          value={formatNumber(stats?.messages_sent)}
          icon={MessageSquare}
        />
        <StatCard
          title="Taxa de Entrega"
          value={formatPercentage(stats?.delivery_rate)}
          icon={Send}
        />
        <StatCard
          title="Taxa de Leitura"
          value={formatPercentage(stats?.read_rate)}
          icon={Eye}
        />
        <StatCard
          title="Campanhas Ativas"
          value={formatNumber(stats?.active_campaigns)}
          icon={Megaphone}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Line Chart - Messages over time */}
        <div className="lg:col-span-2 bg-card rounded-xl p-6 shadow-card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-foreground">Mensagens Enviadas</h3>
              <p className="text-sm text-muted-foreground">Últimos 7 dias</p>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-primary" />
                <span className="text-muted-foreground">Enviadas</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-success" />
                <span className="text-muted-foreground">Entregues</span>
              </div>
            </div>
          </div>
          {messagesData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={messagesData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  dataKey="date"
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                />
                <YAxis
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="sent"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2}
                  dot={{ fill: 'hsl(var(--primary))' }}
                />
                <Line
                  type="monotone"
                  dataKey="delivered"
                  stroke="hsl(var(--success))"
                  strokeWidth={2}
                  dot={{ fill: 'hsl(var(--success))' }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[280px] text-muted-foreground">
              Nenhuma mensagem enviada ainda
            </div>
          )}
        </div>

        {/* Pie Chart - Message Status */}
        <div className="bg-card rounded-xl p-6 shadow-card">
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-foreground">Status das Mensagens</h3>
            <p className="text-sm text-muted-foreground">Distribuição atual</p>
          </div>
          {statusData.some(d => d.value > 0) ? (
            <>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={statusData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {statusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '8px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex flex-col gap-2 mt-4">
                {statusData.map((item) => (
                  <div key={item.name} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                      <span className="text-muted-foreground">{item.name}</span>
                    </div>
                    <span className="font-medium text-foreground">{item.value.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-[280px] text-muted-foreground">
              Nenhuma mensagem enviada ainda
            </div>
          )}
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar Chart - Top Campaigns */}
        <div className="bg-card rounded-xl p-6 shadow-card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-foreground">Top Campanhas</h3>
              <p className="text-sm text-muted-foreground">Por taxa de engajamento</p>
            </div>
            <TrendingUp className="h-5 w-5 text-muted-foreground" />
          </div>
          {campaignsData.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={campaignsData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis type="number" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                <YAxis
                  type="category"
                  dataKey="name"
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={12}
                  width={100}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--card))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                  formatter={(value: number) => [`${value}%`, 'Engajamento']}
                />
                <Bar
                  dataKey="engagement"
                  fill="hsl(var(--primary))"
                  radius={[0, 4, 4, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-[240px] text-muted-foreground">
              Nenhuma campanha concluída ainda
            </div>
          )}
        </div>

        {/* Recent Activity */}
        <div className="bg-card rounded-xl p-6 shadow-card">
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-foreground">Atividade Recente</h3>
            <p className="text-sm text-muted-foreground">Últimas atualizações</p>
          </div>
          {recentActivities.length > 0 ? (
            <div className="space-y-4">
              {recentActivities.map((activity: RecentActivity) => (
                <div key={activity.id} className="flex items-start justify-between gap-4 pb-4 border-b border-border last:border-0 last:pb-0">
                  <div>
                    <p className="text-sm font-medium text-foreground">{activity.title}</p>
                    <p className="text-xs text-muted-foreground mt-1">{activity.time}</p>
                  </div>
                  {activity.status && <StatusBadge status={activity.status as any} />}
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center justify-center h-[200px] text-muted-foreground">
              Nenhuma atividade recente
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
