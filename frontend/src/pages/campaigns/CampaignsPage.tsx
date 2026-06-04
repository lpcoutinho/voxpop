import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Plus, Play, Pause, BarChart2, Trash2, Loader2 } from 'lucide-react';
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ConfirmDialog } from '@/components/shared/ConfirmDialog';
import { EmptyState } from '@/components/shared/EmptyState';
import { campaignsService } from '@/services/campaigns';
import { Campaign, CampaignStatus } from '@/types';
import { toast } from 'sonner';

const STATUS_LABELS: Record<string, string> = {
  draft: 'Rascunho',
  scheduled: 'Agendada',
  running: 'Em Andamento',
  paused: 'Pausada',
  completed: 'Concluída',
  cancelled: 'Cancelada',
  failed: 'Falhou',
};

const STATUS_COLORS: Record<string, string> = {
  running: 'bg-primary/10 text-primary hover:bg-primary/20',
  completed: 'bg-success/10 text-success hover:bg-success/20',
  failed: 'bg-destructive/10 text-destructive hover:bg-destructive/20',
  draft: 'bg-muted text-muted-foreground hover:bg-muted/80',
  paused: 'bg-warning/10 text-warning hover:bg-warning/20',
  scheduled: 'bg-info/10 text-info hover:bg-info/20',
  cancelled: 'bg-muted text-muted-foreground hover:bg-muted/80',
};

export default function CampaignsPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [deleteCampaign, setDeleteCampaign] = useState<Campaign | null>(null);

  const { data: campaigns, isLoading } = useQuery({
    queryKey: ['campaigns'],
    queryFn: campaignsService.list,
    refetchInterval: 5000,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => campaignsService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
      setDeleteCampaign(null);
      toast.success('Campanha excluída com sucesso');
    },
    onError: () => {
      toast.error('Erro ao excluir campanha');
    },
  });

  const handleAction = async (id: number, action: 'start' | 'pause') => {
    try {
      if (action === 'start') {
        await campaignsService.start(id);
      } else {
        await campaignsService.pause(id);
      }
      toast.success(`Campanha ${action === 'start' ? 'iniciada' : 'pausada'} com sucesso!`);
      queryClient.invalidateQueries({ queryKey: ['campaigns'] });
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao processar ação.');
    }
  };

  const handleDelete = () => {
    if (!deleteCampaign) return;
    deleteMutation.mutate(deleteCampaign.id);
  };

  const filteredCampaigns = campaigns
    ? statusFilter === 'all'
      ? campaigns
      : campaigns.filter((c) => c.status === statusFilter)
    : [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

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

      <div className="flex items-center gap-2">
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filtrar por status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos os status</SelectItem>
            <SelectItem value="draft">Rascunho</SelectItem>
            <SelectItem value="scheduled">Agendada</SelectItem>
            <SelectItem value="running">Em Andamento</SelectItem>
            <SelectItem value="paused">Pausada</SelectItem>
            <SelectItem value="completed">Concluída</SelectItem>
            <SelectItem value="cancelled">Cancelada</SelectItem>
            <SelectItem value="failed">Falhou</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="bg-card rounded-lg border">
        {filteredCampaigns.length === 0 ? (
          <EmptyState
            icon={BarChart2}
            title="Nenhuma campanha encontrada"
            description={statusFilter !== 'all' ? 'Nenhuma campanha com este status.' : 'Crie sua primeira campanha para começar.'}
          />
        ) : (
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
              {filteredCampaigns.map((campaign) => {
                const progress = campaign.total_recipients > 0
                  ? (campaign.messages_sent / campaign.total_recipients) * 100
                  : 0;

                const statusKey = campaign.status || 'draft';
                const statusLabel = STATUS_LABELS[statusKey] || statusKey;

                return (
                  <TableRow key={campaign.id}>
                    <TableCell className="font-medium">
                      <Link to={`/campaigns/${campaign.id}`} className="hover:underline">
                        {campaign.name}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary" className={STATUS_COLORS[statusKey]}>
                        {statusLabel}
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
                    <TableCell className="text-muted-foreground text-sm">
                      {campaign.whatsapp_session_name || '-'}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {format(new Date(campaign.created_at), "d MMM, HH:mm", { locale: ptBR })}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        {(statusKey === 'draft' || statusKey === 'paused' || statusKey === 'failed') && (
                          <Button size="sm" variant="ghost" onClick={() => handleAction(campaign.id, 'start')}>
                            <Play className="h-4 w-4 text-green-600" />
                          </Button>
                        )}
                        {statusKey === 'running' && (
                          <Button size="sm" variant="ghost" onClick={() => handleAction(campaign.id, 'pause')}>
                            <Pause className="h-4 w-4 text-yellow-600" />
                          </Button>
                        )}
                        <Link to={`/campaigns/${campaign.id}`}>
                          <Button size="sm" variant="ghost">
                            <BarChart2 className="h-4 w-4" />
                          </Button>
                        </Link>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setDeleteCampaign(campaign)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </div>

      <ConfirmDialog
        open={!!deleteCampaign}
        onOpenChange={(open) => !open && setDeleteCampaign(null)}
        title="Excluir Campanha"
        description={`Tem certeza que deseja excluir a campanha "${deleteCampaign?.name}"? Ela será ocultada da lista e poderá ser restaurada posteriormente.`}
        confirmLabel="Excluir"
        onConfirm={handleDelete}
        variant="destructive"
      />
    </div>
  );
}
