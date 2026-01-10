import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import { BarChart, CheckCircle, XCircle, Clock } from 'lucide-react';

import { PageHeader } from '@/components/layout/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { api } from '@/services/api';

export default function CampaignDetailsPage() {
  const { id } = useParams();

  const { data: campaign, isLoading } = useQuery({
    queryKey: ['campaign', id],
    queryFn: async () => {
      const { data } = await api.get(`/campaigns/${id}/`);
      return data;
    },
    refetchInterval: 3000, // Live updates
  });

  if (isLoading) return <div>Carregando...</div>;
  if (!campaign) return <div>Campanha não encontrada.</div>;

  const progress = campaign.total_recipients > 0 
    ? (campaign.messages_sent / campaign.total_recipients) * 100 
    : 0;

  return (
    <div className="space-y-6">
      <PageHeader 
        title={campaign.name}
        description={`Criada por ${campaign.created_by_name} em ${format(new Date(campaign.created_at), "d 'de' MMMM, yyyy", { locale: ptBR })}`}
        breadcrumbs={[
          { label: 'Campanhas', href: '/campaigns' },
          { label: campaign.name },
        ]}
        actions={
          <Badge className="text-lg px-4 py-1">
            {campaign.status_display}
          </Badge>
        }
      />

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Progresso</CardTitle>
            <BarChart className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{Math.round(progress)}%</div>
            <Progress value={progress} className="h-2 mt-2" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Enviadas</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{campaign.messages_sent}</div>
            <p className="text-xs text-muted-foreground">de {campaign.total_recipients} total</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Falhas</CardTitle>
            <XCircle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{campaign.messages_failed}</div>
            <p className="text-xs text-muted-foreground">Erros de envio</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pendentes</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {campaign.total_recipients - campaign.messages_sent - campaign.messages_failed}
            </div>
            <p className="text-xs text-muted-foreground">Na fila</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Message Preview */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Mensagem</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-gray-100 p-4 rounded-lg whitespace-pre-wrap text-sm border-l-4 border-green-500">
              {campaign.message}
            </div>
            <div className="mt-4 text-sm text-muted-foreground">
              <strong>Sessão:</strong> {campaign.whatsapp_session_name}
            </div>
          </CardContent>
        </Card>

        {/* Recipients List */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Destinatários ({campaign.items.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="max-h-[400px] overflow-y-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Nome</TableHead>
                    <TableHead>Telefone</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Horário</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {campaign.items.map((item: any) => (
                    <TableRow key={item.id}>
                      <TableCell>{item.recipient_name}</TableCell>
                      <TableCell>{item.recipient_phone}</TableCell>
                      <TableCell>
                        <Badge variant={
                          item.status === 'sent' ? 'default' :
                          item.status === 'failed' ? 'destructive' :
                          'outline'
                        }>
                          {item.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {item.sent_at 
                          ? format(new Date(item.sent_at), "HH:mm:ss")
                          : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
