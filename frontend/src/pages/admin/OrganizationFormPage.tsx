import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { organizationsService, plansService, CreateOrganizationData, UpdateOrganizationData } from '@/services/admin';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import { Loader2, Building2, User, ArrowLeft } from 'lucide-react';

export default function OrganizationFormPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isEditing = !!id;

  // Form state
  const [orgData, setOrgData] = useState({
    name: '',
    slug: '',
    document: '',
    email: '',
    phone: '',
    plan_id: '',
    is_active: true,
  });

  const [adminData, setAdminData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
  });

  // Fetch existing organization if editing
  const { data: organization, isLoading: isLoadingOrg } = useQuery({
    queryKey: ['admin', 'organization', id],
    queryFn: () => organizationsService.get(Number(id)),
    enabled: isEditing,
  });

  // Fetch plans
  const { data: plans = [] } = useQuery({
    queryKey: ['admin', 'plans'],
    queryFn: plansService.list,
  });

  // Populate form when editing
  useEffect(() => {
    if (organization) {
      setOrgData({
        name: organization.name || '',
        slug: organization.slug || '',
        document: organization.document || '',
        email: organization.email || '',
        phone: organization.phone || '',
        plan_id: organization.plan_id ? String(organization.plan_id) : '',
        is_active: organization.is_active,
      });
    }
  }, [organization]);

  // Auto-generate slug from name
  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
  };

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: CreateOrganizationData) => organizationsService.create(data),
    onSuccess: () => {
      toast.success('Organização criada com sucesso');
      queryClient.invalidateQueries({ queryKey: ['admin', 'organizations'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'stats'] });
      navigate('/admin/organizations');
    },
    onError: (error: unknown) => {
      let message = 'Erro ao criar organização';
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: Record<string, unknown> } };
        if (axiosError.response?.data) {
          const data = axiosError.response.data;
          const errorMessages: string[] = [];
          for (const [field, errors] of Object.entries(data)) {
            if (Array.isArray(errors)) {
              errorMessages.push(`${field}: ${errors[0]}`);
            } else if (typeof errors === 'string') {
              errorMessages.push(`${field}: ${errors}`);
            }
          }
          message = errorMessages.length > 0 ? errorMessages.join('\n') : message;
        }
      }
      toast.error(message);
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: UpdateOrganizationData) => organizationsService.update(Number(id), data),
    onSuccess: () => {
      toast.success('Organização atualizada com sucesso');
      queryClient.invalidateQueries({ queryKey: ['admin', 'organizations'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'organization', id] });
      navigate('/admin/organizations');
    },
    onError: (error: unknown) => {
      let message = 'Erro ao atualizar organização';
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: Record<string, unknown> } };
        if (axiosError.response?.data) {
          const data = axiosError.response.data;
          const errorMessages: string[] = [];
          for (const [field, errors] of Object.entries(data)) {
            if (Array.isArray(errors)) {
              errorMessages.push(`${field}: ${errors[0]}`);
            } else if (typeof errors === 'string') {
              errorMessages.push(`${field}: ${errors}`);
            }
          }
          message = errorMessages.length > 0 ? errorMessages.join('\n') : message;
        }
      }
      toast.error(message);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (isEditing) {
      updateMutation.mutate({
        name: orgData.name,
        document: orgData.document || undefined,
        email: orgData.email || undefined,
        phone: orgData.phone || undefined,
        plan_id: orgData.plan_id ? Number(orgData.plan_id) : undefined,
        is_active: orgData.is_active,
      });
    } else {
      // Validate admin data for new organization
      if (!adminData.email || !adminData.password || !adminData.first_name || !adminData.last_name) {
        toast.error('Preencha todos os campos do administrador');
        return;
      }

      createMutation.mutate({
        organization: {
          name: orgData.name,
          slug: orgData.slug || generateSlug(orgData.name),
          document: orgData.document || undefined,
          email: orgData.email || undefined,
          phone: orgData.phone || undefined,
          plan_id: orgData.plan_id ? Number(orgData.plan_id) : undefined,
        },
        admin: adminData,
      });
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  if (isEditing && isLoadingOrg) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="animate-fade-in">
      <PageHeader
        title={isEditing ? 'Editar Organização' : 'Nova Organização'}
        description={isEditing ? `Editando ${organization?.name}` : 'Cadastre uma nova organização no sistema'}
        breadcrumbs={[
          { label: 'Admin', href: '/admin/dashboard' },
          { label: 'Organizações', href: '/admin/organizations' },
          { label: isEditing ? 'Editar' : 'Nova' },
        ]}
        actions={
          <Button variant="outline" onClick={() => navigate('/admin/organizations')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Voltar
          </Button>
        }
      />

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Organization Data */}
        <div className="bg-card rounded-xl p-6 shadow-card">
          <div className="flex items-center gap-3 mb-6">
            <Building2 className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold text-foreground">Dados da Organização</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nome da Organização *</Label>
              <Input
                id="name"
                value={orgData.name}
                onChange={(e) => {
                  setOrgData(prev => ({
                    ...prev,
                    name: e.target.value,
                    slug: isEditing ? prev.slug : generateSlug(e.target.value),
                  }));
                }}
                placeholder="Ex: Campanha João Silva"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="slug">Slug (identificador único)</Label>
              <Input
                id="slug"
                value={orgData.slug}
                onChange={(e) => setOrgData(prev => ({ ...prev, slug: e.target.value }))}
                placeholder="campanha-joao-silva"
                disabled={isEditing}
              />
              <p className="text-xs text-muted-foreground">
                {isEditing ? 'Não pode ser alterado após criação' : 'Gerado automaticamente do nome'}
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="document">CNPJ</Label>
              <Input
                id="document"
                value={orgData.document}
                onChange={(e) => setOrgData(prev => ({ ...prev, document: e.target.value }))}
                placeholder="00.000.000/0001-00"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="phone">Telefone</Label>
              <Input
                id="phone"
                value={orgData.phone}
                onChange={(e) => setOrgData(prev => ({ ...prev, phone: e.target.value }))}
                placeholder="(11) 9 9999-9999"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email de Contato</Label>
              <Input
                id="email"
                type="email"
                value={orgData.email}
                onChange={(e) => setOrgData(prev => ({ ...prev, email: e.target.value }))}
                placeholder="contato@empresa.com.br"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="plan">Plano</Label>
              <Select
                value={orgData.plan_id}
                onValueChange={(v) => setOrgData(prev => ({ ...prev, plan_id: v }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecione um plano" />
                </SelectTrigger>
                <SelectContent>
                  {plans.map((plan) => (
                    <SelectItem key={plan.id} value={String(plan.id)}>
                      {plan.name} - R$ {Number(plan.price).toFixed(2)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {isEditing && (
              <div className="flex items-center space-x-2 md:col-span-2">
                <Checkbox
                  id="is_active"
                  checked={orgData.is_active}
                  onCheckedChange={(checked) => setOrgData(prev => ({ ...prev, is_active: !!checked }))}
                />
                <Label htmlFor="is_active" className="cursor-pointer">
                  Organização ativa
                </Label>
              </div>
            )}
          </div>
        </div>

        {/* Admin Data - Only for new organizations */}
        {!isEditing && (
          <div className="bg-card rounded-xl p-6 shadow-card">
            <div className="flex items-center gap-3 mb-6">
              <User className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">Administrador da Organização</h2>
            </div>

            <p className="text-sm text-muted-foreground mb-4">
              Este usuário será o proprietário (owner) da organização e terá acesso total.
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="admin_first_name">Nome *</Label>
                <Input
                  id="admin_first_name"
                  value={adminData.first_name}
                  onChange={(e) => setAdminData(prev => ({ ...prev, first_name: e.target.value }))}
                  placeholder="João"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="admin_last_name">Sobrenome *</Label>
                <Input
                  id="admin_last_name"
                  value={adminData.last_name}
                  onChange={(e) => setAdminData(prev => ({ ...prev, last_name: e.target.value }))}
                  placeholder="Silva"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="admin_email">Email *</Label>
                <Input
                  id="admin_email"
                  type="email"
                  value={adminData.email}
                  onChange={(e) => setAdminData(prev => ({ ...prev, email: e.target.value }))}
                  placeholder="admin@empresa.com.br"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="admin_password">Senha *</Label>
                <Input
                  id="admin_password"
                  type="password"
                  value={adminData.password}
                  onChange={(e) => setAdminData(prev => ({ ...prev, password: e.target.value }))}
                  placeholder="Mínimo 8 caracteres"
                  required
                  minLength={8}
                />
              </div>
            </div>
          </div>
        )}

        {/* Owner info when editing */}
        {isEditing && organization?.owner && (
          <div className="bg-card rounded-xl p-6 shadow-card">
            <div className="flex items-center gap-3 mb-6">
              <User className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold text-foreground">Proprietário</h2>
            </div>

            <div className="flex items-center gap-4 p-4 rounded-lg border bg-background">
              <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                <User className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="font-medium text-foreground">{organization.owner.name}</p>
                <p className="text-sm text-muted-foreground">{organization.owner.email}</p>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/organizations')}
            disabled={isPending}
          >
            Cancelar
          </Button>
          <Button type="submit" disabled={isPending}>
            {isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
            {isEditing ? 'Salvar Alterações' : 'Criar Organização'}
          </Button>
        </div>
      </form>
    </div>
  );
}
