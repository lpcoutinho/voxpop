import { useQuery } from '@tanstack/react-query';
import { Supporter } from '@/types';
import { supportersService } from '@/services/supporters';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import {
  User,
  Phone,
  Mail,
  MapPin,
  Calendar,
  FileText,
  MessageSquare,
  Tag,
  Clock,
  CheckCircle,
  XCircle,
  Edit,
  Loader2,
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

interface SupporterDetailModalProps {
  supporterId: number | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onEdit?: (supporter: Supporter) => void;
}

const formatDate = (dateString: string | undefined) => {
  if (!dateString) return '-';
  try {
    return format(new Date(dateString), "dd 'de' MMMM 'de' yyyy", { locale: ptBR });
  } catch {
    return dateString;
  }
};

const formatDateTime = (dateString: string | undefined) => {
  if (!dateString) return '-';
  try {
    return format(new Date(dateString), "dd/MM/yyyy 'às' HH:mm", { locale: ptBR });
  } catch {
    return dateString;
  }
};

const getGenderLabel = (gender: string | undefined) => {
  switch (gender) {
    case 'M':
      return 'Masculino';
    case 'F':
      return 'Feminino';
    case 'O':
      return 'Outro';
    default:
      return '-';
  }
};

const getSourceLabel = (source: string) => {
  switch (source) {
    case 'import':
      return 'Importação';
    case 'form':
      return 'Formulário';
    case 'manual':
      return 'Manual';
    case 'api':
      return 'API';
    default:
      return source;
  }
};

const getStatusBadge = (supporter: Supporter) => {
  if (supporter.is_blacklisted) {
    return <Badge variant="destructive">Blacklist</Badge>;
  }
  if (supporter.is_supporter_status) {
    return <Badge className="bg-green-600">Apoiador</Badge>;
  }
  if (supporter.is_lead) {
    return <Badge className="bg-blue-600">Lead</Badge>;
  }
  return <Badge variant="secondary">Desconhecido</Badge>;
};

export function SupporterDetailModal({
  supporterId,
  open,
  onOpenChange,
  onEdit,
}: SupporterDetailModalProps) {
  // Fetch fresh data from server when modal opens
  const { data: supporter, isLoading } = useQuery({
    queryKey: ['supporter', supporterId],
    queryFn: () => supportersService.get(supporterId!),
    enabled: open && supporterId !== null,
    staleTime: 0, // Always fetch fresh data
  });

  if (!open) return null;

  const userTags = supporter?.tags.filter(tag => !tag.is_system) || [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        {isLoading || !supporter ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <>
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                <User className="h-6 w-6 text-primary" />
              </div>
              <div>
                <DialogTitle className="text-xl">{supporter.name}</DialogTitle>
                <div className="flex items-center gap-2 mt-1">
                  {getStatusBadge(supporter)}
                  {supporter.whatsapp_opt_in ? (
                    <Badge variant="outline" className="text-green-600 border-green-600">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Opt-in
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="text-red-600 border-red-600">
                      <XCircle className="h-3 w-3 mr-1" />
                      Sem Opt-in
                    </Badge>
                  )}
                </div>
              </div>
            </div>
            {onEdit && (
              <Button variant="outline" size="sm" onClick={() => onEdit(supporter)}>
                <Edit className="h-4 w-4 mr-2" />
                Editar
              </Button>
            )}
          </div>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* Informações de Contato */}
          <section>
            <h3 className="text-sm font-semibold text-muted-foreground mb-3 flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Informações de Contato
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Telefone</p>
                  <p className="font-medium">{supporter.phone}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Email</p>
                  <p className="font-medium">{supporter.email || '-'}</p>
                </div>
              </div>
            </div>
          </section>

          <Separator />

          {/* Dados Pessoais */}
          <section>
            <h3 className="text-sm font-semibold text-muted-foreground mb-3 flex items-center gap-2">
              <User className="h-4 w-4" />
              Dados Pessoais
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-muted-foreground">CPF</p>
                <p className="font-medium">{supporter.cpf || '-'}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Gênero</p>
                <p className="font-medium">{getGenderLabel(supporter.gender)}</p>
              </div>
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Data de Nascimento</p>
                  <p className="font-medium">
                    {supporter.birth_date ? formatDate(supporter.birth_date) : '-'}
                    {supporter.age && ` (${supporter.age} anos)`}
                  </p>
                </div>
              </div>
            </div>
          </section>

          <Separator />

          {/* Localização */}
          <section>
            <h3 className="text-sm font-semibold text-muted-foreground mb-3 flex items-center gap-2">
              <MapPin className="h-4 w-4" />
              Localização
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-muted-foreground">Cidade</p>
                <p className="font-medium">{supporter.city || '-'}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Estado</p>
                <p className="font-medium">{supporter.state || '-'}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Bairro</p>
                <p className="font-medium">{supporter.neighborhood || '-'}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">CEP</p>
                <p className="font-medium">{supporter.zip_code || '-'}</p>
              </div>
            </div>
          </section>

          <Separator />

          {/* Dados Eleitorais */}
          <section>
            <h3 className="text-sm font-semibold text-muted-foreground mb-3 flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Dados Eleitorais
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-muted-foreground">Zona Eleitoral</p>
                <p className="font-medium">{supporter.electoral_zone || '-'}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Seção Eleitoral</p>
                <p className="font-medium">{supporter.electoral_section || '-'}</p>
              </div>
            </div>
          </section>

          <Separator />

          {/* Tags */}
          <section>
            <h3 className="text-sm font-semibold text-muted-foreground mb-3 flex items-center gap-2">
              <Tag className="h-4 w-4" />
              Tags
            </h3>
            {userTags.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {userTags.map((tag) => (
                  <Badge
                    key={tag.id}
                    variant="outline"
                    style={{ borderColor: tag.color, color: tag.color }}
                  >
                    {tag.name}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Nenhuma tag atribuída</p>
            )}
          </section>

          <Separator />

          {/* Metadados */}
          <section>
            <h3 className="text-sm font-semibold text-muted-foreground mb-3 flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Informações do Sistema
            </h3>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-xs text-muted-foreground">Origem</p>
                <p className="font-medium">{getSourceLabel(supporter.source)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Criado em</p>
                <p className="font-medium">{formatDateTime(supporter.created_at)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Atualizado em</p>
                <p className="font-medium">{formatDateTime(supporter.updated_at)}</p>
              </div>
              {supporter.opt_in_date && (
                <div>
                  <p className="text-xs text-muted-foreground">Data do Opt-in</p>
                  <p className="font-medium">{formatDateTime(supporter.opt_in_date)}</p>
                </div>
              )}
            </div>
          </section>
        </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
