"""Tela de venda - principal do PDV."""

from tkinter import ttk, messagebox
import customtkinter as ctk

import database
from utils.helpers import format_brl, parse_decimal
from ui.products_screen import _apply_table_style
from ui.receipt_window import ReceiptWindow


class SaleScreen(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master, fg_color="transparent")
        # itens: [{product_id, code, name, quantity, unit_price, stock}]
        self.items: list[dict] = []
        self._build()

    def on_show(self) -> None:
        self.entry_code.focus_set()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self, text="Venda", font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(18, 6))

        # ----- COLUNA ESQUERDA: itens da venda -----
        left = ctk.CTkFrame(self)
        left.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=(0, 20))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(2, weight=1)

        add_bar = ctk.CTkFrame(left, fg_color="transparent")
        add_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        ctk.CTkLabel(add_bar, text="Código").grid(row=0, column=0, padx=(0, 4))
        self.entry_code = ctk.CTkEntry(add_bar, width=140)
        self.entry_code.grid(row=0, column=1, padx=4)
        self.entry_code.bind("<Return>", lambda _: self._add_by_code())

        ctk.CTkLabel(add_bar, text="Qtd").grid(row=0, column=2, padx=(14, 4))
        self.entry_qty = ctk.CTkEntry(add_bar, width=70)
        self.entry_qty.insert(0, "1")
        self.entry_qty.grid(row=0, column=3, padx=4)
        self.entry_qty.bind("<Return>", lambda _: self._add_by_code())

        ctk.CTkButton(add_bar, text="Adicionar", width=110, command=self._add_by_code).grid(
            row=0, column=4, padx=8
        )
        ctk.CTkButton(
            add_bar, text="Buscar produto...", width=140, command=self._open_product_search
        ).grid(row=0, column=5, padx=4)

        ctk.CTkButton(
            add_bar, text="Remover item", width=130,
            fg_color="#c0392b", hover_color="#a93226",
            command=self._remove_selected,
        ).grid(row=0, column=6, padx=(20, 0))

        ctk.CTkButton(
            add_bar, text="Limpar venda", width=130,
            fg_color="gray", hover_color="#555",
            command=self._clear_items,
        ).grid(row=0, column=7, padx=8)

        # Tabela itens
        table_frame = ctk.CTkFrame(left, fg_color="transparent")
        table_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 8))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        cols = ("code", "name", "qty", "price", "subtotal")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        self.tree.heading("code", text="Código")
        self.tree.heading("name", text="Produto")
        self.tree.heading("qty", text="Qtd")
        self.tree.heading("price", text="Preço un.")
        self.tree.heading("subtotal", text="Subtotal")
        self.tree.column("code", width=90, anchor="w")
        self.tree.column("name", width=300, anchor="w")
        self.tree.column("qty", width=70, anchor="center")
        self.tree.column("price", width=110, anchor="e")
        self.tree.column("subtotal", width=120, anchor="e")
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)

        # ----- COLUNA DIREITA: totais e pagamento -----
        right = ctk.CTkFrame(self)
        right.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=(0, 20))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(99, weight=1)

        ctk.CTkLabel(right, text="TOTAL", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, padx=16, pady=(16, 0), sticky="w"
        )
        self.lbl_total = ctk.CTkLabel(
            right, text="R$ 0,00", font=ctk.CTkFont(size=42, weight="bold"),
            text_color="#1f6aa5",
        )
        self.lbl_total.grid(row=1, column=0, padx=16, pady=(0, 18), sticky="w")

        ctk.CTkLabel(right, text="Forma de pagamento").grid(row=2, column=0, padx=16, sticky="w")
        self.combo_payment = ctk.CTkOptionMenu(
            right,
            values=["Dinheiro", "Cartão Débito", "Cartão Crédito", "PIX"],
            command=self._on_payment_change,
        )
        self.combo_payment.set("Dinheiro")
        self.combo_payment.grid(row=3, column=0, padx=16, pady=(2, 12), sticky="ew")

        ctk.CTkLabel(right, text="Valor recebido").grid(row=4, column=0, padx=16, sticky="w")
        self.entry_paid = ctk.CTkEntry(right, font=ctk.CTkFont(size=16))
        self.entry_paid.grid(row=5, column=0, padx=16, pady=(2, 8), sticky="ew")
        self.entry_paid.bind("<KeyRelease>", lambda _: self._update_change())

        change_row = ctk.CTkFrame(right, fg_color="transparent")
        change_row.grid(row=6, column=0, sticky="ew", padx=16, pady=(4, 16))
        change_row.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(change_row, text="TROCO", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w")
        self.lbl_change = ctk.CTkLabel(
            change_row, text="R$ 0,00",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#27ae60",
        )
        self.lbl_change.grid(row=1, column=0, sticky="w")

        ctk.CTkButton(
            right, text="FINALIZAR VENDA (F9)", height=60,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="#27ae60", hover_color="#1f8a4c",
            command=self._finalize,
        ).grid(row=7, column=0, padx=16, pady=8, sticky="ew")

        _apply_table_style()

    # ---------- Adicionar / remover itens ----------

    def _add_by_code(self) -> None:
        code = self.entry_code.get().strip()
        if not code:
            return
        try:
            qty = parse_decimal(self.entry_qty.get() or "1")
            if qty <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Atenção", "Quantidade inválida.")
            return
        prod = database.get_product_by_code(code)
        if prod is None:
            messagebox.showwarning("Atenção", f"Produto '{code}' não encontrado.")
            return
        self._add_product(prod, qty)
        self.entry_code.delete(0, "end")
        self.entry_qty.delete(0, "end")
        self.entry_qty.insert(0, "1")
        self.entry_code.focus_set()

    def _add_product(self, prod, qty: float) -> None:
        # Verifica se já está no carrinho
        for it in self.items:
            if it["product_id"] == prod["id"]:
                new_qty = it["quantity"] + qty
                if new_qty > prod["stock"]:
                    messagebox.showwarning(
                        "Estoque", f"Estoque insuficiente. Disponível: {prod['stock']}."
                    )
                    return
                it["quantity"] = new_qty
                self._refresh_table()
                return
        if qty > prod["stock"]:
            messagebox.showwarning(
                "Estoque", f"Estoque insuficiente. Disponível: {prod['stock']}."
            )
            return
        self.items.append({
            "product_id": prod["id"],
            "code": prod["code"],
            "name": prod["name"],
            "quantity": qty,
            "unit_price": prod["price"],
            "stock": prod["stock"],
        })
        self._refresh_table()

    def _remove_selected(self) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        if 0 <= idx < len(self.items):
            del self.items[idx]
            self._refresh_table()

    def _clear_items(self) -> None:
        if not self.items:
            return
        if messagebox.askyesno("Confirmar", "Limpar a venda atual?"):
            self.items.clear()
            self.entry_paid.delete(0, "end")
            self._refresh_table()

    def _refresh_table(self) -> None:
        for r in self.tree.get_children():
            self.tree.delete(r)
        for it in self.items:
            qty = it["quantity"]
            qty_txt = f"{qty:.0f}" if float(qty).is_integer() else f"{qty:.3f}"
            subtotal = round(qty * it["unit_price"], 2)
            self.tree.insert(
                "", "end",
                values=(
                    it["code"], it["name"], qty_txt,
                    format_brl(it["unit_price"]), format_brl(subtotal),
                ),
            )
        self._refresh_totals()

    def _refresh_totals(self) -> None:
        total = sum(it["quantity"] * it["unit_price"] for it in self.items)
        self.lbl_total.configure(text=format_brl(total))
        self._update_change()

    def _total(self) -> float:
        return round(sum(it["quantity"] * it["unit_price"] for it in self.items), 2)

    def _on_payment_change(self, _value: str) -> None:
        self._update_change()

    def _update_change(self) -> None:
        try:
            paid = parse_decimal(self.entry_paid.get()) if self.entry_paid.get().strip() else 0.0
        except ValueError:
            paid = 0.0
        change = paid - self._total()
        if self.combo_payment.get() != "Dinheiro":
            self.lbl_change.configure(text="—", text_color="gray")
            return
        if change < 0:
            self.lbl_change.configure(text=format_brl(change), text_color="#c0392b")
        else:
            self.lbl_change.configure(text=format_brl(change), text_color="#27ae60")

    # ---------- Buscar produto ----------

    def _open_product_search(self) -> None:
        win = ctk.CTkToplevel(self)
        win.title("Buscar produto")
        win.geometry("620x420")
        win.transient(self.winfo_toplevel())
        win.grab_set()
        win.grid_columnconfigure(0, weight=1)
        win.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(win, text="Buscar produto", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, padx=14, pady=(14, 4), sticky="w"
        )
        entry = ctk.CTkEntry(win, placeholder_text="Digite código ou nome...")
        entry.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
        entry.focus_set()

        table_frame = ctk.CTkFrame(win, fg_color="transparent")
        table_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        cols = ("code", "name", "price", "stock")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        for c, w, a in [
            ("code", 90, "w"), ("name", 300, "w"),
            ("price", 100, "e"), ("stock", 80, "center"),
        ]:
            tree.heading(c, text=c.capitalize())
            tree.column(c, width=w, anchor=a)
        tree.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=sb.set)

        def refresh_list() -> None:
            for r in tree.get_children():
                tree.delete(r)
            for p in database.list_products(entry.get().strip()):
                tree.insert("", "end", iid=str(p["id"]),
                            values=(p["code"], p["name"], format_brl(p["price"]), p["stock"]))

        def select_and_close(_event=None) -> None:
            sel = tree.selection()
            if not sel:
                return
            pid = int(sel[0])
            prod = database.get_product_by_id(pid)
            if prod is not None:
                self._add_product(prod, 1)
            win.destroy()

        tree.bind("<Double-1>", select_and_close)
        entry.bind("<KeyRelease>", lambda _: refresh_list())
        entry.bind("<Return>", select_and_close)

        ctk.CTkButton(win, text="Adicionar selecionado", command=select_and_close).grid(
            row=3, column=0, pady=(0, 10)
        )

        refresh_list()

    # ---------- Finalização ----------

    def _finalize(self) -> None:
        if not self.items:
            messagebox.showwarning("Atenção", "Adicione itens à venda.")
            return
        total = self._total()
        payment = self.combo_payment.get()
        if payment == "Dinheiro":
            try:
                paid = parse_decimal(self.entry_paid.get())
            except ValueError:
                messagebox.showwarning("Atenção", "Informe o valor recebido.")
                return
            if paid + 1e-6 < total:
                messagebox.showwarning("Atenção", "Valor recebido menor que o total.")
                return
        else:
            paid = total

        try:
            sale_id = database.create_sale(self.items, payment, paid)
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return

        sale = database.get_sale(sale_id)
        items = database.get_sale_items(sale_id)
        ReceiptWindow(self.winfo_toplevel(), dict(sale), [dict(i) for i in items])

        self.items.clear()
        self.entry_paid.delete(0, "end")
        self._refresh_table()
