import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { SegmentFilters, Tag } from '@/types';
import { tagsService } from '@/services/supporters';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { X, Plus } from 'lucide-react';

interface FilterBuilderProps {
  filters: SegmentFilters;
  onChange: (filters: SegmentFilters) => void;
}

const STATES = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
  'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
  'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
];

const FILTER_FIELDS = [
  { key: 'contact_status', label: 'Status', type: 'status' },
  { key: 'city', label: 'Cidade', type: 'text' },
  { key: 'state', label: 'Estado', type: 'state' },
  { key: 'neighborhood', label: 'Bairro', type: 'text' },
  { key: 'gender', label: 'Genero', type: 'gender' },
  { key: 'tags', label: 'Tags (qualquer uma)', type: 'tags' },
  { key: 'tags_all', label: 'Tags (todas)', type: 'tags' },
  { key: 'age_min', label: 'Idade Minima', type: 'number' },
  { key: 'age_max', label: 'Idade Maxima', type: 'number' },
  { key: 'electoral_zone', label: 'Zona Eleitoral', type: 'text' },
  { key: 'electoral_section', label: 'Secao Eleitoral', type: 'text' },
  { key: 'source', label: 'Origem', type: 'source' },
] as const;

type FilterKey = typeof FILTER_FIELDS[number]['key'];

export function FilterBuilder({ filters, onChange }: FilterBuilderProps) {
  const [selectedField, setSelectedField] = useState<FilterKey | ''>('');

  // Fetch available tags
  const { data: tags = [] } = useQuery({
    queryKey: ['tags'],
    queryFn: tagsService.list,
  });

  // Filter out system tags
  const userTags = tags.filter(tag => !tag.is_system);

  // Get active filter keys - include all filters that were added (even empty ones)
  const activeFilters = Object.entries(filters).filter(
    ([_, value]) => value !== undefined
  );

  // Get available fields to add
  const availableFields = FILTER_FIELDS.filter(
    field => !activeFilters.some(([key]) => key === field.key)
  );

  const handleAddFilter = () => {
    if (!selectedField) return;

    const field = FILTER_FIELDS.find(f => f.key === selectedField);
    if (!field) return;

    let defaultValue: string | number | number[];
    switch (field.type) {
      case 'tags':
        defaultValue = [];
        break;
      case 'number':
        defaultValue = 0;
        break;
      default:
        defaultValue = '';
    }

    onChange({ ...filters, [selectedField]: defaultValue });
    setSelectedField('');
  };

  const handleRemoveFilter = (key: string) => {
    const newFilters = { ...filters };
    delete newFilters[key as keyof SegmentFilters];
    onChange(newFilters);
  };

  const handleUpdateFilter = (key: string, value: string | number | number[]) => {
    onChange({ ...filters, [key]: value });
  };

  const handleToggleTag = (filterKey: 'tags' | 'tags_all', tagId: number) => {
    const currentTags = (filters[filterKey] || []) as number[];
    const newTags = currentTags.includes(tagId)
      ? currentTags.filter(id => id !== tagId)
      : [...currentTags, tagId];
    handleUpdateFilter(filterKey, newTags);
  };

  const renderFilterInput = (key: string, value: unknown) => {
    const field = FILTER_FIELDS.find(f => f.key === key);
    if (!field) return null;

    switch (field.type) {
      case 'text':
        return (
          <Input
            value={value as string}
            onChange={(e) => handleUpdateFilter(key, e.target.value)}
            placeholder={`Digite ${field.label.toLowerCase()}`}
          />
        );

      case 'number':
        return (
          <Input
            type="number"
            min={0}
            max={120}
            value={value as number}
            onChange={(e) => handleUpdateFilter(key, parseInt(e.target.value) || 0)}
          />
        );

      case 'state':
        return (
          <Select
            value={value as string}
            onValueChange={(v) => handleUpdateFilter(key, v)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Selecione o estado" />
            </SelectTrigger>
            <SelectContent>
              {STATES.map(state => (
                <SelectItem key={state} value={state}>{state}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      case 'gender':
        return (
          <Select
            value={value as string}
            onValueChange={(v) => handleUpdateFilter(key, v)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Selecione o genero" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="M">Masculino</SelectItem>
              <SelectItem value="F">Feminino</SelectItem>
              <SelectItem value="O">Outro</SelectItem>
            </SelectContent>
          </Select>
        );

      case 'source':
        return (
          <Select
            value={value as string}
            onValueChange={(v) => handleUpdateFilter(key, v)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Selecione a origem" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="import">Importacao</SelectItem>
              <SelectItem value="form">Formulario</SelectItem>
              <SelectItem value="manual">Cadastro Manual</SelectItem>
              <SelectItem value="api">API</SelectItem>
            </SelectContent>
          </Select>
        );

      case 'status':
        return (
          <Select
            value={value as string}
            onValueChange={(v) => handleUpdateFilter(key, v)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Selecione o status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="lead">Lead</SelectItem>
              <SelectItem value="apoiador">Apoiador</SelectItem>
              <SelectItem value="blacklist">Blacklist</SelectItem>
            </SelectContent>
          </Select>
        );

      case 'tags':
        const selectedTagIds = (value || []) as number[];
        return (
          <div className="flex flex-wrap gap-2">
            {userTags.map(tag => {
              const isSelected = selectedTagIds.includes(tag.id);
              return (
                <Badge
                  key={tag.id}
                  variant={isSelected ? 'default' : 'outline'}
                  className="cursor-pointer transition-colors"
                  style={{
                    backgroundColor: isSelected ? tag.color : 'transparent',
                    borderColor: tag.color,
                    color: isSelected ? 'white' : tag.color,
                  }}
                  onClick={() => handleToggleTag(key as 'tags' | 'tags_all', tag.id)}
                >
                  {tag.name}
                  {isSelected && <X className="h-3 w-3 ml-1" />}
                </Badge>
              );
            })}
            {userTags.length === 0 && (
              <span className="text-sm text-muted-foreground">Nenhuma tag disponivel</span>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-4">
      {/* Active Filters */}
      {activeFilters.length > 0 && (
        <div className="space-y-3">
          {activeFilters.map(([key, value]) => {
            const field = FILTER_FIELDS.find(f => f.key === key);
            if (!field) return null;

            return (
              <div key={key} className="flex items-start gap-3 p-3 bg-muted/50 rounded-lg">
                <div className="flex-1 space-y-2">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium">{field.label}</Label>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveFilter(key)}
                      className="h-6 w-6 p-0 text-muted-foreground hover:text-destructive"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                  {renderFilterInput(key, value)}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add Filter */}
      {availableFields.length > 0 && (
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <Label className="text-sm text-muted-foreground">Adicionar filtro</Label>
            <Select
              value={selectedField}
              onValueChange={(v) => setSelectedField(v as FilterKey)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Selecione um campo" />
              </SelectTrigger>
              <SelectContent>
                {availableFields.map(field => (
                  <SelectItem key={field.key} value={field.key}>
                    {field.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button
            type="button"
            variant="outline"
            onClick={handleAddFilter}
            disabled={!selectedField}
          >
            <Plus className="h-4 w-4 mr-1" />
            Adicionar
          </Button>
        </div>
      )}

      {/* Empty State */}
      {activeFilters.length === 0 && (
        <div className="text-center py-6 text-muted-foreground">
          <p className="text-sm">Nenhum filtro adicionado</p>
          <p className="text-xs mt-1">Adicione filtros para segmentar seus apoiadores</p>
        </div>
      )}
    </div>
  );
}
