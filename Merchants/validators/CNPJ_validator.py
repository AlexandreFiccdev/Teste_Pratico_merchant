import re

from django.core.exceptions import ValidationError

CNPJ_FIRST_WEIGHTS = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
CNPJ_SECOND_WEIGHTS = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]


def _cnpj_char_value(char):
    return ord(char) - 48


def _cnpj_check_digit(base, weights):
    total = sum(_cnpj_char_value(char) * weight for char, weight in zip(base, weights))
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder


def normalize_cnpj(value):
    return re.sub(r"[^A-Za-z0-9]", "", value or "").upper()


def validate_cnpj(value):
    cnpj = normalize_cnpj(value)

    if len(cnpj) != 14 or not re.fullmatch(r"[A-Z0-9]{12}[0-9]{2}", cnpj):
        raise ValidationError(
            "CNPJ deve conter 14 caracteres, sendo os 2 últimos numéricos."
        )

    first_digit = _cnpj_check_digit(cnpj[:12], CNPJ_FIRST_WEIGHTS)
    second_digit = _cnpj_check_digit(cnpj[:12] + str(first_digit), CNPJ_SECOND_WEIGHTS)

    if cnpj[12:] != f"{first_digit}{second_digit}":
        raise ValidationError("CNPJ inválido.")
