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
  Search,
  Filter,
  Download,
  MoreHorizontal,
  Pencil,
  Trash2,
  Eye,
  UserCheck,
  UserMinus,
  ShieldOff,
  Loader2,
} from 'lucide-react';
import { Supporter } from '@/types';
import { supportersService } from '@/services/supporters';
import { SupporterDetailModal } from '@/components/supporters/SupporterDetailModal';
import { SupporterEditModal } from '@/components/supporters/SupporterEditModal';
import { toast } from 'sonner';

export default function BlacklistPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [detailModal, setDetailModal] = useState<{ open: boolean; supporterId: number | null }>({
    open: false,
    supporterId: null,
  });
  const [editModal, setEditModal] = useState<{ open: boolean; supporter: Supporter | null }>({
    open: false,
    supporter: null,
  });
  const [confirmDialog, setConfirmDialog] = useState<{
    open: boolean;
    action: 'unblacklist' | 'delete' | null;
    ids: number[];
  }>({ open: false, action: null, ids: [] });

  // Fetch blacklisted contacts
  const { data, isLoading, error } = useQuery({
    queryKey: ['blacklist', page, search],
    queryFn: () =>
      supportersService.list({
        contact_status: 'blacklist',
        search: search || undefined,
        page,
        page_size: 10,
      }),
  });

  // Mutations
  const unblacklistMutation = useMutation({
    mutationFn: (id: number) => supportersService.unblacklist(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blacklist'] });
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      queryClient.invalidateQueries({ queryKey: ['supporters'] });
      toast.success('Contato removido da Blacklist');
    },
    onError: () => toast.error('Erro ao remover da blacklist'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => supportersService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blacklist'] });
      toast.success('Contato excluído');
    },
    onError: () => toast.error('Erro ao excluir contato'),
  });

  const bulkUnblacklistMutation = useMutation({
    mutationFn: (ids: number[]) => supportersService.bulkUnblacklist(ids),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['blacklist'] });
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      queryClient.invalidateQueries({ queryKey: ['supporters'] });
      toast.success(data.message);
      setSelectedIds([]);
    },
    onError: () => toast.error('Erro ao remover da blacklist'),
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
        case 'unblacklist':
          unblacklistMutation.mutate(ids[0]);
          break;
        case 'delete':
          deleteMutation.mutate(ids[0]);
          break;
      }
    } else {
      switch (action) {
        case 'unblacklist':
          bulkUnblacklistMutation.mutate(ids);
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
          <p className="font-medium text-foreground">{item.name}</p>
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
      key: 'original_status',
      header: 'Status Original',
      render: (item: Supporter) => {
        // Check if they were a supporter or lead before blacklist
        const wasSupporter = item.tags.some(t => t.slug === 'apoiador');
        return (
          <StatusBadge
            status={wasSupporter ? 'success' : 'info'}
            label={wasSupporter ? 'Apoiador' : 'Lead'}
          />
        );
      },
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
                setConfirmDialog({ open: true, action: 'unblacklist', ids: [item.id] })
              }
              className="text-green-600"
            >
              <ShieldOff className="h-4 w-4 mr-2" />
              Remover da Blacklist
            </DropdownMenuItem>
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
          <p className="text-destructive mb-2">Erro ao carregar blacklist</p>
          <Button onClick={() => queryClient.invalidateQueries({ queryKey: ['blacklist'] })}>
            Tentar novamente
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Blacklist"
        description="Contatos bloqueados que não receberão mensagens"
        breadcrumbs={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Blacklist' }]}
        actions={
          <div className="flex items-center gap-3">
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Exportar
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
              setConfirmDialog({ open: true, action: 'unblacklist', ids: selectedIds })
            }
          >
            <ShieldOff className="h-4 w-4 mr-2" />
            Remover da Blacklist
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setSelectedIds([])}>
            Limpar seleção
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
        onSuccess={() => queryClient.invalidateQueries({ queryKey: ['blacklist'] })}
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
              {confirmDialog.action === 'unblacklist' && 'Remover da Blacklist'}
              {confirmDialog.action === 'delete' && 'Excluir Contato'}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {confirmDialog.action === 'unblacklist' &&
                `Tem certeza que deseja remover ${confirmDialog.ids.length} contato(s) da Blacklist? Eles voltarão a receber mensagens.`}
              {confirmDialog.action === 'delete' &&
                `Tem certeza que deseja excluir este contato? Esta ação não pode ser desfeita.`}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleConfirmAction}
              className={
                confirmDialog.action === 'delete'
                  ? 'bg-destructive hover:bg-destructive/90'
                  : 'bg-green-600 hover:bg-green-700'
              }
            >
              {confirmDialog.action === 'unblacklist' && 'Remover'}
              {confirmDialog.action === 'delete' && 'Excluir'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
