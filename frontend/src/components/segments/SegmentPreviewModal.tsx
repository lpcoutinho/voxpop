import { useQuery } from '@tanstack/react-query';
import { Segment } from '@/types';
import { segmentsService } from '@/services/segments';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, Users, RefreshCw, Phone, Mail, MapPin } from 'lucide-react';

interface SegmentPreviewModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  segment: Segment | null;
}

export function SegmentPreviewModal({
  open,
  onOpenChange,
  segment,
}: SegmentPreviewModalProps) {
  // Fetch preview data
  const { data, isLoading, refetch, isRefetching } = useQuery({
    queryKey: ['segment-preview', segment?.id],
    queryFn: () => (segment ? segmentsService.preview(segment.id) : Promise.resolve(null)),
    enabled: open && !!segment,
  });

  const formatPhone = (phone: string) => {
    const cleaned = phone.replace(/\D/g, '');
    if (cleaned.length === 13) {
      return `(${cleaned.slice(2, 4)}) ${cleaned.slice(4, 5)} ${cleaned.slice(5, 9)}-${cleaned.slice(9)}`;
    }
    return phone;
  };

  const formatFilters = (filters: Record<string, unknown>) => {
    const labels: Record<string, string> = {
      contact_status: 'Status',
      city: 'Cidade',
      state: 'Estado',
      neighborhood: 'Bairro',
      gender: 'Genero',
      tags: 'Tags',
      tags_all: 'Todas as tags',
      age_min: 'Idade min',
      age_max: 'Idade max',
      electoral_zone: 'Zona eleitoral',
      electoral_section: 'Secao eleitoral',
      source: 'Origem',
    };

    const genderLabels: Record<string, string> = {
      M: 'Masculino',
      F: 'Feminino',
      O: 'Outro',
    };

    const sourceLabels: Record<string, string> = {
      import: 'Importacao',
      form: 'Formulario',
      manual: 'Manual',
      api: 'API',
    };

    const statusLabels: Record<string, string> = {
      lead: 'Lead',
      apoiador: 'Apoiador',
      blacklist: 'Blacklist',
    };

    return Object.entries(filters)
      .filter(([_, value]) => value !== undefined && value !== '' &&
        !(Array.isArray(value) && value.length === 0))
      .map(([key, value]) => {
        let displayValue: string;

        if (key === 'gender') {
          displayValue = genderLabels[value as string] || (value as string);
        } else if (key === 'source') {
          displayValue = sourceLabels[value as string] || (value as string);
        } else if (key === 'contact_status') {
          displayValue = statusLabels[value as string] || (value as string);
        } else if (Array.isArray(value)) {
          displayValue = `${value.length} selecionada(s)`;
        } else {
          displayValue = String(value);
        }

        return {
          label: labels[key] || key,
          value: displayValue,
        };
      });
  };

  if (!segment) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            {segment.name}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Description */}
          {segment.description && (
            <p className="text-muted-foreground">{segment.description}</p>
          )}

          {/* Filters Summary */}
          {Object.keys(segment.filters || {}).length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-muted-foreground">Filtros aplicados</h4>
              <div className="flex flex-wrap gap-2">
                {formatFilters(segment.filters).map(({ label, value }) => (
                  <Badge key={label} variant="secondary">
                    {label}: {value}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Count and Refresh */}
          <div className="flex items-center justify-between bg-muted/50 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center">
                <Users className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold">
                  {isLoading ? (
                    <Loader2 className="h-6 w-6 animate-spin" />
                  ) : (
                    (data?.count || 0).toLocaleString()
                  )}
                </p>
                <p className="text-sm text-muted-foreground">apoiadores no segmento</p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isLoading || isRefetching}
            >
              {isRefetching ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4 mr-2" />
              )}
              Atualizar
            </Button>
          </div>

          {/* Sample Supporters */}
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : data && data.sample.length > 0 ? (
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-muted-foreground">
                Amostra de apoiadores ({data.sample.length})
              </h4>
              <div className="divide-y">
                {data.sample.map((supporter) => (
                  <div key={supporter.id} className="py-3 first:pt-0 last:pb-0">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium">{supporter.name}</p>
                        <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Phone className="h-3 w-3" />
                            {formatPhone(supporter.phone)}
                          </span>
                          {supporter.email && (
                            <span className="flex items-center gap-1">
                              <Mail className="h-3 w-3" />
                              {supporter.email}
                            </span>
                          )}
                          {supporter.city && (
                            <span className="flex items-center gap-1">
                              <MapPin className="h-3 w-3" />
                              {supporter.city}{supporter.state ? `, ${supporter.state}` : ''}
                            </span>
                          )}
                        </div>
                      </div>
                      {/* Tags */}
                      {supporter.tags && supporter.tags.filter(t => !t.is_system).length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {supporter.tags.filter(t => !t.is_system).slice(0, 2).map(tag => (
                            <Badge
                              key={tag.id}
                              variant="outline"
                              className="text-xs"
                              style={{ borderColor: tag.color, color: tag.color }}
                            >
                              {tag.name}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Users className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>Nenhum apoiador corresponde aos filtros</p>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
