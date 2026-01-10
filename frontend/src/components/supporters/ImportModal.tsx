import { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Tag } from '@/types';
import { tagsService } from '@/services/supporters';
import api from '@/services/api';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { toast } from 'sonner';
import { Loader2, Upload, X, FileSpreadsheet, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface ImportModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

interface ImportJob {
  id: number;
  file_name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  total_rows: number;
  processed_rows: number;
  success_count: number;
  error_count: number;
  created_at: string;
}

// Campos disponíveis para mapeamento
const AVAILABLE_FIELDS = [
  { value: 'name', label: 'Nome', required: true },
  { value: 'phone', label: 'Telefone', required: true },
  { value: 'email', label: 'Email', required: false },
  { value: 'cpf', label: 'CPF', required: false },
  { value: 'city', label: 'Cidade', required: false },
  { value: 'state', label: 'Estado', required: false },
  { value: 'neighborhood', label: 'Bairro', required: false },
  { value: 'zip_code', label: 'CEP', required: false },
  { value: 'electoral_zone', label: 'Zona Eleitoral', required: false },
  { value: 'electoral_section', label: 'Secao Eleitoral', required: false },
  { value: 'birth_date', label: 'Data de Nascimento', required: false },
  { value: 'gender', label: 'Genero', required: false },
];

export function ImportModal({
  open,
  onOpenChange,
  onSuccess,
}: ImportModalProps) {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewHeaders, setPreviewHeaders] = useState<string[]>([]);
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({});
  const [selectedTagIds, setSelectedTagIds] = useState<number[]>([]);
  const [step, setStep] = useState<'upload' | 'mapping' | 'processing'>('upload');
  const [importJob, setImportJob] = useState<ImportJob | null>(null);

  // Fetch available tags
  const { data: tags = [] } = useQuery({
    queryKey: ['tags'],
    queryFn: tagsService.list,
    enabled: open,
  });

  // Filter out system tags for selection
  const userTags = tags.filter(tag => !tag.is_system);

  // Import mutation
  const importMutation = useMutation({
    mutationFn: async () => {
      if (!file) throw new Error('Nenhum arquivo selecionado');

      const formData = new FormData();
      formData.append('file', file);
      formData.append('column_mapping', JSON.stringify(columnMapping));
      if (selectedTagIds.length > 0) {
        selectedTagIds.forEach(id => formData.append('auto_tag_ids', id.toString()));
      }

      const response = await api.post('/supporters/import/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data as ImportJob;
    },
    onSuccess: (data) => {
      setImportJob(data);
      setStep('processing');
      toast.success('Importacao iniciada! Acompanhe o progresso abaixo.');
      // Start polling for status
      startPolling(data.id);
    },
    onError: (error: unknown) => {
      let message = 'Erro ao iniciar importacao';
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as { response?: { data?: { detail?: string } } };
        if (axiosError.response?.data?.detail) {
          message = axiosError.response.data.detail;
        }
      }
      toast.error(message);
    },
  });

  const startPolling = (jobId: number) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await api.get(`/supporters/import/${jobId}/`);
        const job = response.data as ImportJob;
        setImportJob(job);

        if (job.status === 'completed' || job.status === 'failed') {
          clearInterval(pollInterval);
          queryClient.invalidateQueries({ queryKey: ['leads'] });
          queryClient.invalidateQueries({ queryKey: ['supporters'] });
          if (job.status === 'completed') {
            toast.success(`Importacao concluida! ${job.success_count} contatos importados.`);
            onSuccess?.();
          } else {
            toast.error(`Importacao falhou. ${job.error_count} erros encontrados.`);
          }
        }
      } catch {
        clearInterval(pollInterval);
      }
    }, 2000);

    // Clean up on unmount
    return () => clearInterval(pollInterval);
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    // Validate file type
    const validTypes = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
    if (!validTypes.includes(selectedFile.type) && !selectedFile.name.match(/\.(csv|xlsx|xls)$/i)) {
      toast.error('Por favor, selecione um arquivo CSV ou Excel');
      return;
    }

    setFile(selectedFile);

    // Parse headers from CSV
    if (selectedFile.name.endsWith('.csv')) {
      const text = await selectedFile.text();
      const lines = text.split('\n');
      if (lines.length > 0) {
        const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
        setPreviewHeaders(headers);

        // Auto-map columns that match field names
        const autoMapping: Record<string, string> = {};
        headers.forEach(header => {
          const normalizedHeader = header.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
          const matchedField = AVAILABLE_FIELDS.find(field => {
            const normalizedField = field.label.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
            return normalizedHeader.includes(normalizedField) || normalizedField.includes(normalizedHeader);
          });
          if (matchedField) {
            autoMapping[header] = matchedField.value;
          }
        });
        setColumnMapping(autoMapping);
        setStep('mapping');
      }
    } else {
      // For Excel files, we'll let the backend handle the parsing
      // Just show generic mapping interface
      setPreviewHeaders([]);
      setStep('mapping');
      toast.info('Arquivo Excel selecionado. O sistema tentara mapear as colunas automaticamente.');
    }
  };

  const handleMappingChange = (header: string, value: string) => {
    setColumnMapping(prev => {
      const newMapping = { ...prev };
      if (value === 'ignore') {
        delete newMapping[header];
      } else {
        newMapping[header] = value;
      }
      return newMapping;
    });
  };

  const toggleTag = (tagId: number) => {
    setSelectedTagIds(prev =>
      prev.includes(tagId)
        ? prev.filter(id => id !== tagId)
        : [...prev, tagId]
    );
  };

  const handleStartImport = () => {
    // Validate required fields are mapped
    const mappedFields = Object.values(columnMapping);
    const requiredFields = AVAILABLE_FIELDS.filter(f => f.required).map(f => f.value);
    const missingRequired = requiredFields.filter(f => !mappedFields.includes(f));

    if (missingRequired.length > 0) {
      const missingLabels = missingRequired.map(f =>
        AVAILABLE_FIELDS.find(af => af.value === f)?.label
      ).join(', ');
      toast.error(`Campos obrigatorios nao mapeados: ${missingLabels}`);
      return;
    }

    importMutation.mutate();
  };

  const resetModal = () => {
    setFile(null);
    setPreviewHeaders([]);
    setColumnMapping({});
    setSelectedTagIds([]);
    setStep('upload');
    setImportJob(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      resetModal();
    }
    onOpenChange(newOpen);
  };

  const getProgressPercentage = () => {
    if (!importJob || importJob.total_rows === 0) return 0;
    return Math.round((importJob.processed_rows / importJob.total_rows) * 100);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Importar Contatos</DialogTitle>
          <DialogDescription>
            Importe contatos a partir de um arquivo CSV ou Excel
          </DialogDescription>
        </DialogHeader>

        {/* Step: Upload */}
        {step === 'upload' && (
          <div className="space-y-6">
            <div
              className="border-2 border-dashed border-muted-foreground/25 rounded-lg p-8 text-center hover:border-primary/50 transition-colors cursor-pointer"
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="h-10 w-10 mx-auto text-muted-foreground mb-4" />
              <p className="text-sm font-medium mb-1">
                Clique para selecionar ou arraste um arquivo
              </p>
              <p className="text-xs text-muted-foreground">
                Formatos aceitos: CSV, XLS, XLSX (max. 10MB)
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xls,.xlsx"
                onChange={handleFileChange}
                className="hidden"
              />
            </div>

            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                O arquivo deve conter pelo menos as colunas <strong>Nome</strong> e <strong>Telefone</strong>.
                Os telefones devem estar no formato brasileiro com DDD.
              </AlertDescription>
            </Alert>
          </div>
        )}

        {/* Step: Mapping */}
        {step === 'mapping' && (
          <div className="space-y-6">
            {file && (
              <div className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                <FileSpreadsheet className="h-8 w-8 text-primary" />
                <div className="flex-1">
                  <p className="font-medium text-sm">{file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {(file.size / 1024).toFixed(1)} KB
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => {
                    setFile(null);
                    setStep('upload');
                    setPreviewHeaders([]);
                    setColumnMapping({});
                  }}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            )}

            {/* Column Mapping */}
            {previewHeaders.length > 0 && (
              <section>
                <h3 className="text-sm font-semibold text-muted-foreground mb-3">
                  Mapeamento de Colunas
                </h3>
                <div className="space-y-3 max-h-64 overflow-y-auto">
                  {previewHeaders.map((header) => (
                    <div key={header} className="flex items-center gap-4">
                      <div className="w-1/2">
                        <Label className="text-sm truncate block">{header}</Label>
                      </div>
                      <div className="w-1/2">
                        <Select
                          value={columnMapping[header] || 'ignore'}
                          onValueChange={(value) => handleMappingChange(header, value)}
                        >
                          <SelectTrigger className="h-9">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="ignore">Ignorar</SelectItem>
                            {AVAILABLE_FIELDS.map((field) => (
                              <SelectItem key={field.value} value={field.value}>
                                {field.label} {field.required && '*'}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
            )}

            <Separator />

            {/* Auto Tags */}
            <section>
              <h3 className="text-sm font-semibold text-muted-foreground mb-3">
                Tags Automaticas
              </h3>
              <p className="text-xs text-muted-foreground mb-3">
                Selecione tags que serao aplicadas automaticamente a todos os contatos importados
              </p>
              {userTags.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {userTags.map((tag) => {
                    const isSelected = selectedTagIds.includes(tag.id);
                    return (
                      <Badge
                        key={tag.id}
                        variant={isSelected ? 'default' : 'outline'}
                        className="cursor-pointer transition-colors"
                        style={{
                          backgroundColor: isSelected ? tag.color : 'transparent',
                          borderColor: tag.color,
                          color: isSelected ? 'white' : tag.color,
                        }}
                        onClick={() => toggleTag(tag.id)}
                      >
                        {tag.name}
                        {isSelected && <X className="h-3 w-3 ml-1" />}
                      </Badge>
                    );
                  })}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Nenhuma tag disponivel</p>
              )}
            </section>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setFile(null);
                  setStep('upload');
                  setPreviewHeaders([]);
                  setColumnMapping({});
                }}
              >
                Voltar
              </Button>
              <Button
                onClick={handleStartImport}
                disabled={importMutation.isPending}
              >
                {importMutation.isPending && (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                )}
                Iniciar Importacao
              </Button>
            </DialogFooter>
          </div>
        )}

        {/* Step: Processing */}
        {step === 'processing' && importJob && (
          <div className="space-y-6">
            <div className="text-center py-4">
              {importJob.status === 'pending' || importJob.status === 'processing' ? (
                <>
                  <Loader2 className="h-12 w-12 mx-auto text-primary animate-spin mb-4" />
                  <p className="text-lg font-medium mb-2">
                    {importJob.status === 'pending' ? 'Preparando importacao...' : 'Importando contatos...'}
                  </p>
                </>
              ) : importJob.status === 'completed' ? (
                <>
                  <CheckCircle2 className="h-12 w-12 mx-auto text-green-500 mb-4" />
                  <p className="text-lg font-medium mb-2 text-green-600">
                    Importacao concluida!
                  </p>
                </>
              ) : (
                <>
                  <AlertCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
                  <p className="text-lg font-medium mb-2 text-destructive">
                    Importacao falhou
                  </p>
                </>
              )}
            </div>

            {/* Progress */}
            {importJob.total_rows > 0 && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Progresso</span>
                  <span className="font-medium">
                    {importJob.processed_rows} / {importJob.total_rows} ({getProgressPercentage()}%)
                  </span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all duration-300"
                    style={{ width: `${getProgressPercentage()}%` }}
                  />
                </div>
              </div>
            )}

            {/* Stats */}
            {(importJob.status === 'completed' || importJob.status === 'failed') && (
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-green-50 dark:bg-green-950/30 rounded-lg text-center">
                  <p className="text-2xl font-bold text-green-600">{importJob.success_count}</p>
                  <p className="text-sm text-green-700 dark:text-green-400">Importados</p>
                </div>
                <div className="p-4 bg-red-50 dark:bg-red-950/30 rounded-lg text-center">
                  <p className="text-2xl font-bold text-red-600">{importJob.error_count}</p>
                  <p className="text-sm text-red-700 dark:text-red-400">Erros</p>
                </div>
              </div>
            )}

            <DialogFooter>
              {(importJob.status === 'completed' || importJob.status === 'failed') && (
                <Button onClick={() => handleOpenChange(false)}>
                  Fechar
                </Button>
              )}
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
