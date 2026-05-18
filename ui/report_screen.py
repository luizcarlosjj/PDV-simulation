"""Tela de relatórios simples (total do dia, mês, top produtos)."""

from tkinter import ttk, messagebox
from datetime import date, timedelta
from datetime import datetime
import customtkinter as ctk

import database
from utils.helpers import format_brl
from ui.products_screen import _apply_table_style


class ReportScreen(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master, fg_color="transparent")
        self._build()
        self.refresh()

    def on_show(self) -> None:
        self.refresh()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(
            self, text="Relatórios",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(18, 6))

        # Filtros
        filters = ctk.CTkFrame(self)
        filters.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 10))

        today = date.today().isoformat()
        ctk.CTkLabel(filters, text="De:").grid(row=0, column=0, padx=(14, 4), pady=10)
        self.entry_start = ctk.CTkEntry(filters, width=120)
        self.entry_start.insert(0, today)
        self.entry_start.grid(row=0, column=1, padx=4, pady=10)

        ctk.CTkLabel(filters, text="Até:").grid(row=0, column=2, padx=(14, 4), pady=10)
        self.entry_end = ctk.CTkEntry(filters, width=120)
        self.entry_end.insert(0, today)
        self.entry_end.grid(row=0, column=3, padx=4, pady=10)

        ctk.CTkButton(filters, text="Hoje", width=80, command=self._today).grid(row=0, column=4, padx=4)
        ctk.CTkButton(filters, text="Mês atual", width=100, command=self._month).grid(row=0, column=5, padx=4)
        ctk.CTkButton(filters, text="7 dias", width=80, command=lambda: self._range(7)).grid(row=0, column=6, padx=4)
        ctk.CTkButton(filters, text="Atualizar", width=110, command=self.refresh).grid(row=0, column=7, padx=(14, 8))

        # KPIs
        kpis = ctk.CTkFrame(self, fg_color="transparent")
        kpis.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 12))
        kpis.grid_columnconfigure((0, 1), weight=1)

        self.card_total = _Card(kpis, "Total vendido", "R$ 0,00", "#1f6aa5")
        self.card_total.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.card_qtd = _Card(kpis, "Vendas realizadas", "0", "#27ae60")
        self.card_qtd.grid(row=0, column=1, padx=(8, 0), sticky="ew")

        # Tabelas: pagamento e top produtos
        left = ctk.CTkFrame(self)
        left.grid(row=3, column=0, sticky="nsew", padx=(20, 8), pady=(0, 20))
        left.grid_rowconfigure(1, weight=1); left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="Por forma de pagamento", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 4)
        )
        cols1 = ("payment", "qtd", "total")
        self.tree_pay = ttk.Treeview(left, columns=cols1, show="headings")
        self.tree_pay.heading("payment", text="Forma")
        self.tree_pay.heading("qtd", text="Qtd")
        self.tree_pay.heading("total", text="Total")
        self.tree_pay.column("payment", width=170, anchor="w")
        self.tree_pay.column("qtd", width=70, anchor="center")
        self.tree_pay.column("total", width=140, anchor="e")
        self.tree_pay.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        right = ctk.CTkFrame(self)
        right.grid(row=3, column=1, sticky="nsew", padx=(8, 20), pady=(0, 20))
        right.grid_rowconfigure(1, weight=1); right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="Top 10 produtos", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 4)
        )
        cols2 = ("name", "qtd", "total")
        self.tree_top = ttk.Treeview(right, columns=cols2, show="headings")
        self.tree_top.heading("name", text="Produto")
        self.tree_top.heading("qtd", text="Qtd")
        self.tree_top.heading("total", text="Total")
        self.tree_top.column("name", width=260, anchor="w")
        self.tree_top.column("qtd", width=70, anchor="center")
        self.tree_top.column("total", width=140, anchor="e")
        self.tree_top.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        _apply_table_style()

    # ---------- Ações ----------

    def _today(self) -> None:
        today = date.today().isoformat()
        self.entry_start.delete(0, "end"); self.entry_start.insert(0, today)
        self.entry_end.delete(0, "end"); self.entry_end.insert(0, today)
        self.refresh()

    def _month(self) -> None:
        today = date.today()
        first = today.replace(day=1)
        self.entry_start.delete(0, "end"); self.entry_start.insert(0, first.isoformat())
        self.entry_end.delete(0, "end"); self.entry_end.insert(0, today.isoformat())
        self.refresh()

    def _range(self, days: int) -> None:
        end = date.today()
        start = end - timedelta(days=days - 1)
        self.entry_start.delete(0, "end"); self.entry_start.insert(0, start.isoformat())
        self.entry_end.delete(0, "end"); self.entry_end.insert(0, end.isoformat())
        self.refresh()

    def refresh(self) -> None:
        try:
            start = self.entry_start.get().strip()
            end = self.entry_end.get().strip()
            datetime.fromisoformat(start)
            datetime.fromisoformat(end)
        except ValueError:
            messagebox.showwarning("Atenção", "Data inválida. Use YYYY-MM-DD.")
            return
        data = database.report_summary(start, end)

        self.card_total.set_value(format_brl(data["total"]))
        self.card_qtd.set_value(str(data["qtd_vendas"]))

        for r in self.tree_pay.get_children():
            self.tree_pay.delete(r)
        for row in data["por_pagamento"]:
            self.tree_pay.insert("", "end", values=(
                row["payment_method"], row["qtd"], format_brl(row["total"])
            ))

        for r in self.tree_top.get_children():
            self.tree_top.delete(r)
        for row in data["top_produtos"]:
            qtd = row["qtd"]
            qtd_txt = f"{qtd:.0f}" if float(qtd).is_integer() else f"{qtd:.3f}"
            self.tree_top.insert("", "end", values=(
                row["name"], qtd_txt, format_brl(row["total"])
            ))


class _Card(ctk.CTkFrame):
    def __init__(self, master, title: str, value: str, color: str) -> None:
        super().__init__(master, corner_radius=10)
        ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=13)).pack(
            anchor="w", padx=18, pady=(14, 0)
        )
        self.value_lbl = ctk.CTkLabel(
            self, text=value, font=ctk.CTkFont(size=30, weight="bold"),
            text_color=color,
        )
        self.value_lbl.pack(anchor="w", padx=18, pady=(0, 14))

    def set_value(self, v: str) -> None:
        self.value_lbl.configure(text=v)
