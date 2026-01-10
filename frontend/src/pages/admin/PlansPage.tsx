import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { plansService, CreatePlanData, UpdatePlanData } from '@/services/admin';
import { Plan } from '@/types';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
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
  CreditCard,
  Plus,
  Edit,
  Trash2,
  Loader2,
  Users,
  MessageSquare,
  Megaphone,
  Smartphone,
  Building2,
} from 'lucide-react';

interface PlanFormData {
  name: string;
  description: string;
  max_supporters: string;
  max_messages_month: string;
  max_campaigns: string;
  max_whatsapp_sessions: string;
  price: string;
  is_active: boolean;
  is_public: boolean;
}

const initialFormData: PlanFormData = {
  name: '',
  description: '',
  max_supporters: '1000',
  max_messages_month: '5000',
  max_campaigns: '5',
  max_whatsapp_sessions: '1',
  price: '99.00',
  is_active: true,
  is_public: true,
};

export default function PlansPage() {
  const queryClient = useQueryClient();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<Plan | null>(null);
  const [deletePlan, setDeletePlan] = useState<Plan | null>(null);
  const [formData, setFormData] = useState<PlanFormData>(initialFormData);

  // Fetch plans
  const { data: plans = [], isLoading } = useQuery({
    queryKey: ['admin', 'plans'],
    queryFn: plansService.list,
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: CreatePlanData) => plansService.create(data),
    onSuccess: () => {
      toast.success('Plano criado com sucesso');
      queryClient.invalidateQueries({ queryKey: ['admin', 'plans'] });
      handleCloseDialog();
    },
    onError: () => {
      toast.error('Erro ao criar plano');
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdatePlanData }) =>
      plansService.update(id, data),
    onSuccess: () => {
      toast.success('Plano atualizado com sucesso');
      queryClient.invalidateQueries({ queryKey: ['admin', 'plans'] });
      handleCloseDialog();
    },
    onError: () => {
      toast.error('Erro ao atualizar plano');
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => plansService.delete(id),
    onSuccess: () => {
      toast.success('Plano excluído com sucesso');
      queryClient.invalidateQueries({ queryKey: ['admin', 'plans'] });
      setDeletePlan(null);
    },
    onError: () => {
      toast.error('Erro ao excluir plano. Verifique se não há organizações usando este plano.');
    },
  });

  const handleOpenCreate = () => {
    setEditingPlan(null);
    setFormData(initialFormData);
    setIsDialogOpen(true);
  };

  const handleOpenEdit = (plan: Plan) => {
    setEditingPlan(plan);
    setFormData({
      name: plan.name,
      description: plan.description || '',
      max_supporters: String(plan.max_supporters),
      max_messages_month: String(plan.max_messages_month),
      max_campaigns: String(plan.max_campaigns),
      max_whatsapp_sessions: String(plan.max_whatsapp_sessions),
      price: String(plan.price),
      is_active: plan.is_active,
      is_public: plan.is_public,
    });
    setIsDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setIsDialogOpen(false);
    setEditingPlan(null);
    setFormData(initialFormData);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const data = {
      name: formData.name,
      description: formData.description || undefined,
      max_supporters: Number(formData.max_supporters),
      max_messages_month: Number(formData.max_messages_month),
      max_campaigns: Number(formData.max_campaigns),
      max_whatsapp_sessions: Number(formData.max_whatsapp_sessions),
      price: Number(formData.price),
      is_active: formData.is_active,
      is_public: formData.is_public,
    };

    if (editingPlan) {
      updateMutation.mutate({ id: editingPlan.id, data });
    } else {
      createMutation.mutate(data);
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Planos"
        description="Gerencie os planos de assinatura disponíveis"
        actions={
          <Button onClick={handleOpenCreate}>
            <Plus className="h-4 w-4 mr-2" />
            Novo Plano
          </Button>
        }
      />

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : plans.length === 0 ? (
        <div className="bg-card rounded-xl p-16 shadow-card text-center">
          <CreditCard className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground mb-4">Nenhum plano cadastrado</p>
          <Button onClick={handleOpenCreate}>
            <Plus className="h-4 w-4 mr-2" />
            Criar primeiro plano
          </Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className="bg-card rounded-xl p-6 shadow-card flex flex-col"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="text-lg font-semibold text-foreground">{plan.name}</h3>
                    {!plan.is_active && (
                      <Badge variant="secondary">Inativo</Badge>
                    )}
                    {!plan.is_public && (
                      <Badge variant="outline">Privado</Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">{plan.description || 'Sem descrição'}</p>
                </div>
                <div className="flex gap-1">
                  <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleOpenEdit(plan)}>
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-destructive hover:text-destructive"
                    onClick={() => setDeletePlan(plan)}
                    disabled={(plan.tenants_count ?? 0) > 0}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {/* Price */}
              <div className="mb-6">
                <span className="text-3xl font-bold text-foreground">
                  R$ {Number(plan.price).toFixed(2)}
                </span>
                <span className="text-muted-foreground">/mês</span>
              </div>

              {/* Limits */}
              <div className="space-y-3 flex-1">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
                    <Users className="h-4 w-4 text-blue-500" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {plan.max_supporters.toLocaleString('pt-BR')} contatos
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-green-500/10 flex items-center justify-center">
                    <MessageSquare className="h-4 w-4 text-green-500" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {plan.max_messages_month.toLocaleString('pt-BR')} mensagens/mês
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-orange-500/10 flex items-center justify-center">
                    <Megaphone className="h-4 w-4 text-orange-500" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {plan.max_campaigns} campanhas
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center">
                    <Smartphone className="h-4 w-4 text-purple-500" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {plan.max_whatsapp_sessions} sessões WhatsApp
                    </p>
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="mt-6 pt-4 border-t flex items-center justify-between">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Building2 className="h-4 w-4" />
                  <span className="text-sm">
                    {plan.tenants_count ?? 0} organizações
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {editingPlan ? 'Editar Plano' : 'Novo Plano'}
            </DialogTitle>
          </DialogHeader>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nome do Plano *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Ex: Starter, Pro, Enterprise"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Descrição</Label>
              <Input
                id="description"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Descrição do plano"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="price">Preço (R$) *</Label>
              <Input
                id="price"
                type="number"
                step="0.01"
                min="0"
                value={formData.price}
                onChange={(e) => setFormData(prev => ({ ...prev, price: e.target.value }))}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="max_supporters">Máx. Contatos *</Label>
                <Input
                  id="max_supporters"
                  type="number"
                  min="1"
                  value={formData.max_supporters}
                  onChange={(e) => setFormData(prev => ({ ...prev, max_supporters: e.target.value }))}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="max_messages_month">Máx. Mensagens/Mês *</Label>
                <Input
                  id="max_messages_month"
                  type="number"
                  min="1"
                  value={formData.max_messages_month}
                  onChange={(e) => setFormData(prev => ({ ...prev, max_messages_month: e.target.value }))}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="max_campaigns">Máx. Campanhas *</Label>
                <Input
                  id="max_campaigns"
                  type="number"
                  min="1"
                  value={formData.max_campaigns}
                  onChange={(e) => setFormData(prev => ({ ...prev, max_campaigns: e.target.value }))}
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="max_whatsapp_sessions">Máx. Sessões WhatsApp *</Label>
                <Input
                  id="max_whatsapp_sessions"
                  type="number"
                  min="1"
                  value={formData.max_whatsapp_sessions}
                  onChange={(e) => setFormData(prev => ({ ...prev, max_whatsapp_sessions: e.target.value }))}
                  required
                />
              </div>
            </div>

            <div className="flex items-center gap-6">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_active"
                  checked={formData.is_active}
                  onCheckedChange={(checked) => setFormData(prev => ({ ...prev, is_active: !!checked }))}
                />
                <Label htmlFor="is_active" className="cursor-pointer">Ativo</Label>
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="is_public"
                  checked={formData.is_public}
                  onCheckedChange={(checked) => setFormData(prev => ({ ...prev, is_public: !!checked }))}
                />
                <Label htmlFor="is_public" className="cursor-pointer">Público</Label>
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleCloseDialog} disabled={isPending}>
                Cancelar
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                {editingPlan ? 'Salvar' : 'Criar'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Dialog */}
      <AlertDialog open={!!deletePlan} onOpenChange={() => setDeletePlan(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir Plano</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja excluir o plano "{deletePlan?.name}"?
              Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deletePlan && deleteMutation.mutate(deletePlan.id)}
              disabled={deleteMutation.isPending}
              className="bg-destructive hover:bg-destructive/90"
            >
              {deleteMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
