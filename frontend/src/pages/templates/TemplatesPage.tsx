import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { DataTable } from '@/components/shared/DataTable';
import { EmptyState } from '@/components/shared/EmptyState';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ConfirmDialog } from '@/components/shared/ConfirmDialog';
import { Plus, MoreHorizontal, Pencil, Copy, Trash2, FileText, Eye, Loader2 } from 'lucide-react';
import { MessageTemplate } from '@/types';
import { toast } from 'sonner';
import { templatesService } from '@/services/templates';

const typeLabels: Record<string, string> = {
  text: 'Texto',
  image: 'Imagem',
  document: 'Documento',
  audio: 'Áudio',
  video: 'Vídeo',
};

const typeColors: Record<string, string> = {
  text: 'bg-primary/10 text-primary',
  image: 'bg-success/10 text-success',
  document: 'bg-warning/10 text-warning',
  audio: 'bg-purple-500/10 text-purple-500',
  video: 'bg-pink-500/10 text-pink-500',
};

export default function TemplatesPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [deleteTemplate, setDeleteTemplate] = useState<MessageTemplate | null>(null);

  // Fetch templates from API
  const { data: templates = [], isLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: templatesService.list,
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => templatesService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      setDeleteTemplate(null);
      toast.success('Template excluído com sucesso');
    },
    onError: () => {
      toast.error('Erro ao excluir template');
    },
  });

  // Duplicate mutation
  const duplicateMutation = useMutation({
    mutationFn: (id: number) => templatesService.duplicate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      toast.success('Template duplicado com sucesso');
    },
    onError: () => {
      toast.error('Erro ao duplicar template');
    },
  });

  const handleDelete = () => {
    if (!deleteTemplate) return;
    deleteMutation.mutate(deleteTemplate.id);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const truncateContent = (content: string, maxLength: number = 80) => {
    if (content.length <= maxLength) return content;
    return content.slice(0, maxLength) + '...';
  };

  const columns = [
    {
      key: 'name',
      header: 'Nome',
      render: (item: MessageTemplate) => (
        <p className="font-medium text-foreground">{item.name}</p>
      ),
    },
    {
      key: 'type',
      header: 'Tipo',
      render: (item: MessageTemplate) => {
        const type = item.message_type || item.type || 'text';
        return (
          <Badge variant="secondary" className={typeColors[type] || typeColors.text}>
            {typeLabels[type] || type}
          </Badge>
        );
      },
    },
    {
      key: 'content',
      header: 'Conteúdo',
      render: (item: MessageTemplate) => (
        <p className="text-sm text-muted-foreground max-w-md">
          {truncateContent(item.content)}
        </p>
      ),
    },
    {
      key: 'created_at',
      header: 'Criado em',
      render: (item: MessageTemplate) => (
        <span className="text-sm text-muted-foreground">{formatDate(item.created_at)}</span>
      ),
    },
    {
      key: 'actions',
      header: '',
      className: 'w-12',
      render: (item: MessageTemplate) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>
              <Eye className="h-4 w-4 mr-2" />
              Visualizar
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Pencil className="h-4 w-4 mr-2" />
              Editar
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => duplicateMutation.mutate(item.id)}>
              <Copy className="h-4 w-4 mr-2" />
              Duplicar
            </DropdownMenuItem>
            <DropdownMenuItem
              className="text-destructive"
              onClick={() => setDeleteTemplate(item)}
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
          title="Templates de Mensagem"
          description="Crie e gerencie seus modelos de mensagem"
          breadcrumbs={[
            { label: 'Dashboard', href: '/dashboard' },
            { label: 'Templates' },
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
        title="Templates de Mensagem"
        description="Crie e gerencie seus modelos de mensagem"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Templates' },
        ]}
        actions={
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Novo Template
          </Button>
        }
      />

      {/* Variables Info */}
      <div className="bg-card rounded-xl p-4 mb-6 shadow-card">
        <p className="text-sm text-muted-foreground mb-2">
          <strong className="text-foreground">Variáveis disponíveis:</strong> Use essas variáveis nos seus templates para personalizar as mensagens
        </p>
        <div className="flex flex-wrap gap-2">
          {['{{name}}', '{{first_name}}', '{{city}}', '{{neighborhood}}'].map((variable) => (
            <code
              key={variable}
              className="px-2 py-1 rounded bg-primary/10 text-primary text-sm font-mono"
            >
              {variable}
            </code>
          ))}
        </div>
      </div>

      {templates.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="Nenhum template criado"
          description="Crie templates para agilizar o envio de mensagens"
          action={{
            label: 'Criar Template',
            onClick: () => {},
          }}
        />
      ) : (
        <DataTable
          data={templates}
          columns={columns}
          pagination={{
            page,
            pageSize: 10,
            total: templates.length,
            onPageChange: setPage,
          }}
        />
      )}

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!deleteTemplate}
        onOpenChange={(open) => !open && setDeleteTemplate(null)}
        title="Excluir Template"
        description={`Tem certeza que deseja excluir o template "${deleteTemplate?.name}"? Esta ação não pode ser desfeita.`}
        confirmLabel="Excluir"
        onConfirm={handleDelete}
        variant="destructive"
      />
    </div>
  );
}
