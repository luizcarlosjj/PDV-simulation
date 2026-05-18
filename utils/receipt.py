"""Geração, salvamento (TXT/PDF) do cupom não fiscal."""

import os
import sys
from datetime import datetime

from .helpers import format_brl


COMPANY_NAME = "MEU ESTABELECIMENTO"
COMPANY_INFO = "CNPJ / Endereço"
RECEIPT_WIDTH = 42  # caracteres por linha (padrão 80mm térmica)


def _line(char: str = "-") -> str:
    return char * RECEIPT_WIDTH


def _center(text: str) -> str:
    return text.center(RECEIPT_WIDTH)


def _two_cols(left: str, right: str) -> str:
    space = RECEIPT_WIDTH - len(left) - len(right)
    if space < 1:
        space = 1
    return left + (" " * space) + right


def build_receipt_text(sale: dict, items: list[dict]) -> str:
    lines: list[str] = []
    lines.append(_center(COMPANY_NAME))
    lines.append(_center(COMPANY_INFO))
    lines.append(_center("CUPOM NAO FISCAL"))
    lines.append(_line("="))
    dt = sale["datetime"]
    if isinstance(dt, datetime):
        dt = dt.strftime("%d/%m/%Y %H:%M:%S")
    lines.append(_two_cols(f"Venda #{sale['id']}", dt))
    lines.append(_line())
    lines.append(_two_cols("ITEM", "VL TOTAL"))
    lines.append(_line())

    for it in items:
        nome = it["name"][: RECEIPT_WIDTH - 2]
        lines.append(nome)
        qtd = it["quantity"]
        unit = format_brl(it["unit_price"])
        sub = format_brl(it["subtotal"])
        qtd_txt = (f"{qtd:.0f}" if float(qtd).is_integer() else f"{qtd:.3f}")
        left = f"  {qtd_txt} x {unit}"
        lines.append(_two_cols(left, sub))

    lines.append(_line())
    lines.append(_two_cols("TOTAL", format_brl(sale["total"])))
    lines.append(_two_cols(f"FORMA: {sale['payment_method'].upper()}", ""))
    lines.append(_two_cols("VALOR PAGO", format_brl(sale["amount_paid"])))
    lines.append(_two_cols("TROCO", format_brl(sale["change_value"])))
    lines.append(_line("="))
    lines.append(_center("Obrigado pela preferencia!"))
    lines.append(_center("Este documento nao tem valor fiscal"))
    lines.append("")
    lines.append("")
    return "\n".join(lines)


def default_receipts_dir() -> str:
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "recibos")
    os.makedirs(path, exist_ok=True)
    return path


def save_text(path: str, content: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def save_pdf(path: str, content: str) -> None:
    """Gera um PDF do cupom em formato 80mm (largura padrão térmica)."""
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    lines = content.split("\n")

    page_width = 80 * mm
    font_size = 9
    line_height = font_size * 1.25
    top_margin = 8 * mm
    bottom_margin = 8 * mm
    side_margin = 4 * mm

    page_height = top_margin + bottom_margin + (len(lines) * line_height)
    if page_height < 60 * mm:
        page_height = 60 * mm

    c = canvas.Canvas(path, pagesize=(page_width, page_height))
    c.setFont("Courier", font_size)

    y = page_height - top_margin
    for line in lines:
        c.drawString(side_margin, y, line)
        y -= line_height

    c.save()
