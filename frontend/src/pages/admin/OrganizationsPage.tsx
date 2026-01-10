import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { organizationsService, plansService } from '@/services/admin';
import { Organization } from '@/types';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
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
import { toast } from 'sonner';
import {
  Building2,
  Plus,
  Search,
  MoreHorizontal,
  Edit,
  Power,
  Loader2,
  Users,
  Megaphone,
} from 'lucide-react';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export default function OrganizationsPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [planFilter, setPlanFilter] = useState<string>('all');
  const [page, setPage] = useState(1);
  const [toggleDialog, setToggleDialog] = useState<Organization | null>(null);

  // Fetch organizations
  const { data, isLoading } = useQuery({
    queryKey: ['admin', 'organizations', { search, status: statusFilter, plan: planFilter, page }],
    queryFn: () => organizationsService.list({
      search: search || undefined,
      is_active: statusFilter === 'all' ? undefined : statusFilter === 'active',
      plan_id: planFilter === 'all' ? undefined : Number(planFilter),
      page,
      page_size: 20,
    }),
  });

  // Fetch plans for filter
  const { data: plansData } = useQuery({
    queryKey: ['admin', 'plans'],
    queryFn: plansService.list,
  });
  // Handle both array and paginated response formats
  const plans = Array.isArray(plansData) ? plansData : [];

  // Toggle status mutation
  const toggleMutation = useMutation({
    mutationFn: (id: number) => organizationsService.toggleStatus(id),
    onSuccess: (data) => {
      toast.success(
        data.is_active
          ? 'Organização ativada com sucesso'
          : 'Organização desativada com sucesso'
      );
      queryClient.invalidateQueries({ queryKey: ['admin', 'organizations'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'stats'] });
      setToggleDialog(null);
    },
    onError: () => {
      toast.error('Erro ao alterar status da organização');
    },
  });

  const organizations = data?.results ?? [];
  const totalCount = data?.count ?? 0;
  const totalPages = Math.ceil(totalCount / 20);

  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Organizações"
        description={`${totalCount} organizações cadastradas`}
        actions={
          <Button asChild>
            <Link to="/admin/organizations/new">
              <Plus className="h-4 w-4 mr-2" />
              Nova Organização
            </Link>
          </Button>
        }
      />

      {/* Filters */}
      <div className="bg-card rounded-xl p-4 shadow-card mb-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Buscar por nome ou slug..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="pl-9"
            />
          </div>
          <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(1); }}>
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              <SelectItem value="active">Ativas</SelectItem>
              <SelectItem value="inactive">Inativas</SelectItem>
            </SelectContent>
          </Select>
          <Select value={planFilter} onValueChange={(v) => { setPlanFilter(v); setPage(1); }}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Plano" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos os planos</SelectItem>
              {plans.map((plan) => (
                <SelectItem key={plan.id} value={String(plan.id)}>
                  {plan.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-card rounded-xl shadow-card overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : organizations.length === 0 ? (
          <div className="text-center py-16">
            <Building2 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">Nenhuma organização encontrada</p>
          </div>
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Organização</TableHead>
                  <TableHead>Owner</TableHead>
                  <TableHead>Plano</TableHead>
                  <TableHead className="text-center">Contatos</TableHead>
                  <TableHead className="text-center">Campanhas</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Criada em</TableHead>
                  <TableHead className="w-[60px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {organizations.map((org) => (
                  <TableRow key={org.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                          <Building2 className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <p className="font-medium text-foreground">{org.name}</p>
                          <p className="text-sm text-muted-foreground">{org.slug}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <p className="text-sm text-foreground">{org.owner?.name ?? '-'}</p>
                      <p className="text-xs text-muted-foreground">{org.owner?.email ?? '-'}</p>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{org.plan?.name ?? 'Sem plano'}</Badge>
                    </TableCell>
                    <TableCell className="text-center">
                      <div className="flex items-center justify-center gap-1">
                        <Users className="h-4 w-4 text-muted-foreground" />
                        <span>{org.supporters_count?.toLocaleString('pt-BR') ?? 0}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <div className="flex items-center justify-center gap-1">
                        <Megaphone className="h-4 w-4 text-muted-foreground" />
                        <span>{org.campaigns_count?.toLocaleString('pt-BR') ?? 0}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={org.is_active ? 'default' : 'secondary'}>
                        {org.is_active ? 'Ativa' : 'Inativa'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <p className="text-sm text-muted-foreground">
                        {format(new Date(org.created_at), "dd/MM/yyyy", { locale: ptBR })}
                      </p>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem asChild>
                            <Link to={`/admin/organizations/${org.id}`}>
                              <Edit className="h-4 w-4 mr-2" />
                              Editar
                            </Link>
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => setToggleDialog(org)}>
                            <Power className="h-4 w-4 mr-2" />
                            {org.is_active ? 'Desativar' : 'Ativar'}
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-6 py-4 border-t">
                <p className="text-sm text-muted-foreground">
                  Página {page} de {totalPages}
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    Anterior
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                  >
                    Próxima
                  </Button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Toggle Status Dialog */}
      <AlertDialog open={!!toggleDialog} onOpenChange={() => setToggleDialog(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {toggleDialog?.is_active ? 'Desativar' : 'Ativar'} Organização
            </AlertDialogTitle>
            <AlertDialogDescription>
              {toggleDialog?.is_active
                ? `Tem certeza que deseja desativar a organização "${toggleDialog?.name}"? Os usuários não conseguirão mais acessar o sistema.`
                : `Tem certeza que deseja ativar a organização "${toggleDialog?.name}"?`
              }
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => toggleDialog && toggleMutation.mutate(toggleDialog.id)}
              disabled={toggleMutation.isPending}
            >
              {toggleMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {toggleDialog?.is_active ? 'Desativar' : 'Ativar'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
