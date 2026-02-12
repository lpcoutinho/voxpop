import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { VariableTextarea } from '@/components/ui/variable-textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent } from '@/components/ui/card';
import { toast } from 'sonner';
import { api } from '@/services/api';

const AVAILABLE_VARIABLES = [
  { name: '{{name}}', label: 'Nome Completo', description: 'Nome completo do apoiador' },
  { name: '{{first_name}}', label: 'Primeiro Nome', description: 'Apenas o primeiro nome' },
  { name: '{{city}}', label: 'Cidade', description: 'Cidade do apoiador' },
  { name: '{{neighborhood}}', label: 'Bairro', description: 'Bairro do apoiador' },
];

const formSchema = z.object({
  name: z.string().min(3, 'Nome deve ter pelo menos 3 caracteres'),
  description: z.string().optional(),
  message: z.string().min(10, 'A mensagem deve ter pelo menos 10 caracteres'),
  whatsapp_session: z.string().min(1, 'Selecione uma sessão'),
  target_tags: z.array(z.string()).default([]),
  target_groups: z.array(z.string()).default([]),
}).refine((data) => data.target_tags.length > 0 || data.target_groups.length > 0, {
  message: "Selecione pelo menos um público alvo (Tags ou Grupos)",
  path: ["target_groups"], // Show error on groups field
});

type FormValues = z.infer<typeof formSchema>;

export default function CampaignCreatePage() {
  const navigate = useNavigate();

  // Fetch Sessions
  const { data: sessions } = useQuery({
    queryKey: ['whatsapp-sessions'],
    queryFn: async () => {
      const { data } = await api.get('/whatsapp/sessions/');
      return Array.isArray(data) ? data : data.results;
    },
  });

  // Fetch Tags
  const { data: tags } = useQuery({
    queryKey: ['tags'],
    queryFn: async () => {
      const { data } = await api.get('/supporters/tags/');
      return Array.isArray(data) ? data : data.results;
    },
  });

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
      description: '',
      message: '',
      whatsapp_session: '',
      target_tags: [],
      target_groups: [],
    },
  });

  // Função para inserir variável no campo de mensagem
  const insertVariable = (variable: string) => {
    const messageField = form.getValues('message');
    const textarea = document.querySelector('textarea[name="message"]') as HTMLTextAreaElement;

    const newValue = messageField + variable;
    form.setValue('message', newValue);

    // Colocar o cursor no final
    if (textarea) {
      textarea.focus();
      const pos = newValue.length;
      textarea.setSelectionRange(pos, pos);
    }
  };

  const mutation = useMutation({
    mutationFn: async (values: FormValues) => {
      await api.post('/campaigns/', values);
    },
    onSuccess: () => {
      toast.success('Campanha criada com sucesso!');
      navigate('/campaigns');
    },
    onError: (error: any) => {
      const msg = error.response?.data?.detail || 'Erro ao criar campanha.';
      // Handle backend non_field_errors if validation fails there
      if (error.response?.data?.non_field_errors) {
          toast.error(error.response.data.non_field_errors[0]);
      } else {
          toast.error(msg);
      }
    },
  });

  function onSubmit(values: FormValues) {
    mutation.mutate(values);
  }

  const connectedSessions = sessions?.filter((s: any) => s.status === 'connected') || [];

  const groups = [
    { id: 'leads', label: 'Leads (Cadastros Iniciais)' },
    { id: 'supporters', label: 'Apoiadores Confirmados' },
    { id: 'team', label: 'Equipe Interna' },
  ];

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <PageHeader 
        title="Nova Campanha" 
        description="Configure sua mensagem e o público alvo."
        breadcrumbs={[
          { label: 'Campanhas', href: '/campaigns' },
          { label: 'Nova' },
        ]}
      />

      <Card>
        <CardContent className="pt-6">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <FormField
                  control={form.control}
                  name="name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Nome da Campanha</FormLabel>
                      <FormControl>
                        <Input placeholder="Ex: Aviso de Evento" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="whatsapp_session"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Canal de Envio (WhatsApp)</FormLabel>
                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Selecione uma sessão conectada" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {connectedSessions.length === 0 && (
                            <SelectItem value="none" disabled>Nenhuma sessão conectada</SelectItem>
                          )}
                          {connectedSessions.map((session: any) => (
                            <SelectItem key={session.id} value={session.id.toString()}>
                              {session.name} ({session.phone_number || 'Sem número'})
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormDescription>
                        Apenas sessões com status "Connected" aparecem aqui.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="message"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mensagem</FormLabel>
                    <FormControl>
                      <VariableTextarea
                        value={field.value}
                        onChange={field.onChange}
                        placeholder="Digite sua mensagem... Use {{name}}, {{city}}, etc."
                        minHeight="150px"
                      />
                    </FormControl>
                    <FormDescription>
                      As variáveis aparecerão destacadas. Clique nos botões abaixo para inserir variáveis automaticamente.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {/* Available Variables */}
              <div className="bg-card rounded-xl p-4 shadow-card">
                <p className="text-sm text-muted-foreground mb-3">
                  <strong className="text-foreground">Variáveis disponíveis:</strong> Clique em uma variável para inseri-la na mensagem
                </p>
                <div className="flex flex-wrap gap-2">
                  {AVAILABLE_VARIABLES.map((variable) => (
                    <button
                      key={variable.name}
                      type="button"
                      onClick={() => insertVariable(variable.name)}
                      className="px-3 py-2 rounded-lg bg-primary/10 text-primary text-sm font-mono font-medium hover:bg-primary/20 transition-colors border border-primary/20 text-left"
                      title={variable.description}
                    >
                      <div className="flex flex-col">
                        <span className="font-semibold">{variable.name}</span>
                        <span className="text-xs text-primary/70 font-normal">{variable.label}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-4 border rounded-lg p-4 bg-gray-50/50">
                <h3 className="text-lg font-medium">Público Alvo</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Selecione quem receberá esta mensagem. É obrigatório selecionar pelo menos um grupo ou tag.
                </p>
                
                <FormField
                  control={form.control}
                  name="target_groups"
                  render={() => (
                    <FormItem>
                      <div className="mb-4">
                        <FormLabel className="text-base">Grupos Fixos</FormLabel>
                        <FormDescription>
                          Selecione grupos de contatos pré-definidos do sistema.
                        </FormDescription>
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {groups.map((item) => (
                          <FormField
                            key={item.id}
                            control={form.control}
                            name="target_groups"
                            render={({ field }) => {
                              return (
                                <FormItem
                                  key={item.id}
                                  className="flex flex-row items-start space-x-3 space-y-0 rounded-md border p-4 bg-white shadow-sm"
                                >
                                  <FormControl>
                                    <Checkbox
                                      checked={field.value?.includes(item.id)}
                                      onCheckedChange={(checked) => {
                                        return checked
                                          ? field.onChange([...field.value, item.id])
                                          : field.onChange(
                                              field.value?.filter(
                                                (value) => value !== item.id
                                              )
                                            )
                                      }}
                                    />
                                  </FormControl>
                                  <FormLabel className="font-normal cursor-pointer">
                                    {item.label}
                                  </FormLabel>
                                </FormItem>
                              )
                            }}
                          />
                        ))}
                      </div>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="my-4 border-t border-gray-200" />
                
                <FormField
                  control={form.control}
                  name="target_tags"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Filtrar por Tags Específicas</FormLabel>
                      <Select 
                        onValueChange={(value) => {
                          if (!field.value?.includes(value)) {
                            field.onChange([...(field.value || []), value]);
                          }
                        }}
                      >
                        <FormControl>
                          <SelectTrigger className="bg-white">
                            <SelectValue placeholder="Adicionar tag..." />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {tags?.map((tag: any) => (
                            <SelectItem key={tag.id} value={tag.id.toString()}>
                              {tag.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      
                      {/* Display selected tags */}
                      <div className="flex flex-wrap gap-2 mt-2">
                        {field.value?.length === 0 && (
                          <span className="text-sm text-muted-foreground italic">Nenhuma tag selecionada.</span>
                        )}
                        {field.value?.map((tagId) => {
                          const tag = tags?.find((t: any) => t.id.toString() === tagId);
                          return tag ? (
                            <div key={tagId} className="bg-primary/10 text-primary px-2 py-1 rounded-md text-sm flex items-center gap-2 border border-primary/20">
                              {tag.name}
                              <button 
                                type="button"
                                onClick={() => field.onChange(field.value?.filter(id => id !== tagId))}
                                className="text-primary hover:text-primary/80 font-bold"
                              >
                                &times;
                              </button>
                            </div>
                          ) : null;
                        })}
                      </div>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="flex justify-end gap-4">
                <Button type="button" variant="outline" onClick={() => navigate('/campaigns')}>
                  Cancelar
                </Button>
                <Button type="submit" disabled={mutation.isPending}>
                  {mutation.isPending && (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  )}
                  Criar Campanha
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}