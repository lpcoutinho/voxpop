import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { ConfirmDialog } from '@/components/shared/ConfirmDialog';
import { Plus, Smartphone, QrCode, Power, PowerOff, Trash2, MessageSquare, Loader2 } from 'lucide-react';
import { WhatsAppSession, WhatsAppSessionStatus } from '@/types';
import { toast } from 'sonner';
import { whatsappService } from '@/services/whatsapp';

const statusIcons: Record<WhatsAppSessionStatus, string> = {
  connected: '🟢',
  connecting: '🟡',
  disconnected: '🔴',
  banned: '⚫',
};

export default function WhatsAppPage() {
  const queryClient = useQueryClient();
  // const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [connectingSession, setConnectingSession] = useState<WhatsAppSession | null>(null);
  const [disconnectSession, setDisconnectSession] = useState<WhatsAppSession | null>(null);
  const [deleteSession, setDeleteSession] = useState<WhatsAppSession | null>(null);
  const [qrCode, setQrCode] = useState<string | null>(null);

  /*
  const [formData, setFormData] = useState({
    name: '',
    daily_message_limit: 1000,
  });
  */

  // Fetch sessions from API
  const { data: sessions = [], isLoading } = useQuery({
    queryKey: ['whatsapp-sessions'],
    queryFn: whatsappService.list,
  });

  // Create mutation
  /*
  const createMutation = useMutation({
    mutationFn: (data: { name: string; daily_message_limit?: number }) =>
      whatsappService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['whatsapp-sessions'] });
      setIsCreateOpen(false);
      setFormData({ name: '', daily_message_limit: 1000 });
      toast.success('Sessão criada. Conecte escaneando o QR Code.');
    },
    onError: () => {
      toast.error('Erro ao criar sessão');
    },
  });
  */

  // Connect mutation
  const connectMutation = useMutation({
    mutationFn: (id: number) => whatsappService.connect(id),
    onSuccess: (data) => {
      if (data.qr_code) {
        setQrCode(data.qr_code);
      }
      queryClient.invalidateQueries({ queryKey: ['whatsapp-sessions'] });
    },
    onError: () => {
      toast.error('Erro ao conectar sessão');
      setConnectingSession(null);
    },
  });

  // Disconnect mutation
  const disconnectMutation = useMutation({
    mutationFn: (id: number) => whatsappService.disconnect(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['whatsapp-sessions'] });
      setDisconnectSession(null);
      toast.success('Sessão desconectada');
    },
    onError: () => {
      toast.error('Erro ao desconectar sessão');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => whatsappService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['whatsapp-sessions'] });
      setDeleteSession(null);
      toast.success('Sessão excluída');
    },
    onError: () => {
      toast.error('Erro ao excluir sessão');
    },
  });

  const formatPhone = (phone?: string) => {
    if (!phone) return '-';
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 13) {
      return `(${cleaned.slice(2, 4)}) ${cleaned.slice(4, 5)} ${cleaned.slice(5, 9)}-${cleaned.slice(9)}`;
    }
    return phone;
  };

  /*
  const handleCreate = () => {
    if (!formData.name.trim()) {
      toast.error('O nome da sessão é obrigatório');
      return;
    }
    createMutation.mutate({
      name: formData.name,
      daily_message_limit: formData.daily_message_limit,
    });
  };
  */

  const handleConnect = (session: WhatsAppSession) => {
    setConnectingSession(session);
    setQrCode(null);
    connectMutation.mutate(session.id);
  };

  const handleDisconnect = () => {
    if (!disconnectSession) return;
    disconnectMutation.mutate(disconnectSession.id);
  };

  const handleDelete = () => {
    if (!deleteSession) return;
    deleteMutation.mutate(deleteSession.id);
  };

  if (isLoading) {
    return (
      <div className="animate-fade-in">
        <PageHeader
          title="Sessões WhatsApp"
          description="Gerencie suas conexões do WhatsApp"
          breadcrumbs={[
            { label: 'Dashboard', href: '/dashboard' },
            { label: 'WhatsApp' },
          ]}
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
        title="Sessões WhatsApp"
        description="Gerencie suas conexões do WhatsApp"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'WhatsApp' },
        ]}
        /*
        actions={
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Nova Sessão
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Criar Nova Sessão</DialogTitle>
                <DialogDescription>
                  Configure uma nova sessão do WhatsApp para envio de mensagens
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="session-name">Nome da Sessão *</Label>
                  <Input
                    id="session-name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Ex: Principal, Backup..."
                    disabled={createMutation.isPending}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="daily-limit">Limite Diário de Mensagens</Label>
                  <Input
                    id="daily-limit"
                    type="number"
                    value={formData.daily_message_limit}
                    onChange={(e) => setFormData({ ...formData, daily_message_limit: parseInt(e.target.value) || 1000 })}
                    min={100}
                    max={5000}
                    disabled={createMutation.isPending}
                  />
                  <p className="text-xs text-muted-foreground">
                    Recomendado: 1000 mensagens/dia para evitar bloqueios
                  </p>
                </div>
              </div>
              <DialogFooter>
                <Button onClick={handleCreate} disabled={createMutation.isPending}>
                  {createMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  Criar Sessão
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        }
        */
      />

      {/* Empty State */}
      {sessions.length === 0 ? (
        <div className="bg-card rounded-xl p-12 shadow-card text-center">
          <div className="mx-auto w-12 h-12 rounded-full bg-success/10 flex items-center justify-center mb-4">
            <Smartphone className="h-6 w-6 text-success" />
          </div>
          <h3 className="font-semibold text-foreground mb-2">Nenhuma sessão configurada</h3>
          <p className="text-muted-foreground mb-4">Crie uma sessão para conectar seu WhatsApp.</p>
          {/*
          <Button onClick={() => setIsCreateOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Nova Sessão
          </Button>
          */}
        </div>
      ) : (
        <>
          {/* Sessions Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sessions.map((session) => (
              <div
                key={session.id}
                className="bg-card rounded-xl p-6 shadow-card hover:shadow-card-hover transition-shadow"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-success/10 flex items-center justify-center">
                      <Smartphone className="h-6 w-6 text-success" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-foreground">{session.name}</h3>
                      <p className="text-sm text-muted-foreground">
                        {formatPhone(session.phone_number)}
                      </p>
                    </div>
                  </div>
                  <span className="text-lg">{statusIcons[session.status]}</span>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Status</span>
                    <StatusBadge status={session.status} />
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Mensagens hoje</span>
                      <span className="font-medium text-foreground">
                        {session.messages_sent_today || 0} / {session.daily_message_limit || 1000}
                      </span>
                    </div>
                    <Progress
                      value={((session.messages_sent_today || 0) / (session.daily_message_limit || 1000)) * 100}
                      className="h-2"
                    />
                  </div>

                  <div className="flex items-center gap-2 pt-2">
                    {session.status === 'disconnected' ? (
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => handleConnect(session)}
                        disabled={connectMutation.isPending}
                      >
                        <QrCode className="h-4 w-4 mr-2" />
                        Conectar
                      </Button>
                    ) : session.status === 'connected' ? (
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1"
                        onClick={() => setDisconnectSession(session)}
                      >
                        <PowerOff className="h-4 w-4 mr-2" />
                        Desconectar
                      </Button>
                    ) : (
                      <Button variant="outline" size="sm" className="flex-1" disabled>
                        <Power className="h-4 w-4 mr-2 animate-pulse" />
                        Conectando...
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-destructive hover:text-destructive"
                      onClick={() => setDeleteSession(session)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Summary */}
          <div className="mt-8 bg-card rounded-xl p-6 shadow-card">
            <div className="flex items-center gap-3 mb-4">
              <MessageSquare className="h-5 w-5 text-primary" />
              <h3 className="font-semibold text-foreground">Resumo do Dia</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div>
                <p className="text-sm text-muted-foreground">Sessões Conectadas</p>
                <p className="text-2xl font-semibold text-foreground">
                  {sessions.filter(s => s.status === 'connected').length} / {sessions.length}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total de Mensagens</p>
                <p className="text-2xl font-semibold text-foreground">
                  {sessions.reduce((acc, s) => acc + (s.messages_sent_today || 0), 0).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Limite Total</p>
                <p className="text-2xl font-semibold text-foreground">
                  {sessions.reduce((acc, s) => acc + (s.daily_message_limit || 1000), 0).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Capacidade Usada</p>
                <p className="text-2xl font-semibold text-foreground">
                  {sessions.length > 0 ? Math.round(
                    (sessions.reduce((acc, s) => acc + (s.messages_sent_today || 0), 0) /
                      sessions.reduce((acc, s) => acc + (s.daily_message_limit || 1000), 0)) *
                      100
                  ) : 0}%
                </p>
              </div>
            </div>
          </div>
        </>
      )}

      {/* QR Code Dialog */}
      <Dialog open={!!connectingSession} onOpenChange={(open) => {
        if (!open) {
          setConnectingSession(null);
          setQrCode(null);
        }
      }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Conectar WhatsApp</DialogTitle>
            <DialogDescription>
              Escaneie o QR Code com seu WhatsApp para conectar
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col items-center py-6">
            <div className="w-64 h-64 bg-muted rounded-xl flex items-center justify-center mb-4">
              {qrCode ? (
                <img src={qrCode} alt="QR Code" className="w-full h-full object-contain" />
              ) : (
                <div className="text-center">
                  <QrCode className="h-32 w-32 text-muted-foreground mx-auto mb-4 animate-pulse" />
                  <p className="text-sm text-muted-foreground">Gerando QR Code...</p>
                </div>
              )}
            </div>
            <p className="text-sm text-muted-foreground text-center">
              Abra o WhatsApp no seu celular, vá em<br />
              <strong>Configurações → Aparelhos conectados</strong><br />
              e escaneie este código
            </p>
          </div>
        </DialogContent>
      </Dialog>

      {/* Disconnect Confirmation */}
      <ConfirmDialog
        open={!!disconnectSession}
        onOpenChange={(open) => !open && setDisconnectSession(null)}
        title="Desconectar Sessão"
        description={`Tem certeza que deseja desconectar a sessão "${disconnectSession?.name}"? Você precisará escanear o QR Code novamente para reconectar.`}
        confirmLabel="Desconectar"
        onConfirm={handleDisconnect}
        variant="destructive"
      />

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!deleteSession}
        onOpenChange={(open) => !open && setDeleteSession(null)}
        title="Excluir Sessão"
        description={`Tem certeza que deseja excluir a sessão "${deleteSession?.name}"? Esta ação não pode ser desfeita.`}
        confirmLabel="Excluir"
        onConfirm={handleDelete}
        variant="destructive"
      />
    </div>
  );
}
