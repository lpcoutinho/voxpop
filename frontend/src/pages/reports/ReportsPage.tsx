import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/button';
import { Construction } from 'lucide-react';

export default function ReportsPage() {
  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Relatórios"
        description="Analise o desempenho das suas campanhas"
        breadcrumbs={[
          { label: 'Dashboard', href: '/dashboard' },
          { label: 'Relatórios' },
        ]}
      />

      <div className="flex flex-col items-center justify-center py-20">
        <div className="w-20 h-20 rounded-full bg-muted flex items-center justify-center mb-6">
          <Construction className="h-10 w-10 text-muted-foreground" />
        </div>
        <h2 className="text-xl font-semibold text-foreground mb-2">Em desenvolvimento</h2>
        <p className="text-muted-foreground text-center max-w-md mb-6">
          A seção de relatórios está sendo desenvolvida. Em breve você poderá visualizar métricas detalhadas das suas campanhas.
        </p>
        <Button variant="outline" onClick={() => window.history.back()}>
          Voltar
        </Button>
      </div>
    </div>
  );
}
