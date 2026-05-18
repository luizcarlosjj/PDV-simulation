"""Funções utilitárias compartilhadas."""

from typing import Union


def format_brl(value: Union[float, int, None]) -> str:
    if value is None:
        return "R$ 0,00"
    formatted = f"{value:,.2f}"
    # Converte para formato brasileiro: 1,234.56 -> 1.234,56
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def parse_decimal(text: str) -> float:
    """Aceita '1.234,56' ou '1234.56' ou '1234,56'."""
    s = text.strip().replace("R$", "").strip()
    if not s:
        raise ValueError("Valor vazio.")
    if "," in s and "." in s:
        # Formato BR: ponto = milhar, vírgula = decimal
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    return float(s)
