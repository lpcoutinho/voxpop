import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { DataTable } from '@/components/shared/DataTable';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Plus,
  Search,
  Filter,
  Upload,
  Download,
  MoreHorizontal,
  Pencil,
  Trash2,
  Eye,
  UserMinus,
  Ban,
  ShieldOff,
  Loader2,
} from 'lucide-react';
import { Supporter } from '@/types';
import { supportersService } from '@/services/supporters';
import { SupporterDetailModal } from '@/components/supporters/SupporterDetailModal';
import { SupporterEditModal } from '@/components/supporters/SupporterEditModal';
import { SupporterCreateModal } from '@/components/supporters/SupporterCreateModal';
import { ImportModal } from '@/components/supporters/ImportModal';
import { toast } from 'sonner';

export default function SupportersPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean;
    action: 'demote' | 'blacklist' | 'unblacklist' | 'delete' | null;
    ids: number[];
  }>({ open: false, action: null, ids: [] });
  const [detailModal, setDetailModal] = useState<{ open: boolean; supporterId: number | null }>({
    open: false,
    supporterId: null,
  });
  const [editModal, setEditModal] = useState<{ open: boolean; supporter: Supporter | null }>({
    open: false,
    supporter: null,
  });
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [importModalOpen, setImportModalOpen] = useState(false);

  // Fetch supporters (contacts with Apoiador tag)
  const { data, isLoading, error } = useQuery({
    queryKey: ['supporters', page, search],
    queryFn: () =>
      supportersService.list({
        contact_status: 'apoiador',
        search: search || undefined,
        page,
        page_size: 10,
      }),
  });

  // Mutations
  const demoteMutation = useMutation({
    mutationFn: (id: number) => supportersService.demote(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['supporters'] });
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      toast.success('Apoiador movido para Leads');
    },
    onError: () => toast.error('Erro ao mover para leads'),
  });

  const blacklistMutation = useMutation({
    mutationFn: (id: number) => supportersService.blacklist(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['supporters'] });
      toast.success('Apoiador adicionado a Blacklist');
    },
    onError: () => toast.error('Erro ao adicionar a blacklist'),
  });

  const unblacklistMutation = useMutation({
    mutationFn: (id: number) => supportersService.unblacklist(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['supporters'] });
      toast.success('Apoiador removido da Blacklist');
    },
    onError: () => toast.error('Erro ao remover da blacklist'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => supportersService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['supporters'] });
      toast.success('Apoiador excluido');
    },
    onError: () => toast.error('Erro ao excluir apoiador'),
  });

  const bulkDemoteMutation = useMutation({
    mutationFn: (ids: number[]) => supportersService.bulkDemote(ids),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['supporters'] });
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      toast.success(data.message);
      setSelectedIds([]);
    },
    onError: () => toast.error('Erro ao mover para leads'),
  });

  const bulkBlacklistMutation = useMutation({
    mutationFn: (ids: number[]) => supportersService.bulkBlacklist(ids),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['supporters'] });
      toast.success(data.message);
      setSelectedIds([]);
    },
    onError: () => toast.error('Erro ao adicionar a blacklist'),
  });

  const formatPhone = (phone: string) => {
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 13) {
      return `(${cleaned.slice(2, 4)}) ${cleaned.slice(4, 5)} ${cleaned.slice(5, 9)}-${cleaned.slice(9)}`;
    }
    return phone;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked && data?.results) {
      setSelectedIds(data.results.map((s) => s.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectOne = (id: number, checked: boolean) => {
    if (checked) {
      setSelectedIds([...selectedIds, id]);
    } else {
      setSelectedIds(selectedIds.filter((i) => i !== id));
    }
  };

  const handleConfirmAction = () => {
    const { action, ids } = confirmDialog;
    if (!action || ids.length === 0) return;

    if (ids.length === 1) {
      switch (action) {
        case 'demote':
          demoteMutation.mutate(ids[0]);
          break;
        case 'blacklist':
          blacklistMutation.mutate(ids[0]);
          break;
        case 'unblacklist':
          unblacklistMutation.mutate(ids[0]);
          break;
        case 'delete':
          deleteMutation.mutate(ids[0]);
          break;
      }
    } else {
      switch (action) {
        case 'demote':
          bulkDemoteMutation.mutate(ids);
          break;
        case 'blacklist':
          bulkBlacklistMutation.mutate(ids);
          break;
      }
    }
    setConfirmDialog({ open: false, action: null, ids: [] });
  };

  const handleViewDetails = (supporter: Supporter) => {
    setDetailModal({ open: true, supporterId: supporter.id });
  };

  const handleEdit = (supporter: Supporter) => {
    setDetailModal({ open: false, supporterId: null });
    setEditModal({ open: true, supporter });
  };

  const columns = [
    {
      key: 'select',
      header: () => (
        <Checkbox
          checked={data?.results?.length > 0 && selectedIds.length === data?.results?.length}
          onCheckedChange={handleSelectAll}
        />
      ),
      className: 'w-12',
      render: (item: Supporter) => (
        <Checkbox
          checked={selectedIds.includes(item.id)}
          onCheckedChange={(checked) => handleSelectOne(item.id, !!checked)}
        />
      ),
    },
    {
      key: 'name',
      header: 'Nome',
      render: (item: Supporter) => (
        <div>
          <div className="flex items-center gap-2">
            <p className="font-medium text-foreground">{item.name}</p>
            {item.is_blacklisted && (
              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                Blacklist
              </span>
            )}
          </div>
          <p className="text-sm text-muted-foreground">{item.email || '-'}</p>
        </div>
      ),
    },
    {
      key: 'phone',
      header: 'Telefone',
      render: (item: Supporter) => (
        <span className="text-foreground">{formatPhone(item.phone)}</span>
      ),
    },
    {
      key: 'city',
      header: 'Cidade',
      render: (item: Supporter) => (
        <span className="text-foreground">
          {item.city ? `${item.city}, ${item.state}` : '-'}
        </span>
      ),
    },
    {
      key: 'tags',
      header: 'Tags',
      render: (item: Supporter) => (
        <div className="flex flex-wrap gap-1">
          {item.tags
            .filter((tag) => !tag.is_system)
            .slice(0, 3)
            .map((tag) => (
              <span
                key={tag.id}
                className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
                style={{
                  backgroundColor: `${tag.color}20`,
                  color: tag.color,
                }}
              >
                {tag.name}
              </span>
            ))}
          {item.tags.filter((t) => !t.is_system).length > 3 && (
            <span className="text-xs text-muted-foreground">
              +{item.tags.filter((t) => !t.is_system).length - 3}
            </span>
          )}
        </div>
      ),
    },
    {
      key: 'whatsapp_opt_in',
      header: 'Opt-in',
      render: (item: Supporter) => (
        <StatusBadge
          status={item.whatsapp_opt_in ? 'success' : 'error'}
          label={item.whatsapp_opt_in ? 'Sim' : 'Nao'}
        />
      ),
    },
    {
      key: 'created_at',
      header: 'Cadastro',
      render: (item: Supporter) => (
        <span className="text-muted-foreground text-sm">{formatDate(item.created_at)}</span>
      ),
    },
    {
      key: 'actions',
      header: '',
      className: 'w-12',
      render: (item: Supporter) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => handleViewDetails(item)}>
              <Eye className="h-4 w-4 mr-2" />
              Ver detalhes
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleEdit(item)}>
              <Pencil className="h-4 w-4 mr-2" />
              Editar
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() =>
                setConfirmDialog({ open: true, action: 'demote', ids: [item.id] })
              }
              className="text-blue-600"
            >
              <UserMinus className="h-4 w-4 mr-2" />
              Mover para Leads
            </DropdownMenuItem>
            {item.is_blacklisted ? (
              <DropdownMenuItem
                onClick={() =>
                  setConfirmDialog({ open: true, action: 'unblacklist', ids: [item.id] })
                }
                className="text-green-600"
              >
                <ShieldOff className="h-4 w-4 mr-2" />
                Remover da Blacklist
              </DropdownMenuItem>
            ) : (
              <DropdownMenuItem
                onClick={() =>
                  setConfirmDialog({ open: true, action: 'blacklist', ids: [item.id] })
                }
                className="text-orange-600"
              >
                <Ban className="h-4 w-4 mr-2" />
                Adicionar a Blacklist
              </DropdownMenuItem>
            )}
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() =>
                setConfirmDialog({ open: true, action: 'delete', ids: [item.id] })
              }
              className="text-destructive"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Excluir
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <p className="text-destructive mb-2">Erro ao carregar apoiadores</p>
          <Button onClick={() => queryClient.invalidateQueries({ queryKey: ['supporters'] })}>
            Tentar novamente
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Apoiadores"
        description="Gerencie sua base de apoiadores confirmados"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Apoiadores' }]}
        actions={
          <div className="flex items-center gap-3">
            <Button variant="outline" onClick={() => setImportModalOpen(true)}>
              <Upload className="h-4 w-4 mr-2" />
              Importar
            </Button>
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Exportar
            </Button>
            <Button onClick={() => setCreateModalOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Novo Apoiador
            </Button>
          </div>
        }
      />

      {/* Bulk Actions */}
      {selectedIds.length > 0 && (
        <div className="flex items-center gap-4 mb-4 p-3 bg-muted rounded-lg">
          <span className="text-sm font-medium">
            {selectedIds.length} selecionado(s)
          </span>
          <Button
            size="sm"
            variant="outline"
            onClick={() =>
              setConfirmDialog({ open: true, action: 'demote', ids: selectedIds })
            }
          >
            <UserMinus className="h-4 w-4 mr-2" />
            Mover para Leads
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() =>
              setConfirmDialog({ open: true, action: 'blacklist', ids: selectedIds })
            }
          >
            <Ban className="h-4 w-4 mr-2" />
            Adicionar a Blacklist
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setSelectedIds([])}>
            Limpar selecao
          </Button>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar por nome, telefone ou email..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="pl-9"
          />
        </div>
        <Button variant="outline">
          <Filter className="h-4 w-4 mr-2" />
          Filtros
        </Button>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : (
        <DataTable
          data={data?.results || []}
          columns={columns}
          pagination={{
            page,
            pageSize: 10,
            total: data?.count || 0,
            onPageChange: setPage,
          }}
        />
      )}

      {/* Detail Modal */}
      <SupporterDetailModal
        supporterId={detailModal.supporterId}
        open={detailModal.open}
        onOpenChange={(open) => setDetailModal({ open, supporterId: open ? detailModal.supporterId : null })}
        onEdit={handleEdit}
      />

      {/* Edit Modal */}
      <SupporterEditModal
        supporter={editModal.supporter}
        open={editModal.open}
        onOpenChange={(open) => setEditModal({ open, supporter: open ? editModal.supporter : null })}
        onSuccess={() => queryClient.invalidateQueries({ queryKey: ['supporters'] })}
      />

      {/* Create Modal */}
      <SupporterCreateModal
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        onSuccess={() => queryClient.invalidateQueries({ queryKey: ['supporters'] })}
        defaultStatus="apoiador"
      />

      {/* Import Modal */}
      <ImportModal
        open={importModalOpen}
        onOpenChange={setImportModalOpen}
        onSuccess={() => queryClient.invalidateQueries({ queryKey: ['supporters'] })}
      />

      {/* Confirmation Dialog */}
      <AlertDialog
        open={confirmDialog.open}
        onOpenChange={(open) =>
          setConfirmDialog({ open, action: null, ids: [] })
        }
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {confirmDialog.action === 'demote' && 'Mover para Leads'}
              {confirmDialog.action === 'blacklist' && 'Adicionar a Blacklist'}
              {confirmDialog.action === 'unblacklist' && 'Remover da Blacklist'}
              {confirmDialog.action === 'delete' && 'Excluir Apoiador'}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {confirmDialog.action === 'demote' &&
                `Tem certeza que deseja mover ${confirmDialog.ids.length} apoiador(es) para Leads?`}
              {confirmDialog.action === 'blacklist' &&
                `Tem certeza que deseja adicionar ${confirmDialog.ids.length} apoiador(es) a Blacklist? Eles nao receberao mais mensagens.`}
              {confirmDialog.action === 'unblacklist' &&
                `Tem certeza que deseja remover este apoiador da Blacklist?`}
              {confirmDialog.action === 'delete' &&
                `Tem certeza que deseja excluir este apoiador? Esta acao nao pode ser desfeita.`}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmAction}
              className={
                confirmDialog.action === 'delete'
                  ? 'bg-destructive hover:bg-destructive/90'
                  : confirmDialog.action === 'blacklist'
                  ? 'bg-orange-600 hover:bg-orange-700'
                  : confirmDialog.action === 'unblacklist'
                  ? 'bg-green-600 hover:bg-green-700'
                  : 'bg-blue-600 hover:bg-blue-700'
              }
            >
              {confirmDialog.action === 'demote' && 'Mover'}
              {confirmDialog.action === 'blacklist' && 'Adicionar'}
              {confirmDialog.action === 'unblacklist' && 'Remover'}
              {confirmDialog.action === 'delete' && 'Excluir'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
