import { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { MessageTemplate } from '@/types';
import { templatesService } from '@/services/templates';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';

interface TemplateFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
  template?: MessageTemplate | null;
}

const initialFormData = {
  name: '',
  description: '',
  message_type: 'text',
  content: '',
};

export function TemplateFormModal({
  open,
  onOpenChange,
  onSuccess,
  template,
}: TemplateFormModalProps) {
  const queryClient = useQueryClient();
  const isEditing = !!template;

  const [formData, setFormData] = useState(initialFormData);

  useEffect(() => {
    if (template) {
      setFormData({
        name: template.name || '',
        description: template.description || '',
        message_type: template.message_type || template.type || 'text',
        content: template.content || '',
      });
    } else {
      setFormData(initialFormData);
    }
  }, [template, open]);

  const createMutation = useMutation({
    mutationFn: (data: Partial<MessageTemplate>) => templatesService.create(data),
    onSuccess: () => {
      toast.success('Template criado com sucesso');
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      handleClose();
      onSuccess?.();
    },
    onError: () => {
      toast.error('Erro ao criar template');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<MessageTemplate> }) =>
      templatesService.update(id, data),
    onSuccess: () => {
      toast.success('Template atualizado com sucesso');
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      handleClose();
      onSuccess?.();
    },
    onError: () => {
      toast.error('Erro ao atualizar template');
    },
  });

  const isPending = createMutation.isPending || updateMutation.isPending;

  const handleClose = () => {
    setFormData(initialFormData);
    onOpenChange(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      toast.error('Nome do template é obrigatório');
      return;
    }
    if (!formData.content.trim()) {
      toast.error('Conteúdo do template é obrigatório');
      return;
    }

    const data: Partial<MessageTemplate> = {
      name: formData.name.trim(),
      description: formData.description.trim(),
      message_type: formData.message_type,
      content: formData.content.trim(),
    };

    if (isEditing && template) {
      updateMutation.mutate({ id: template.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const handleChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <Dialog open={open} onOpenChange={(open) => { if (!open) handleClose(); }}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEditing ? 'Editar Template' : 'Novo Template'}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-5">

          <div className="space-y-2">
            <Label htmlFor="name">Nome do Template *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              placeholder="Ex: Aniversário, Convite Reunião..."
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="message_type">Tipo de Mensagem</Label>
            <Select
              value={formData.message_type}
              onValueChange={(value) => handleChange('message_type', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Selecione..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="text">Texto</SelectItem>
                <SelectItem value="image">Imagem</SelectItem>
                <SelectItem value="document">Documento</SelectItem>
                <SelectItem value="audio">Áudio</SelectItem>
                <SelectItem value="video">Vídeo</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Descrição</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              placeholder="Descrição opcional do template"
              rows={2}
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="content">Conteúdo da Mensagem *</Label>
              <span className="text-xs text-muted-foreground">
                {formData.content.length} caracteres
              </span>
            </div>
            <Textarea
              id="content"
              value={formData.content}
              onChange={(e) => handleChange('content', e.target.value)}
              placeholder="Escreva sua mensagem... Use {{name}}, {{city}}, {{neighborhood}} para personalizar"
              rows={8}
              required
            />
            <div className="flex flex-wrap gap-1.5 mt-1">
              <span className="text-xs text-muted-foreground">Variáveis:</span>
              {['{{name}}', '{{first_name}}', '{{city}}', '{{neighborhood}}'].map((v) => (
                <code
                  key={v}
                  className="px-1.5 py-0.5 rounded bg-primary/10 text-primary text-xs font-mono cursor-pointer hover:bg-primary/20"
                  onClick={() => handleChange('content', formData.content + v)}
                >
                  {v}
                </code>
              ))}
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isPending}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {isEditing ? 'Salvar' : 'Criar Template'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
