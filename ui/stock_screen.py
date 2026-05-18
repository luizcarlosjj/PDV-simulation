"""Tela de controle de estoque (entradas, saídas, ajustes e histórico)."""

from tkinter import ttk, messagebox
from datetime import datetime
import customtkinter as ctk

import database
from utils.helpers import parse_decimal
from ui.products_screen import _apply_table_style


class StockScreen(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master, fg_color="transparent")
        self._products: list = []
        self._build()
        self.refresh()

    def on_show(self) -> None:
        self.refresh()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self,
            text="Estoque",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(18, 6))

        # Coluna esquerda: lista de produtos com estoque
        left = ctk.CTkFrame(self)
        left.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=(0, 20))
        left.grid_rowconfigure(2, weight=1)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="Posição de estoque", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 4)
        )
        self.entry_search = ctk.CTkEntry(left, placeholder_text="Buscar produto...")
        self.entry_search.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 8))
        self.entry_search.bind("<KeyRelease>", lambda _: self._refresh_products())

        table_frame = ctk.CTkFrame(left, fg_color="transparent")
        table_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        cols = ("id", "code", "name", "stock")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("code", text="Código")
        self.tree.heading("name", text="Nome")
        self.tree.heading("stock", text="Qtd")
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("code", width=90, anchor="w")
        self.tree.column("name", width=240, anchor="w")
        self.tree.column("stock", width=80, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Coluna direita: movimentação + histórico
        right = ctk.CTkFrame(self)
        right.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=(0, 20))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(right, text="Movimentar estoque", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=12, pady=(10, 4)
        )

        self.lbl_selected = ctk.CTkLabel(
            right, text="Selecione um produto à esquerda.", text_color="gray"
        )
        self.lbl_selected.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))

        form = ctk.CTkFrame(right, fg_color="transparent")
        form.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 10))

        ctk.CTkLabel(form, text="Tipo").grid(row=0, column=0, padx=4, pady=4, sticky="w")
        self.combo_type = ctk.CTkOptionMenu(
            form, values=["entrada", "saida", "ajuste"], width=130
        )
        self.combo_type.set("entrada")
        self.combo_type.grid(row=0, column=1, padx=4, pady=4)

        ctk.CTkLabel(form, text="Quantidade").grid(row=0, column=2, padx=(14, 4), pady=4, sticky="w")
        self.entry_qty = ctk.CTkEntry(form, width=100)
        self.entry_qty.grid(row=0, column=3, padx=4, pady=4)

        ctk.CTkLabel(form, text="Motivo").grid(row=1, column=0, padx=4, pady=4, sticky="w")
        self.entry_reason = ctk.CTkEntry(form, width=350, placeholder_text="(opcional)")
        self.entry_reason.grid(row=1, column=1, columnspan=3, padx=4, pady=4, sticky="ew")

        ctk.CTkButton(form, text="Aplicar", width=130, command=self._apply).grid(
            row=2, column=0, columnspan=4, pady=(8, 0), sticky="w", padx=4
        )

        # Histórico
        ctk.CTkLabel(right, text="Histórico de movimentos", font=ctk.CTkFont(weight="bold")).grid(
            row=3, column=0, sticky="nw", padx=12, pady=(10, 4)
        )
        hist_frame = ctk.CTkFrame(right, fg_color="transparent")
        hist_frame.grid(row=4, column=0, sticky="nsew", padx=8, pady=(0, 8))
        hist_frame.grid_rowconfigure(0, weight=1)
        hist_frame.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(4, weight=2)

        cols2 = ("dt", "type", "qty", "reason")
        self.tree_hist = ttk.Treeview(hist_frame, columns=cols2, show="headings", height=8)
        self.tree_hist.heading("dt", text="Data")
        self.tree_hist.heading("type", text="Tipo")
        self.tree_hist.heading("qty", text="Qtd")
        self.tree_hist.heading("reason", text="Motivo")
        self.tree_hist.column("dt", width=140, anchor="w")
        self.tree_hist.column("type", width=80, anchor="center")
        self.tree_hist.column("qty", width=70, anchor="center")
        self.tree_hist.column("reason", width=240, anchor="w")
        self.tree_hist.grid(row=0, column=0, sticky="nsew")
        scrollbar2 = ttk.Scrollbar(hist_frame, orient="vertical", command=self.tree_hist.yview)
        scrollbar2.grid(row=0, column=1, sticky="ns")
        self.tree_hist.configure(yscrollcommand=scrollbar2.set)

        _apply_table_style()

    # ---------- Lógica ----------

    def refresh(self) -> None:
        self._refresh_products()
        self._refresh_history()

    def _refresh_products(self) -> None:
        for r in self.tree.get_children():
            self.tree.delete(r)
        self._products = database.list_products(self.entry_search.get().strip())
        for p in self._products:
            tag = "low" if p["stock"] <= 5 else ""
            self.tree.insert(
                "", "end",
                values=(p["id"], p["code"], p["name"], p["stock"]),
                tags=(tag,),
            )
        self.tree.tag_configure("low", background="#fff3cd")

    def _refresh_history(self, product_id: int | None = None) -> None:
        for r in self.tree_hist.get_children():
            self.tree_hist.delete(r)
        for m in database.list_stock_movements(product_id):
            dt = m["datetime"]
            try:
                dt = datetime.fromisoformat(dt).strftime("%d/%m/%Y %H:%M")
            except Exception:
                pass
            qty = m["quantity"]
            qty_txt = f"{qty:.0f}" if float(qty).is_integer() else f"{qty:.3f}"
            self.tree_hist.insert(
                "", "end",
                values=(dt, m["type"], qty_txt, m["reason"] or ""),
            )

    def _on_select(self, _event) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        product_id = int(values[0])
        prod = database.get_product_by_id(product_id)
        if prod is None:
            return
        self.lbl_selected.configure(
            text=f"Produto: [{prod['code']}] {prod['name']}  |  Estoque atual: {prod['stock']}",
            text_color=("gray10", "gray90"),
        )
        self._selected_product_id = product_id
        self._refresh_history(product_id)

    def _apply(self) -> None:
        pid = getattr(self, "_selected_product_id", None)
        if pid is None:
            messagebox.showwarning("Atenção", "Selecione um produto.")
            return
        try:
            qty = parse_decimal(self.entry_qty.get())
            if qty <= 0:
                raise ValueError("Quantidade deve ser maior que zero.")
        except ValueError as e:
            messagebox.showwarning("Atenção", f"Quantidade inválida. {e}")
            return
        try:
            database.adjust_stock(
                pid, qty, self.combo_type.get(), self.entry_reason.get().strip()
            )
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return
        self.entry_qty.delete(0, "end")
        self.entry_reason.delete(0, "end")
        self.refresh()
        messagebox.showinfo("Sucesso", "Movimento registrado.")
