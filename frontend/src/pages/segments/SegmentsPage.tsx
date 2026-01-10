import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { DataTable } from '@/components/shared/DataTable';
import { EmptyState } from '@/components/shared/EmptyState';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ConfirmDialog } from '@/components/shared/ConfirmDialog';
import { Badge } from '@/components/ui/badge';
import { Plus, MoreHorizontal, Pencil, Copy, Trash2, Filter, Users, Loader2, Eye } from 'lucide-react';
import { Segment } from '@/types';
import { toast } from 'sonner';
import { segmentsService } from '@/services/segments';
import { SegmentFormModal } from '@/components/segments/SegmentFormModal';
import { SegmentPreviewModal } from '@/components/segments/SegmentPreviewModal';

export default function SegmentsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [deleteSegment, setDeleteSegment] = useState<Segment | null>(null);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editModal, setEditModal] = useState<{ open: boolean; segment: Segment | null }>({
    open: false,
    segment: null,
  });
  const [previewModal, setPreviewModal] = useState<{ open: boolean; segment: Segment | null }>({
    open: false,
    segment: null,
  });

  // Fetch segments from API
  const { data: segments = [], isLoading } = useQuery({
    queryKey: ['segments'],
    queryFn: segmentsService.list,
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => segmentsService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['segments'] });
      setDeleteSegment(null);
      toast.success('Segmento excluido com sucesso');
    },
    onError: () => {
      toast.error('Erro ao excluir segmento. Verifique se nao esta em uso em campanhas ativas.');
    },
  });

  // Duplicate mutation
  const duplicateMutation = useMutation({
    mutationFn: (id: number) => segmentsService.duplicate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['segments'] });
      toast.success('Segmento duplicado com sucesso');
    },
    onError: () => {
      toast.error('Erro ao duplicar segmento');
    },
  });

  const handleDelete = () => {
    if (!deleteSegment) return;
    deleteMutation.mutate(deleteSegment.id);
  };

  const handleEdit = (segment: Segment) => {
    setEditModal({ open: true, segment });
  };

  const handleDuplicate = (segment: Segment) => {
    duplicateMutation.mutate(segment.id);
  };

  const handlePreview = (segment: Segment) => {
    setPreviewModal({ open: true, segment });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const columns = [
    {
      key: 'name',
      header: 'Segmento',
      render: (item: Segment) => (
        <div>
          <p className="font-medium text-foreground">{item.name}</p>
          {item.description && (
            <p className="text-sm text-muted-foreground line-clamp-1">{item.description}</p>
          )}
        </div>
      ),
    },
    {
      key: 'leads_count',
      header: 'Leads',
      render: (item: Segment) => (
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 font-medium">
            {(item.leads_count || 0).toLocaleString()}
          </Badge>
        </div>
      ),
    },
    {
      key: 'supporters_count',
      header: 'Apoiadores',
      render: (item: Segment) => (
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 font-medium">
            {(item.supporters_count || 0).toLocaleString()}
          </Badge>
        </div>
      ),
    },
    {
      key: 'total',
      header: 'Total',
      render: (item: Segment) => (
        <div className="flex items-center gap-2">
          <Users className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium text-foreground">
            {(item.cached_count || 0).toLocaleString()}
          </span>
        </div>
      ),
    },
    {
      key: 'created_at',
      header: 'Criado em',
      render: (item: Segment) => (
        <span className="text-sm text-muted-foreground">{formatDate(item.created_at)}</span>
      ),
    },
    {
      key: 'actions',
      header: '',
      className: 'w-12',
      render: (item: Segment) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => handlePreview(item)}>
              <Eye className="h-4 w-4 mr-2" />
              Ver Apoiadores
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleEdit(item)}>
              <Pencil className="h-4 w-4 mr-2" />
              Editar
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => handleDuplicate(item)}>
              <Copy className="h-4 w-4 mr-2" />
              Duplicar
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-destructive"
              onClick={() => setDeleteSegment(item)}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Excluir
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  if (isLoading) {
    return (
      <div className="animate-fade-in">
        <PageHeader
          title="Segmentos"
          description="Crie segmentos para organizar sua audiencia"
          breadcrumbs={[
            { label: 'Dashboard', href: '/dashboard' },
            { label: 'Segmentos' },
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
        title="Segmentos"
        description="Crie segmentos para organizar sua audiencia"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Segmentos' },
        ]}
        actions={
          <Button onClick={() => setCreateModalOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Novo Segmento
          </Button>
        }
      />

      {segments.length === 0 ? (
        <EmptyState
          icon={Filter}
          title="Nenhum segmento criado"
          description="Crie segmentos para filtrar e organizar seus apoiadores"
          action={{
            label: 'Criar Segmento',
            onClick: () => setCreateModalOpen(true),
          }}
        />
      ) : (
        <DataTable
          data={segments}
          columns={columns}
          pagination={{
            page,
            pageSize: 10,
            total: segments.length,
            onPageChange: setPage,
          }}
        />
      )}

      {/* Create Modal */}
      <SegmentFormModal
        open={createModalOpen}
        onOpenChange={setCreateModalOpen}
        onSuccess={() => queryClient.invalidateQueries({ queryKey: ['segments'] })}
      />

      {/* Edit Modal */}
      <SegmentFormModal
        open={editModal.open}
        onOpenChange={(open) => setEditModal({ open, segment: open ? editModal.segment : null })}
        segment={editModal.segment}
        onSuccess={() => queryClient.invalidateQueries({ queryKey: ['segments'] })}
      />

      {/* Preview Modal */}
      <SegmentPreviewModal
        open={previewModal.open}
        onOpenChange={(open) => setPreviewModal({ open, segment: open ? previewModal.segment : null })}
        segment={previewModal.segment}
      />

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!deleteSegment}
        onOpenChange={(open) => !open && setDeleteSegment(null)}
        title="Excluir Segmento"
        description={`Tem certeza que deseja excluir o segmento "${deleteSegment?.name}"? Esta acao nao pode ser desfeita.`}
        confirmLabel="Excluir"
        onConfirm={handleDelete}
        variant="destructive"
      />
    </div>
  );
}
