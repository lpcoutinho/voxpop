import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { MoreHorizontal, Pencil, Trash, KeyRound } from 'lucide-react';
import { PageHeader } from '@/components/layout/PageHeader';
import { AddMemberDialog } from './components/AddMemberDialog';
import { EditMemberDialog } from './components/EditMemberDialog';
import { ResetPasswordDialog } from './components/ResetPasswordDialog';
import { api } from '@/services/api';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
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
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { toast } from 'sonner';

interface Member {
  id: number;
  name: string;
  first_name: string;
  last_name: string;
  email: string;
  whatsapp: string;
  role: string;
  role_display: string;
  is_active: boolean;
  created_at: string;
}

interface PaginatedResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Member[];
}

export default function TeamMembersPage() {
  const queryClient = useQueryClient();
  const [editingMember, setEditingMember] = useState<Member | null>(null);
  const [resettingMember, setResettingMember] = useState<Member | null>(null);
  const [deletingMember, setDeletingMember] = useState<Member | null>(null);

  const { data, isLoading, error } = useQuery<PaginatedResponse | Member[]>({
    queryKey: ['team-members'],
    queryFn: async () => {
      const { data } = await api.get('/tenants/members/');
      return data;
    },
  });

  const members = Array.isArray(data) ? data : data?.results;

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`/tenants/members/${id}/`);
    },
    onSuccess: () => {
      toast.success('Membro removido com sucesso!');
      queryClient.invalidateQueries({ queryKey: ['team-members'] });
      setDeletingMember(null);
    },
    onError: () => {
      toast.error('Erro ao remover membro.');
    },
  });

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .substring(0, 2);
  };

  const getRoleBadgeVariant = (role: string) => {
    switch (role) {
      case 'owner':
      case 'admin':
        return 'default'; // primary color
      case 'operator':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  if (isLoading) return <div>Carregando...</div>;
  if (error) return <div>Erro ao carregar membros.</div>;

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Membros da Equipe" 
        description="Gerencie os membros e seus acessos"
        actions={<AddMemberDialog />}
      />
      
      <div className="bg-card rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Membro</TableHead>
              <TableHead>Função</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Adicionado em</TableHead>
              <TableHead className="w-[50px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {members?.map((member) => (
              <TableRow key={member.id}>
                <TableCell className="flex items-center gap-3">
                  <Avatar>
                    <AvatarFallback>{getInitials(member.name)}</AvatarFallback>
                  </Avatar>
                  <div>
                    <div className="font-medium">{member.name}</div>
                    <div className="text-sm text-muted-foreground">{member.email}</div>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant={getRoleBadgeVariant(member.role)}>
                    {member.role_display}
                  </Badge>
                </TableCell>
                <TableCell>
                  {member.is_active ? (
                    <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                      Ativo
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="bg-red-50 text-red-700 border-red-200">
                      Inativo
                    </Badge>
                  )}
                </TableCell>
                <TableCell>
                  {format(new Date(member.created_at), "d 'de' MMMM, yyyy", { locale: ptBR })}
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" className="h-8 w-8 p-0">
                        <span className="sr-only">Abrir menu</span>
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuLabel>Ações</DropdownMenuLabel>
                      <DropdownMenuItem onClick={() => setEditingMember(member)}>
                        <Pencil className="mr-2 h-4 w-4" /> Editar
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => setResettingMember(member)}>
                        <KeyRound className="mr-2 h-4 w-4" /> Resetar Senha
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem 
                        className="text-red-600 focus:text-red-600"
                        onClick={() => setDeletingMember(member)}
                      >
                        <Trash className="mr-2 h-4 w-4" /> Remover
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
            {members?.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                  Nenhum membro encontrado.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <EditMemberDialog 
        open={!!editingMember} 
        onOpenChange={(open) => !open && setEditingMember(null)}
        member={editingMember}
      />

      <ResetPasswordDialog 
        open={!!resettingMember} 
        onOpenChange={(open) => !open && setResettingMember(null)}
        member={resettingMember}
      />

      <AlertDialog open={!!deletingMember} onOpenChange={(open) => !open && setDeletingMember(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Tem certeza?</AlertDialogTitle>
            <AlertDialogDescription>
              Isso removerá o acesso de <strong>{deletingMember?.name}</strong> a esta organização.
              Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction 
              onClick={() => deletingMember && deleteMutation.mutate(deletingMember.id)}
              className="bg-red-600 hover:bg-red-700"
            >
              Remover
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
