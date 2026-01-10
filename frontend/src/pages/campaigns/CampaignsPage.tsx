import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Plus, Play, Pause, BarChart2 } from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { api } from '@/services/api';
import { toast } from 'sonner';

interface Campaign {
  id: number;
  name: string;
  status: string;
  status_display: string;
  total_recipients: number;
  messages_sent: number;
  messages_failed: number;
  created_at: string;
  whatsapp_session_name: string;
}

export default function CampaignsPage() {
  const { data: campaigns, isLoading, refetch } = useQuery<Campaign[]>({
    queryKey: ['campaigns'],
    queryFn: async () => {
      const { data } = await api.get('/campaigns/');
      // Handle pagination if needed, for now assuming array or results
      return Array.isArray(data) ? data : data.results;
    },
    refetchInterval: 5000, // Auto-refresh para ver progresso
  });

  const handleAction = async (id: number, action: 'start' | 'pause') => {
    try {
      await api.post(`/campaigns/${id}/${action}/`);
      toast.success(`Campanha ${action === 'start' ? 'iniciada' : 'pausada'} com sucesso!`);
      refetch();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao processar ação.');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'default'; // primary
      case 'completed': return 'success'; // green (custom class needed or use outline with color)
      case 'failed': return 'destructive';
      case 'draft': return 'secondary';
      case 'paused': return 'warning'; // yellow (custom)
      default: return 'outline';
    }
  };

  if (isLoading) return <div>Carregando...</div>;

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Campanhas" 
        description="Gerencie seus disparos em massa."
        actions={
          <Link to="/campaigns/new">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Nova Campanha
            </Button>
          </Link>
        }
      />

      <div className="bg-card rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nome</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Progresso</TableHead>
              <TableHead>Sessão</TableHead>
              <TableHead>Criada em</TableHead>
              <TableHead className="text-right">Ações</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {campaigns?.map((campaign) => {
              const progress = campaign.total_recipients > 0 
                ? (campaign.messages_sent / campaign.total_recipients) * 100 
                : 0;

              return (
                <TableRow key={campaign.id}>
                  <TableCell className="font-medium">
                    <Link to={`/campaigns/${campaign.id}`} className="hover:underline">
                      {campaign.name}
                    </Link>
                  </TableCell>
                  <TableCell>
                    <Badge variant={getStatusColor(campaign.status) as any}>
                      {campaign.status_display}
                    </Badge>
                  </TableCell>
                  <TableCell className="w-[200px]">
                    <div className="space-y-1">
                      <Progress value={progress} className="h-2" />
                      <div className="text-xs text-muted-foreground flex justify-between">
                        <span>{Math.round(progress)}%</span>
                        <span>{campaign.messages_sent}/{campaign.total_recipients}</span>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>{campaign.whatsapp_session_name}</TableCell>
                  <TableCell>
                    {format(new Date(campaign.created_at), "d MMM, HH:mm", { locale: ptBR })}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      {campaign.status === 'draft' || campaign.status === 'paused' || campaign.status === 'failed' ? (
                        <Button size="sm" variant="ghost" onClick={() => handleAction(campaign.id, 'start')}>
                          <Play className="h-4 w-4 text-green-600" />
                        </Button>
                      ) : null}
                      
                      {campaign.status === 'running' && (
                        <Button size="sm" variant="ghost" onClick={() => handleAction(campaign.id, 'pause')}>
                          <Pause className="h-4 w-4 text-yellow-600" />
                        </Button>
                      )}

                      <Link to={`/campaigns/${campaign.id}`}>
                        <Button size="sm" variant="ghost">
                          <BarChart2 className="h-4 w-4" />
                        </Button>
                      </Link>
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
            {campaigns?.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                  Nenhuma campanha encontrada.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}