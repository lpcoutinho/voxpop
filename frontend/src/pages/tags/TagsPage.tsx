import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { ConfirmDialog } from '@/components/shared/ConfirmDialog';
import { Badge } from '@/components/ui/badge';
import { Plus, Pencil, Trash2, Users, Loader2, Lock } from 'lucide-react';
import { Tag } from '@/types';
import { toast } from 'sonner';
import { tagsService } from '@/services/supporters';

const colorOptions = [
  '#22c55e', '#6366f1', '#f59e0b', '#ec4899', '#14b8a6', '#8b5cf6',
  '#ef4444', '#3b82f6', '#84cc16', '#f97316', '#06b6d4', '#a855f7',
];

export default function TagsPage() {
  const queryClient = useQueryClient();
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingTag, setEditingTag] = useState<Tag | null>(null);
  const [deleteTag, setDeleteTag] = useState<Tag | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    color: colorOptions[0],
    description: '',
  });

  // Fetch tags from API
  const { data: tags = [], isLoading } = useQuery({
    queryKey: ['tags'],
    queryFn: tagsService.list,
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: { name: string; color: string; description?: string }) =>
      tagsService.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tags'] });
      setIsCreateOpen(false);
      resetForm();
      toast.success('Tag criada com sucesso');
    },
    onError: () => {
      toast.error('Erro ao criar tag');
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { name?: string; color?: string; description?: string } }) =>
      tagsService.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tags'] });
      setEditingTag(null);
      resetForm();
      toast.success('Tag atualizada com sucesso');
    },
    onError: () => {
      toast.error('Erro ao atualizar tag');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => tagsService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tags'] });
      setDeleteTag(null);
      toast.success('Tag excluída com sucesso');
    },
    onError: () => {
      toast.error('Erro ao excluir tag. Tags de sistema não podem ser excluídas.');
    },
  });

  const resetForm = () => {
    setFormData({ name: '', color: colorOptions[0], description: '' });
  };

  const handleCreate = () => {
    if (!formData.name.trim()) {
      toast.error('O nome da tag é obrigatório');
      return;
    }
    createMutation.mutate({
      name: formData.name,
      color: formData.color,
      description: formData.description || undefined,
    });
  };

  const handleEdit = () => {
    if (!editingTag || !formData.name.trim()) return;
    updateMutation.mutate({
      id: editingTag.id,
      data: {
        name: formData.name,
        color: formData.color,
        description: formData.description || undefined,
      },
    });
  };

  const handleDelete = () => {
    if (!deleteTag) return;
    deleteMutation.mutate(deleteTag.id);
  };

  const openEdit = (tag: Tag) => {
    setEditingTag(tag);
    setFormData({
      name: tag.name,
      color: tag.color,
      description: tag.description || '',
    });
  };

  const TagForm = ({ onSubmit, submitLabel, isSubmitting }: { onSubmit: () => void; submitLabel: string; isSubmitting?: boolean }) => (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">Nome *</Label>
        <Input
          id="name"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="Ex: Voluntário"
          disabled={isSubmitting}
        />
      </div>

      <div className="space-y-2">
        <Label>Cor</Label>
        <div className="flex flex-wrap gap-2">
          {colorOptions.map((color) => (
            <button
              key={color}
              type="button"
              onClick={() => setFormData({ ...formData, color })}
              disabled={isSubmitting}
              className={`w-8 h-8 rounded-full transition-all ${
                formData.color === color ? 'ring-2 ring-offset-2 ring-primary scale-110' : 'hover:scale-105'
              }`}
              style={{ backgroundColor: color }}
            />
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Descrição</Label>
        <Textarea
          id="description"
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          placeholder="Descrição opcional da tag..."
          rows={3}
          disabled={isSubmitting}
        />
      </div>

      <DialogFooter>
        <Button type="button" onClick={onSubmit} disabled={isSubmitting}>
          {isSubmitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
          {submitLabel}
        </Button>
      </DialogFooter>
    </div>
  );

  if (isLoading) {
    return (
      <div className="animate-fade-in">
        <PageHeader
          title="Tags"
          description="Organize seus apoiadores com tags personalizadas"
          breadcrumbs={[
            { label: 'Dashboard', href: '/dashboard' },
            { label: 'Tags' },
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
        title="Tags"
        description="Organize seus apoiadores com tags personalizadas"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Tags' },
        ]}
        actions={
          <Dialog open={isCreateOpen} onOpenChange={(open) => {
            setIsCreateOpen(open);
            if (!open) resetForm();
          }}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Nova Tag
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Criar Nova Tag</DialogTitle>
                <DialogDescription>
                  Crie uma tag para categorizar seus apoiadores
                </DialogDescription>
              </DialogHeader>
              <TagForm onSubmit={handleCreate} submitLabel="Criar Tag" isSubmitting={createMutation.isPending} />
            </DialogContent>
          </Dialog>
        }
      />

      {/* Empty State */}
      {tags.length === 0 ? (
        <div className="bg-card rounded-xl p-12 shadow-card text-center">
          <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
            <Users className="h-6 w-6 text-primary" />
          </div>
          <h3 className="font-semibold text-foreground mb-2">Nenhuma tag encontrada</h3>
          <p className="text-muted-foreground mb-4">Crie sua primeira tag para começar a organizar seus apoiadores.</p>
          <Button onClick={() => setIsCreateOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Nova Tag
          </Button>
        </div>
      ) : (
        /* Tags Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tags.map((tag) => (
            <div
              key={tag.id}
              className="bg-card rounded-xl p-5 shadow-card hover:shadow-card-hover transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div
                    className="w-4 h-4 rounded-full"
                    style={{ backgroundColor: tag.color }}
                  />
                  <h3 className="font-semibold text-foreground">{tag.name}</h3>
                  {tag.is_system && (
                    <Lock className="h-3 w-3 text-muted-foreground" title="Tag de sistema" />
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => openEdit(tag)}
                  >
                    <Pencil className="h-4 w-4" />
                  </Button>
                  {!tag.is_system && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive hover:text-destructive"
                      onClick={() => setDeleteTag(tag)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              </div>

              {tag.description && (
                <p className="text-sm text-muted-foreground mb-4 line-clamp-2">
                  {tag.description}
                </p>
              )}

              <div className="flex items-center gap-3 text-sm">
                <div className="flex items-center gap-1.5">
                  <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200 font-medium text-xs">
                    {(tag.leads_count || 0).toLocaleString()}
                  </Badge>
                  <span className="text-muted-foreground">Leads</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200 font-medium text-xs">
                    {(tag.apoiadores_count || 0).toLocaleString()}
                  </Badge>
                  <span className="text-muted-foreground">Apoiadores</span>
                </div>
                <div className="flex items-center gap-1.5 ml-auto">
                  <Users className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground font-medium">{(tag.supporters_count || 0).toLocaleString()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Edit Dialog */}
      <Dialog open={!!editingTag} onOpenChange={(open) => {
        if (!open) {
          setEditingTag(null);
          resetForm();
        }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Editar Tag</DialogTitle>
            <DialogDescription>
              Faça alterações na tag selecionada
            </DialogDescription>
          </DialogHeader>
          <TagForm onSubmit={handleEdit} submitLabel="Salvar Alterações" isSubmitting={updateMutation.isPending} />
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={!!deleteTag}
        onOpenChange={(open) => !open && setDeleteTag(null)}
        title="Excluir Tag"
        description={`Tem certeza que deseja excluir a tag "${deleteTag?.name}"? Esta ação não pode ser desfeita e a tag será removida de todos os apoiadores.`}
        confirmLabel="Excluir"
        onConfirm={handleDelete}
        variant="destructive"
      />
    </div>
  );
}
