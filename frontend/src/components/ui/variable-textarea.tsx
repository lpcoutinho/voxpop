import { useState, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';

interface VariableTextareaProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  minHeight?: string;
  name?: string;
  onBlur?: () => void;
}

// Padrão regex para encontrar {{variavel}}
const VARIABLE_PATTERN = /\{\{[\w\s]+\}\}/g;

// Estilos compartilhados para garantir alinhamento perfeito
const sharedStyles = {
  boxSizing: 'border-box',
  fontFamily: 'inherit',
  fontSize: '0.875rem', // text-sm
  lineHeight: '1.625', // leading-relaxed
  letterSpacing: '0.01em',
  wordSpacing: 'normal',
  padding: '0.75rem', // p-3
  margin: '0',
  border: '1px solid hsl(var(--input))',
  borderRadius: '0.375rem', // rounded-md
};

export function VariableTextarea({
  value,
  onChange,
  placeholder = '',
  className,
  minHeight = '150px',
  name,
  onBlur,
}: VariableTextareaProps) {
  const [textareaHeight, setTextareaHeight] = useState(minHeight);
  const highlightRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Sincronizar scroll
  const handleScroll = () => {
    if (highlightRef.current && textareaRef.current) {
      highlightRef.current.scrollTop = textareaRef.current.scrollTop;
      highlightRef.current.scrollLeft = textareaRef.current.scrollLeft;
    }
  };

  // Ajustar altura automaticamente
  const adjustHeight = () => {
    if (textareaRef.current) {
      const newHeight = Math.max(
        parseInt(minHeight),
        textareaRef.current.scrollHeight
      );
      setTextareaHeight(`${newHeight}px`);
    }
  };

  useEffect(() => {
    adjustHeight();
  }, [value]);

  // Função para destacar as variáveis
  const highlightText = (text: string) => {
    // Escapar HTML para evitar XSS
    let escaped = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Substituir variáveis por spans destacados - estilo inline para garantir consistência
    // SEM font-mono para evitar problemas de largura de caracteres
    escaped = escaped.replace(VARIABLE_PATTERN, (match) => {
      return `<span style="background-color: hsl(var(--primary) / 0.2); color: hsl(var(--primary)); font-weight: 500;">${match}</span>`;
    });

    return escaped;
  };

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
    adjustHeight();
  };

  return (
    <div className="relative w-full">
      {/* Container com highlight (fundo) */}
      <div
        ref={highlightRef}
        className="absolute inset-0 overflow-auto whitespace-pre-wrap break-words pointer-events-none"
        style={{
          ...sharedStyles,
          backgroundColor: 'hsl(var(--background) / 0.5)',
          minHeight: textareaHeight,
          maxHeight: '400px',
        }}
        dangerouslySetInnerHTML={{
          __html: highlightText(value) || `<span class="text-muted-foreground">${placeholder}</span>`,
        }}
      />

      {/* Textarea transparente (frente) */}
      <textarea
        ref={textareaRef}
        name={name}
        value={value}
        onChange={handleChange}
        onScroll={handleScroll}
        onBlur={onBlur}
        className={cn(
          'relative w-full resize-none bg-transparent',
          'text-transparent caret-foreground',
          'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
          'placeholder:text-transparent',
          className
        )}
        style={{
          ...sharedStyles,
          minHeight: textareaHeight,
          maxHeight: '400px',
        }}
        placeholder={placeholder}
      />
    </div>
  );
}
