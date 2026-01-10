import { useMutation } from '@tanstack/react-query';
import { Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import { api } from '@/services/api';

interface ResetPasswordDialogProps {
  member: {
    id: number;
    name: string;
  } | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ResetPasswordDialog({ member, open, onOpenChange }: ResetPasswordDialogProps) {
  const mutation = useMutation({
    mutationFn: async () => {
      if (!member) return;
      await api.post(`/tenants/members/${member.id}/reset-password/`);
    },
    onSuccess: () => {
      toast.success('Senha resetada e enviada com sucesso!');
      onOpenChange(false);
    },
    onError: (error: any) => {
      const msg = error.response?.data?.detail || 'Erro ao resetar senha.';
      toast.error(msg);
    },
  });

  const handleConfirm = () => {
    mutation.mutate();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Resetar Senha</DialogTitle>
          <DialogDescription>
            Uma nova senha será gerada e enviada para o WhatsApp cadastrado de <strong>{member?.name}</strong>.
          </DialogDescription>
        </DialogHeader>
        
        <DialogFooter className="mt-4">
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button variant="destructive" onClick={handleConfirm} disabled={mutation.isPending}>
            {mutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            Confirmar Reset
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}