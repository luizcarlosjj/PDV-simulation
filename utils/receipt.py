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
    """Gera um PDF mínimo (Courier, 80mm) sem dependências externas.

    Implementa apenas o necessário do formato PDF 1.4 para texto monoespaçado
    em uma página. Evita depender de reportlab/fpdf2 — ambos arrastam
    bibliotecas que quebram o PyInstaller em Python 3.10.0.
    """
    lines = content.split("\n")

    # PDF usa unidade "point" (1 pt = 1/72"). 1 mm = 2.834645669 pt.
    mm = 2.834645669
    page_width = 80 * mm
    side_margin = 4 * mm
    top_margin = 6 * mm
    bottom_margin = 6 * mm
    font_size = 9
    line_height = font_size * 1.2  # pt
    page_height = max(60 * mm, top_margin + bottom_margin + len(lines) * line_height)

    # Escapa caracteres especiais do PDF e converte para Latin-1 (WinAnsi)
    def pdf_escape(text: str) -> bytes:
        safe = text.encode("latin-1", errors="replace")
        return safe.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")

    # Stream de conteúdo: posiciona texto e desenha cada linha
    content_lines: list[bytes] = [b"BT", f"/F1 {font_size} Tf".encode("latin-1")]
    y = page_height - top_margin - font_size
    content_lines.append(f"{side_margin:.2f} {y:.2f} Td".encode("latin-1"))
    content_lines.append(b"(" + pdf_escape(lines[0] if lines else "") + b") Tj")
    for line in lines[1:]:
        content_lines.append(f"0 -{line_height:.2f} Td".encode("latin-1"))
        content_lines.append(b"(" + pdf_escape(line) + b") Tj")
    content_lines.append(b"ET")
    stream = b"\n".join(content_lines)

    # Objetos PDF
    objects: list[bytes] = []

    def add_obj(body: bytes) -> int:
        objects.append(body)
        return len(objects)  # número do objeto (1-based)

    # 1: Catalog  2: Pages  3: Page  4: Font  5: Content
    catalog_num = add_obj(b"<< /Type /Catalog /Pages 2 0 R >>")
    pages_num = add_obj(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    page_num = add_obj(
        f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width:.2f} {page_height:.2f}] "
        f"/Contents 5 0 R /Resources << /Font << /F1 4 0 R >> >> >>".encode("latin-1")
    )
    font_num = add_obj(
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>"
    )
    content_num = add_obj(
        f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1")
        + stream
        + b"\nendstream"
    )

    # Monta o arquivo PDF
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets: list[int] = []
    for i, obj_body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode("latin-1") + obj_body + b"\nendobj\n"

    xref_offset = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode("latin-1")
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode("latin-1")
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_num} 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode("latin-1")

    with open(path, "wb") as f:
        f.write(out)
