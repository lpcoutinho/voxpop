import * as React from "react";
import { cn } from "@/lib/utils";

// Utility functions for masking
const masks = {
  phone: (value: string): string => {
    // Remove all non-digits
    const digits = value.replace(/\D/g, '');

    // Limit to 11 digits (DDD + 9 digits)
    const limited = digits.slice(0, 11);

    // Apply mask: (XX) X XXXX-XXXX or (XX) XXXX-XXXX
    if (limited.length === 0) return '';
    if (limited.length <= 2) return `(${limited}`;
    if (limited.length <= 3) return `(${limited.slice(0, 2)}) ${limited.slice(2)}`;
    if (limited.length <= 7) return `(${limited.slice(0, 2)}) ${limited.slice(2, 3)} ${limited.slice(3)}`;
    if (limited.length <= 11) return `(${limited.slice(0, 2)}) ${limited.slice(2, 3)} ${limited.slice(3, 7)}-${limited.slice(7)}`;
    return `(${limited.slice(0, 2)}) ${limited.slice(2, 3)} ${limited.slice(3, 7)}-${limited.slice(7, 11)}`;
  },

  cpf: (value: string): string => {
    // Remove all non-digits
    const digits = value.replace(/\D/g, '');

    // Limit to 11 digits
    const limited = digits.slice(0, 11);

    // Apply mask: XXX.XXX.XXX-XX
    if (limited.length === 0) return '';
    if (limited.length <= 3) return limited;
    if (limited.length <= 6) return `${limited.slice(0, 3)}.${limited.slice(3)}`;
    if (limited.length <= 9) return `${limited.slice(0, 3)}.${limited.slice(3, 6)}.${limited.slice(6)}`;
    return `${limited.slice(0, 3)}.${limited.slice(3, 6)}.${limited.slice(6, 9)}-${limited.slice(9)}`;
  },

  cep: (value: string): string => {
    // Remove all non-digits
    const digits = value.replace(/\D/g, '');

    // Limit to 8 digits
    const limited = digits.slice(0, 8);

    // Apply mask: XXXXX-XXX
    if (limited.length === 0) return '';
    if (limited.length <= 5) return limited;
    return `${limited.slice(0, 5)}-${limited.slice(5)}`;
  },
};

// Extract raw value (digits only) for each mask type
const getRawValue = {
  phone: (value: string): string => {
    const digits = value.replace(/\D/g, '');
    // Only add country code when we have a complete phone number (11 digits)
    // Otherwise return just the digits (user is still typing)
    if (digits.length === 0) {
      return '';
    }
    if (digits.length === 11) {
      // Complete number: add country code
      return `55${digits}`;
    }
    // Incomplete number: return just digits without country code
    return digits;
  },

  cpf: (value: string): string => {
    return value.replace(/\D/g, '');
  },

  cep: (value: string): string => {
    return value.replace(/\D/g, '');
  },
};

// Convert stored value (e.g., 5511999999999) to display format
const toDisplayValue = {
  phone: (value: string): string => {
    if (!value) return '';
    let digits = value.replace(/\D/g, '');
    // If value has country code (13 digits starting with 55), remove it for display
    if (digits.startsWith('55') && digits.length >= 12) {
      digits = digits.slice(2);
    }
    return masks.phone(digits);
  },

  cpf: (value: string): string => {
    return masks.cpf(value);
  },

  cep: (value: string): string => {
    return masks.cep(value);
  },
};

export type MaskType = 'phone' | 'cpf' | 'cep';

interface MaskedInputProps extends Omit<React.ComponentProps<"input">, 'onChange'> {
  mask: MaskType;
  value: string;
  onValueChange: (rawValue: string) => void;
}

const MaskedInput = React.forwardRef<HTMLInputElement, MaskedInputProps>(
  ({ className, mask, value, onValueChange, ...props }, ref) => {
    // Convert the stored value to display format
    const displayValue = toDisplayValue[mask](value || '');

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const inputValue = e.target.value;
      const maskedValue = masks[mask](inputValue);
      const rawValue = getRawValue[mask](maskedValue);
      onValueChange(rawValue);
    };

    return (
      <input
        type="text"
        inputMode="numeric"
        className={cn(
          "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-base ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
          className,
        )}
        ref={ref}
        value={displayValue}
        onChange={handleChange}
        {...props}
      />
    );
  },
);
MaskedInput.displayName = "MaskedInput";

export { MaskedInput };
