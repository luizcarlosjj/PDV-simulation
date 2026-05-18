"""Histórico de vendas - consulta e reimpressão de cupons."""

from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
import customtkinter as ctk

import database
from utils.helpers import format_brl
from ui.products_screen import _apply_table_style
from ui.receipt_window import ReceiptWindow


class HistoryScreen(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master, fg_color="transparent")
        self._build()
        self.refresh()

    def on_show(self) -> None:
        self.refresh()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            self, text="Histórico de vendas",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 6))

        filters = ctk.CTkFrame(self)
        filters.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        today = date.today().isoformat()
        ctk.CTkLabel(filters, text="De:").grid(row=0, column=0, padx=(14, 4), pady=10)
        self.entry_start = ctk.CTkEntry(filters, width=120)
        self.entry_start.insert(0, today)
        self.entry_start.grid(row=0, column=1, padx=4, pady=10)

        ctk.CTkLabel(filters, text="Até:").grid(row=0, column=2, padx=(14, 4), pady=10)
        self.entry_end = ctk.CTkEntry(filters, width=120)
        self.entry_end.insert(0, today)
        self.entry_end.grid(row=0, column=3, padx=4, pady=10)

        ctk.CTkLabel(filters, text="(YYYY-MM-DD)", text_color="gray").grid(
            row=0, column=4, padx=8
        )

        ctk.CTkButton(filters, text="Hoje", width=80, command=self._set_today).grid(
            row=0, column=5, padx=4
        )
        ctk.CTkButton(filters, text="7 dias", width=80, command=lambda: self._set_range(7)).grid(
            row=0, column=6, padx=4
        )
        ctk.CTkButton(filters, text="30 dias", width=80, command=lambda: self._set_range(30)).grid(
            row=0, column=7, padx=4
        )
        ctk.CTkButton(filters, text="Filtrar", width=100, command=self.refresh).grid(
            row=0, column=8, padx=(12, 8)
        )
        ctk.CTkButton(
            filters, text="Ver / Reimprimir cupom", width=180,
            fg_color="#1f6aa5", command=self._reprint,
        ).grid(row=0, column=9, padx=8)

        # Tabela
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 6))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        cols = ("id", "dt", "payment", "paid", "change", "total")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        self.tree.heading("id", text="Venda")
        self.tree.heading("dt", text="Data/Hora")
        self.tree.heading("payment", text="Pagamento")
        self.tree.heading("paid", text="Recebido")
        self.tree.heading("change", text="Troco")
        self.tree.heading("total", text="Total")
        self.tree.column("id", width=80, anchor="center")
        self.tree.column("dt", width=170, anchor="center")
        self.tree.column("payment", width=140, anchor="w")
        self.tree.column("paid", width=120, anchor="e")
        self.tree.column("change", width=120, anchor="e")
        self.tree.column("total", width=140, anchor="e")
        self.tree.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns", pady=8)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<Double-1>", lambda _: self._reprint())

        self.lbl_summary = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=14, weight="bold")
        )
        self.lbl_summary.grid(row=3, column=0, sticky="w", padx=24, pady=(0, 14))

        _apply_table_style()

    # ---------- Ações ----------

    def _set_today(self) -> None:
        today = date.today().isoformat()
        self.entry_start.delete(0, "end"); self.entry_start.insert(0, today)
        self.entry_end.delete(0, "end"); self.entry_end.insert(0, today)
        self.refresh()

    def _set_range(self, days: int) -> None:
        end = date.today()
        start = end - timedelta(days=days - 1)
        self.entry_start.delete(0, "end"); self.entry_start.insert(0, start.isoformat())
        self.entry_end.delete(0, "end"); self.entry_end.insert(0, end.isoformat())
        self.refresh()

    def refresh(self) -> None:
        for r in self.tree.get_children():
            self.tree.delete(r)
        try:
            start = self.entry_start.get().strip()
            end = self.entry_end.get().strip()
            datetime.fromisoformat(start)
            datetime.fromisoformat(end)
        except ValueError:
            messagebox.showwarning("Atenção", "Data inválida. Use o formato YYYY-MM-DD.")
            return
        sales = database.list_sales(start, end)
        total = 0.0
        for s in sales:
            dt = s["datetime"]
            try:
                dt = datetime.fromisoformat(dt).strftime("%d/%m/%Y %H:%M")
            except Exception:
                pass
            self.tree.insert("", "end", iid=str(s["id"]), values=(
                s["id"], dt, s["payment_method"],
                format_brl(s["amount_paid"]),
                format_brl(s["change_value"]),
                format_brl(s["total"]),
            ))
            total += s["total"]
        self.lbl_summary.configure(
            text=f"{len(sales)} venda(s)   |   Total: {format_brl(total)}"
        )

    def _reprint(self) -> None:
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione uma venda.")
            return
        sale_id = int(sel[0])
        sale = database.get_sale(sale_id)
        items = database.get_sale_items(sale_id)
        if sale:
            ReceiptWindow(self.winfo_toplevel(), dict(sale), [dict(i) for i in items])
