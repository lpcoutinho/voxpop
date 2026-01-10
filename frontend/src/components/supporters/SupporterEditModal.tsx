import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Supporter, Tag } from '@/types';
import { supportersService, tagsService, UpdateSupporterData } from '@/services/supporters';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { MaskedInput } from '@/components/ui/masked-input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { Loader2, X } from 'lucide-react';

interface SupporterEditModalProps {
  supporter: Supporter | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

const STATES = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
  'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
  'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
];

export function SupporterEditModal({
  supporter,
  open,
  onOpenChange,
  onSuccess,
}: SupporterEditModalProps) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<UpdateSupporterData>({});
  const [selectedTagIds, setSelectedTagIds] = useState<number[]>([]);

  // Fetch available tags
  const { data: tags = [] } = useQuery({
    queryKey: ['tags'],
    queryFn: tagsService.list,
  });

  // Filter out system tags for selection
  const userTags = tags.filter(tag => !tag.is_system);

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: UpdateSupporterData) =>
      supportersService.update(supporter!.id, data),
    onSuccess: () => {
      toast.success('Contato atualizado com sucesso');
      queryClient.invalidateQueries({ queryKey: ['supporters'] });
      queryClient.invalidateQueries({ queryKey: ['leads'] });
      queryClient.invalidateQueries({ queryKey: ['blacklist'] });
      onOpenChange(false);
      onSuccess?.();
    },
    onError: (error: unknown) => {
      // Try to extract error message from axios response
      let message = 'Erro ao atualizar contato';
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: Record<string, unknown> } };
        if (axiosError.response?.data) {
          const data = axiosError.response.data;
          // Map field names to Portuguese labels
          const fieldLabels: Record<string, string> = {
            name: 'Nome',
            phone: 'Telefone',
            email: 'Email',
            cpf: 'CPF',
            city: 'Cidade',
            state: 'Estado',
            neighborhood: 'Bairro',
            zip_code: 'CEP',
            electoral_zone: 'Zona Eleitoral',
            electoral_section: 'Seção Eleitoral',
            birth_date: 'Data de Nascimento',
            gender: 'Gênero',
            whatsapp_opt_in: 'Opt-in WhatsApp',
            tag_ids: 'Tags',
          };
          // Build error messages with field names
          const errorMessages: string[] = [];
          for (const [field, errors] of Object.entries(data)) {
            const label = fieldLabels[field] || field;
            if (Array.isArray(errors)) {
              errorMessages.push(`${label}: ${errors[0]}`);
            } else if (typeof errors === 'string') {
              errorMessages.push(`${label}: ${errors}`);
            }
          }
          message = errorMessages.length > 0 ? errorMessages.join('\n') : message;
        }
      } else if (error instanceof Error) {
        message = error.message;
      }
      toast.error(message);
    },
  });

  // Initialize form when supporter changes
  useEffect(() => {
    if (supporter) {
      setFormData({
        name: supporter.name,
        phone: supporter.phone,
        email: supporter.email || '',
        cpf: supporter.cpf || '',
        city: supporter.city || '',
        state: supporter.state || '',
        neighborhood: supporter.neighborhood || '',
        zip_code: supporter.zip_code || '',
        electoral_zone: supporter.electoral_zone || '',
        electoral_section: supporter.electoral_section || '',
        birth_date: supporter.birth_date || '',
        gender: supporter.gender,
        whatsapp_opt_in: supporter.whatsapp_opt_in,
      });
      // Only select non-system tags
      setSelectedTagIds(
        supporter.tags
          .filter(tag => !tag.is_system)
          .map(tag => tag.id)
      );
    }
  }, [supporter]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!supporter) return;

    // Clean up empty strings to undefined
    const cleanedData: UpdateSupporterData = {
      name: formData.name,
      phone: formData.phone,
      whatsapp_opt_in: formData.whatsapp_opt_in,
      tag_ids: selectedTagIds,
    };

    // Only include optional fields if they have values
    if (formData.email) cleanedData.email = formData.email;
    if (formData.cpf) cleanedData.cpf = formData.cpf;
    if (formData.city) cleanedData.city = formData.city;
    if (formData.state) cleanedData.state = formData.state;
    if (formData.neighborhood) cleanedData.neighborhood = formData.neighborhood;
    if (formData.zip_code) cleanedData.zip_code = formData.zip_code;
    if (formData.electoral_zone) cleanedData.electoral_zone = formData.electoral_zone;
    if (formData.electoral_section) cleanedData.electoral_section = formData.electoral_section;
    if (formData.birth_date) cleanedData.birth_date = formData.birth_date;
    if (formData.gender) cleanedData.gender = formData.gender;

    updateMutation.mutate(cleanedData);
  };

  const handleChange = (field: keyof UpdateSupporterData, value: string | boolean) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const toggleTag = (tagId: number) => {
    setSelectedTagIds(prev =>
      prev.includes(tagId)
        ? prev.filter(id => id !== tagId)
        : [...prev, tagId]
    );
  };

  if (!supporter) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Editar Contato</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Dados Básicos */}
          <section>
            <h3 className="text-sm font-semibold text-muted-foreground mb-3">
              Dados Básicos
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <Label htmlFor="name">Nome *</Label>
                <Input
                  id="name"
                  value={formData.name || ''}
                  onChange={(e) => handleChange('name', e.target.value)}
                  required
                />
              </div>
              <div>
                <Label htmlFor="phone">Telefone *</Label>
                <MaskedInput
                  id="phone"
                  mask="phone"
                  value={formData.phone || ''}
                  onValueChange={(value) => handleChange('phone', value)}
                  placeholder="(11) 9 9999-9999"
                  required
                />
              </div>
              <div>
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email || ''}
                  onChange={(e) => handleChange('email', e.target.value)}
                />
              </div>
            </div>
          </section>

          <Separator />

          {/* Dados Pessoais */}
          <section>
            <h3 className="text-sm font-semibold text-muted-foreground mb-3">
              Dados Pessoais
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="cpf">CPF</Label>
                <MaskedInput
                  id="cpf"
                  mask="cpf"
                  value={formData.cpf || ''}
                  onValueChange={(value) => handleChange('cpf', value)}
                  placeholder="000.000.000-00"
                />
              </div>
              <div>
                <Label htmlFor="gender">Gênero</Label>
                <Select
                  value={formData.gender || ''}
                  onValueChange={(value) => handleChange('gender', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione..." />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="M">Masculino</SelectItem>
                    <SelectItem value="F">Feminino</SelectItem>
                    <SelectItem value="O">Outro</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="birth_date">Data de Nascimento</Label>
                <Input
                  id="birth_date"
                  type="date"
                  value={formData.birth_date || ''}
                  onChange={(e) => handleChange('birth_date', e.target.value)}
                />
              </div>
            </div>
          </section>

          <Separator />

          {/* Localização */}
          <section>
            <h3 className="text-sm font-semibold text-muted-foreground mb-3">
              Localização
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="city">Cidade</Label>
                <Input
                  id="city"
                  value={formData.city || ''}
                  onChange={(e) => handleChange('city', e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="state">Estado</Label>
                <Select
                  value={formData.state || ''}
                  onValueChange={(value) => handleChange('state', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Selecione..." />
                  </SelectTrigger>
                  <SelectContent>
                    {STATES.map(state => (
                      <SelectItem key={state} value={state}>{state}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="neighborhood">Bairro</Label>
                <Input
                  id="neighborhood"
                  value={formData.neighborhood || ''}
                  onChange={(e) => handleChange('neighborhood', e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="zip_code">CEP</Label>
                <MaskedInput
                  id="zip_code"
                  mask="cep"
                  value={formData.zip_code || ''}
                  onValueChange={(value) => handleChange('zip_code', value)}
                  placeholder="00000-000"
                />
              </div>
            </div>
          </section>

          <Separator />

          {/* Dados Eleitorais */}
          <section>
            <h3 className="text-sm font-semibold text-muted-foreground mb-3">
              Dados Eleitorais
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="electoral_zone">Zona Eleitoral</Label>
                <Input
                  id="electoral_zone"
                  value={formData.electoral_zone || ''}
                  onChange={(e) => handleChange('electoral_zone', e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="electoral_section">Seção Eleitoral</Label>
                <Input
                  id="electoral_section"
                  value={formData.electoral_section || ''}
                  onChange={(e) => handleChange('electoral_section', e.target.value)}
                />
              </div>
            </div>
          </section>

          <Separator />

          {/* Configurações */}
          <section>
            <h3 className="text-sm font-semibold text-muted-foreground mb-3">
              Configurações
            </h3>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="whatsapp_opt_in"
                checked={formData.whatsapp_opt_in || false}
                onCheckedChange={(checked) => handleChange('whatsapp_opt_in', !!checked)}
              />
              <Label htmlFor="whatsapp_opt_in" className="cursor-pointer">
                Opt-in WhatsApp (consentimento para receber mensagens)
              </Label>
            </div>
          </section>

          <Separator />

          {/* Tags */}
          <section>
            <h3 className="text-sm font-semibold text-muted-foreground mb-3">
              Tags
            </h3>
            {userTags.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {userTags.map((tag) => {
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
                      onClick={() => toggleTag(tag.id)}
                    >
                      {tag.name}
                      {isSelected && <X className="h-3 w-3 ml-1" />}
                    </Badge>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Nenhuma tag disponível</p>
            )}
          </section>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={updateMutation.isPending}
            >
              Cancelar
            </Button>
            <Button type="submit" disabled={updateMutation.isPending}>
              {updateMutation.isPending && (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              )}
              Salvar
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
