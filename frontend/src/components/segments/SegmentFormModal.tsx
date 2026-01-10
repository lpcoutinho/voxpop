import { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Segment, SegmentFilters, Supporter } from '@/types';
import { segmentsService, CreateSegmentData } from '@/services/segments';
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
import { Separator } from '@/components/ui/separator';
import { FilterBuilder } from './FilterBuilder';
import { toast } from 'sonner';
import { Loader2, Users, Eye } from 'lucide-react';

interface SegmentFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  segment?: Segment | null;
  onSuccess?: () => void;
}

export function SegmentFormModal({
  open,
  onOpenChange,
  segment,
  onSuccess,
}: SegmentFormModalProps) {
  const queryClient = useQueryClient();
  const isEditing = !!segment;

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [filters, setFilters] = useState<SegmentFilters>({});
  const [previewData, setPreviewData] = useState<{ count: number; sample: Supporter[] } | null>(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);

  // Reset form when modal opens/closes or segment changes
  useEffect(() => {
    if (open) {
      if (segment) {
        setName(segment.name);
        setDescription(segment.description || '');
        setFilters(segment.filters || {});
      } else {
        setName('');
        setDescription('');
        setFilters({});
      }
      setPreviewData(null);
    }
  }, [open, segment]);

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: CreateSegmentData) => segmentsService.create(data),
    onSuccess: () => {
      toast.success('Segmento criado com sucesso');
      queryClient.invalidateQueries({ queryKey: ['segments'] });
      onOpenChange(false);
      onSuccess?.();
    },
    onError: () => {
      toast.error('Erro ao criar segmento');
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<CreateSegmentData> }) =>
      segmentsService.update(id, data),
    onSuccess: () => {
      toast.success('Segmento atualizado com sucesso');
      queryClient.invalidateQueries({ queryKey: ['segments'] });
      onOpenChange(false);
      onSuccess?.();
    },
    onError: () => {
      toast.error('Erro ao atualizar segmento');
    },
  });

  const isPending = createMutation.isPending || updateMutation.isPending;

  const handlePreview = async () => {
    setIsLoadingPreview(true);
    try {
      const data = await segmentsService.previewFilters(filters);
      setPreviewData(data);
    } catch {
      toast.error('Erro ao carregar preview');
    } finally {
      setIsLoadingPreview(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      toast.error('Nome e obrigatorio');
      return;
    }

    const data: CreateSegmentData = {
      name: name.trim(),
      description: description.trim() || undefined,
      filters,
    };

    if (isEditing && segment) {
      updateMutation.mutate({ id: segment.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const formatPhone = (phone: string) => {
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 13) {
      return `(${cleaned.slice(2, 4)}) ${cleaned.slice(4, 5)} ${cleaned.slice(5, 9)}-${cleaned.slice(9)}`;
    }
    return phone;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? 'Editar Segmento' : 'Novo Segmento'}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Info */}
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nome *</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Nome do segmento"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Descricao</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Descricao opcional do segmento"
                rows={2}
              />
            </div>
          </div>

          <Separator />

          {/* Filters */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-base font-semibold">Filtros</Label>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handlePreview}
                disabled={isLoadingPreview}
              >
                {isLoadingPreview ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Eye className="h-4 w-4 mr-2" />
                )}
                Preview
              </Button>
            </div>

            <FilterBuilder filters={filters} onChange={setFilters} />
          </div>

          {/* Preview Results */}
          {previewData && (
            <>
              <Separator />
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm">
                  <Users className="h-4 w-4 text-muted-foreground" />
                  <span className="font-medium">{previewData.count.toLocaleString()}</span>
                  <span className="text-muted-foreground">apoiador(es) correspondem aos filtros</span>
                </div>

                {previewData.sample.length > 0 && (
                  <div className="bg-muted/50 rounded-lg p-3">
                    <p className="text-xs text-muted-foreground mb-2">Amostra (primeiros 10):</p>
                    <div className="space-y-1">
                      {previewData.sample.map((supporter) => (
                        <div key={supporter.id} className="flex items-center justify-between text-sm">
                          <span className="font-medium">{supporter.name}</span>
                          <span className="text-muted-foreground">{formatPhone(supporter.phone)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isPending}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {isEditing ? 'Salvar' : 'Criar Segmento'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
