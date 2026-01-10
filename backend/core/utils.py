"""
Utility functions for VoxPop.
"""
import re
from typing import Any


def clean_phone_number(phone: str) -> str:
    """
    Normalize phone number to international format.

    Args:
        phone: Phone number in any format

    Returns:
        Phone number with only digits, starting with country code (55)
        Returns empty string if invalid

    Example:
        clean_phone_number("(11) 99999-9999") -> "5511999999999"
        clean_phone_number("+5511999999999") -> "5511999999999"
    """
    if not phone:
        return ''

    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)

    # Add Brazil country code if not present
    if len(digits) == 11:  # DDD + 9 digits
        digits = '55' + digits
    elif len(digits) == 10:  # DDD + 8 digits (old format)
        digits = '55' + digits
    elif len(digits) == 13 and digits.startswith('55'):
        # Already has country code (55 + DDD + 9 digits)
        pass
    elif len(digits) == 12 and digits.startswith('55'):
        # Already has country code (55 + DDD + 8 digits - old format)
        pass
    elif len(digits) < 10 or len(digits) > 13:
        # Invalid length
        return ''

    return digits


def format_phone_display(phone: str) -> str:
    """
    Format phone number for display.

    Args:
        phone: Phone number with only digits

    Returns:
        Formatted phone number

    Example:
        format_phone_display("5511999999999") -> "+55 (11) 99999-9999"
    """
    digits = re.sub(r'\D', '', phone)

    if len(digits) == 13:  # +55 11 99999-9999
        return f"+{digits[:2]} ({digits[2:4]}) {digits[4:9]}-{digits[9:]}"
    elif len(digits) == 11:  # 11 99999-9999
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"

    return phone


def clean_document(document: str) -> str:
    """
    Clean document (CPF/CNPJ) removing special characters.

    Args:
        document: Document with or without formatting

    Returns:
        Document with only digits
    """
    return re.sub(r'\D', '', document)


def format_cpf(cpf: str) -> str:
    """Format CPF for display."""
    digits = clean_document(cpf)
    if len(digits) == 11:
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
    return cpf


def format_cnpj(cnpj: str) -> str:
    """Format CNPJ for display."""
    digits = clean_document(cnpj)
    if len(digits) == 14:
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
    return cnpj


def validate_cpf(cpf: str) -> bool:
    """Validate CPF using checksum."""
    cpf = clean_document(cpf)

    if len(cpf) != 11:
        return False

    # Check for known invalid CPFs
    if cpf == cpf[0] * 11:
        return False

    # Calculate first check digit
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    if resto == 10:
        resto = 0
    if resto != int(cpf[9]):
        return False

    # Calculate second check digit
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    if resto == 10:
        resto = 0
    if resto != int(cpf[10]):
        return False

    return True


def validate_cnpj(cnpj: str) -> bool:
    """Validate CNPJ using checksum."""
    cnpj = clean_document(cnpj)

    if len(cnpj) != 14:
        return False

    # Check for known invalid CNPJs
    if cnpj == cnpj[0] * 14:
        return False

    # First check digit
    weights = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * weights[i] for i in range(12))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    if int(cnpj[12]) != digito1:
        return False

    # Second check digit
    weights = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * weights[i] for i in range(13))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    if int(cnpj[13]) != digito2:
        return False

    return True


def render_template_variables(template: str, context: dict[str, Any]) -> str:
    """
    Render template with variables using {{variable}} syntax.

    Args:
        template: Template string with {{variable}} placeholders
        context: Dictionary with variable values

    Returns:
        Rendered string

    Example:
        render_template_variables("Ola {{name}}!", {"name": "Joao"})
        -> "Ola Joao!"
    """
    result = template
    for key, value in context.items():
        placeholder = f"{{{{{key}}}}}"
        result = result.replace(placeholder, str(value))
    return result
