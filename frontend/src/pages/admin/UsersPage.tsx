import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { usersService, organizationsService } from '@/services/admin';
import { AdminUser } from '@/types';
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
  Users,
  Search,
  MoreHorizontal,
  Key,
  Loader2,
  Building2,
  Mail,
  CheckCircle,
  XCircle,
  Shield,
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';

export default function UsersPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [page, setPage] = useState(1);
  const [resetPasswordUser, setResetPasswordUser] = useState<AdminUser | null>(null);

  // Fetch users
  const { data, isLoading } = useQuery({
    queryKey: ['admin', 'users', { search, status: statusFilter, page }],
    queryFn: () => usersService.list({
      search: search || undefined,
      is_active: statusFilter === 'all' ? undefined : statusFilter === 'active',
      page,
      page_size: 20,
    }),
  });

  // Reset password mutation
  const resetPasswordMutation = useMutation({
    mutationFn: (id: number) => usersService.resetPassword(id),
    onSuccess: (data) => {
      if (data.temporary_password) {
        toast.success(`Senha temporária: ${data.temporary_password}`, {
          duration: 10000,
          description: 'Anote esta senha, ela não será exibida novamente.',
        });
      } else {
        toast.success('Email de recuperação enviado com sucesso');
      }
      setResetPasswordUser(null);
    },
    onError: () => {
      toast.error('Erro ao resetar senha');
    },
  });

  const users = data?.results ?? [];
  const totalCount = data?.count ?? 0;
  const totalPages = Math.ceil(totalCount / 20);

  const getRoleBadge = (role: string) => {
    const roleConfig: Record<string, { label: string; color: string }> = {
      owner: { label: 'Proprietário', color: 'bg-yellow-500' },
      admin: { label: 'Admin', color: 'bg-purple-500' },
      operator: { label: 'Operador', color: 'bg-blue-500' },
      viewer: { label: 'Visualizador', color: 'bg-gray-500' },
    };
    const config = roleConfig[role] || { label: role, color: 'bg-gray-500' };
    return (
      <Badge className={`${config.color} text-white text-xs`}>
        {config.label}
      </Badge>
    );
  };

  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Usuários"
        description={`${totalCount} usuários cadastrados`}
      />

      {/* Filters */}
      <div className="bg-card rounded-xl p-4 shadow-card mb-6">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Buscar por nome ou email..."
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
              <SelectItem value="active">Ativos</SelectItem>
              <SelectItem value="inactive">Inativos</SelectItem>
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
        ) : users.length === 0 ? (
          <div className="text-center py-16">
            <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">Nenhum usuário encontrado</p>
          </div>
        ) : (
          <>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Usuário</TableHead>
                  <TableHead>Organizações</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Último Acesso</TableHead>
                  <TableHead>Cadastro</TableHead>
                  <TableHead className="w-[60px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                          {user.is_superuser ? (
                            <Shield className="h-5 w-5 text-primary" />
                          ) : (
                            <span className="text-primary font-medium">
                              {user.name?.charAt(0).toUpperCase() || user.email.charAt(0).toUpperCase()}
                            </span>
                          )}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <p className="font-medium text-foreground">{user.name || 'Sem nome'}</p>
                            {user.is_superuser && (
                              <Badge variant="outline" className="text-xs">Super Admin</Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-1 text-sm text-muted-foreground">
                            <Mail className="h-3 w-3" />
                            {user.email}
                          </div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      {user.organizations && user.organizations.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {user.organizations.slice(0, 2).map((org) => (
                            <div key={org.id} className="flex items-center gap-1">
                              <Badge variant="outline" className="text-xs">
                                <Building2 className="h-3 w-3 mr-1" />
                                {org.name}
                              </Badge>
                              {getRoleBadge(org.role)}
                            </div>
                          ))}
                          {user.organizations.length > 2 && (
                            <Badge variant="secondary" className="text-xs">
                              +{user.organizations.length - 2}
                            </Badge>
                          )}
                        </div>
                      ) : (
                        <span className="text-sm text-muted-foreground">-</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {user.is_active ? (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        ) : (
                          <XCircle className="h-4 w-4 text-red-500" />
                        )}
                        <span className={user.is_active ? 'text-green-600' : 'text-red-600'}>
                          {user.is_active ? 'Ativo' : 'Inativo'}
                        </span>
                        {user.is_verified && (
                          <Badge variant="outline" className="text-xs text-green-600 border-green-600">
                            Verificado
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {user.last_login ? (
                        <p className="text-sm text-muted-foreground">
                          {formatDistanceToNow(new Date(user.last_login), {
                            addSuffix: true,
                            locale: ptBR,
                          })}
                        </p>
                      ) : (
                        <span className="text-sm text-muted-foreground">Nunca</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {user.date_joined && (
                        <p className="text-sm text-muted-foreground">
                          {format(new Date(user.date_joined), "dd/MM/yyyy", { locale: ptBR })}
                        </p>
                      )}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => setResetPasswordUser(user)}>
                            <Key className="h-4 w-4 mr-2" />
                            Resetar Senha
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

      {/* Reset Password Dialog */}
      <AlertDialog open={!!resetPasswordUser} onOpenChange={() => setResetPasswordUser(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Resetar Senha</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja resetar a senha do usuário "{resetPasswordUser?.name || resetPasswordUser?.email}"?
              Uma senha temporária será gerada ou um email de recuperação será enviado.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => resetPasswordUser && resetPasswordMutation.mutate(resetPasswordUser.id)}
              disabled={resetPasswordMutation.isPending}
            >
              {resetPasswordMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Resetar Senha
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
