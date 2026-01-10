import { cn } from '@/lib/utils';

type StatusType = 
  | 'connected' 
  | 'connecting' 
  | 'disconnected' 
  | 'banned'
  | 'draft' 
  | 'scheduled' 
  | 'running' 
  | 'paused' 
  | 'completed' 
  | 'cancelled'
  | 'success'
  | 'warning'
  | 'error'
  | 'info';

interface StatusBadgeProps {
  status: StatusType;
  label?: string;
  className?: string;
}

const statusConfig: Record<StatusType, { label: string; className: string; dot: string }> = {
  connected: { 
    label: 'Conectado', 
    className: 'bg-success/10 text-success border-success/20',
    dot: 'bg-success'
  },
  connecting: { 
    label: 'Conectando', 
    className: 'bg-warning/10 text-warning border-warning/20',
    dot: 'bg-warning animate-pulse'
  },
  disconnected: { 
    label: 'Desconectado', 
    className: 'bg-destructive/10 text-destructive border-destructive/20',
    dot: 'bg-destructive'
  },
  banned: { 
    label: 'Banido', 
    className: 'bg-foreground/10 text-foreground border-foreground/20',
    dot: 'bg-foreground'
  },
  draft: { 
    label: 'Rascunho', 
    className: 'bg-muted text-muted-foreground border-border',
    dot: 'bg-muted-foreground'
  },
  scheduled: { 
    label: 'Agendada', 
    className: 'bg-primary/10 text-primary border-primary/20',
    dot: 'bg-primary'
  },
  running: { 
    label: 'Em execução', 
    className: 'bg-success/10 text-success border-success/20',
    dot: 'bg-success animate-pulse'
  },
  paused: { 
    label: 'Pausada', 
    className: 'bg-warning/10 text-warning border-warning/20',
    dot: 'bg-warning'
  },
  completed: { 
    label: 'Concluída', 
    className: 'bg-success/10 text-success border-success/20',
    dot: 'bg-success'
  },
  cancelled: { 
    label: 'Cancelada', 
    className: 'bg-destructive/10 text-destructive border-destructive/20',
    dot: 'bg-destructive'
  },
  success: { 
    label: 'Sucesso', 
    className: 'bg-success/10 text-success border-success/20',
    dot: 'bg-success'
  },
  warning: { 
    label: 'Atenção', 
    className: 'bg-warning/10 text-warning border-warning/20',
    dot: 'bg-warning'
  },
  error: { 
    label: 'Erro', 
    className: 'bg-destructive/10 text-destructive border-destructive/20',
    dot: 'bg-destructive'
  },
  info: { 
    label: 'Info', 
    className: 'bg-primary/10 text-primary border-primary/20',
    dot: 'bg-primary'
  },
};

export function StatusBadge({ status, label, className }: StatusBadgeProps) {
  const config = statusConfig[status];
  
  return (
    <span className={cn(
      'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border',
      config.className,
      className
    )}>
      <span className={cn('w-1.5 h-1.5 rounded-full', config.dot)} />
      {label || config.label}
    </span>
  );
}
