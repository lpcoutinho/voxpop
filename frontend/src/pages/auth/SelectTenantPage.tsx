import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Building2, ChevronRight } from 'lucide-react';

export default function SelectTenantPage() {
  const navigate = useNavigate();
  const { tenants, selectTenant } = useAuth();

  const handleSelectTenant = (tenant: typeof tenants[0]) => {
    selectTenant(tenant);
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-8 bg-background">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-xl bg-gradient-primary flex items-center justify-center mx-auto mb-4">
            <span className="text-primary-foreground font-bold text-xl">VP</span>
          </div>
          <h2 className="text-2xl font-semibold text-foreground">Selecione a organização</h2>
          <p className="text-muted-foreground mt-2">
            Você tem acesso a múltiplas organizações
          </p>
        </div>

        <div className="space-y-3">
          {tenants.map((tenant) => (
            <Button
              key={tenant.id}
              variant="outline"
              className="w-full h-auto p-4 justify-between hover:bg-secondary"
              onClick={() => handleSelectTenant(tenant)}
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Building2 className="h-5 w-5 text-primary" />
                </div>
                <div className="text-left">
                  <p className="font-medium text-foreground">{tenant.name}</p>
                  <p className="text-sm text-muted-foreground">{tenant.slug}</p>
                </div>
              </div>
              <ChevronRight className="h-5 w-5 text-muted-foreground" />
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
}
