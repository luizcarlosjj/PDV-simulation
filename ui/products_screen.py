"""Tela de cadastro / edição / exclusão de produtos."""

from tkinter import ttk, messagebox
import customtkinter as ctk

import database
from utils.helpers import format_brl, parse_decimal


class ProductsScreen(ctk.CTkFrame):
    def __init__(self, master) -> None:
        super().__init__(master, fg_color="transparent")
        self.selected_id: int | None = None
        self._build()
        self.refresh()

    def on_show(self) -> None:
        self.refresh()

    def _build(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Título
        ctk.CTkLabel(
            self,
            text="Produtos",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 6))

        # Form
        form = ctk.CTkFrame(self)
        form.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 12))
        for i in range(8):
            form.grid_columnconfigure(i, weight=0)
        form.grid_columnconfigure(7, weight=1)

        ctk.CTkLabel(form, text="Código").grid(row=0, column=0, padx=(14, 4), pady=10, sticky="w")
        self.entry_code = ctk.CTkEntry(form, width=120)
        self.entry_code.grid(row=0, column=1, padx=4, pady=10)

        ctk.CTkLabel(form, text="Nome").grid(row=0, column=2, padx=(14, 4), pady=10, sticky="w")
        self.entry_name = ctk.CTkEntry(form, width=260)
        self.entry_name.grid(row=0, column=3, padx=4, pady=10)

        ctk.CTkLabel(form, text="Preço (R$)").grid(row=0, column=4, padx=(14, 4), pady=10, sticky="w")
        self.entry_price = ctk.CTkEntry(form, width=110)
        self.entry_price.grid(row=0, column=5, padx=4, pady=10)

        ctk.CTkLabel(form, text="Estoque inicial").grid(row=0, column=6, padx=(14, 4), pady=10, sticky="w")
        self.entry_stock = ctk.CTkEntry(form, width=90)
        self.entry_stock.grid(row=0, column=7, padx=(4, 14), pady=10, sticky="w")

        btns = ctk.CTkFrame(form, fg_color="transparent")
        btns.grid(row=1, column=0, columnspan=8, sticky="ew", padx=10, pady=(0, 10))
        ctk.CTkButton(btns, text="Novo", width=110, command=self.clear_form).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="Salvar", width=110, command=self.save).pack(side="left", padx=4)
        ctk.CTkButton(btns, text="Excluir", width=110, fg_color="#c0392b", hover_color="#a93226", command=self.delete).pack(side="left", padx=4)

        ctk.CTkLabel(btns, text="Buscar:").pack(side="left", padx=(20, 6))
        self.entry_search = ctk.CTkEntry(btns, width=200, placeholder_text="Código ou nome...")
        self.entry_search.pack(side="left")
        self.entry_search.bind("<KeyRelease>", lambda _: self.refresh())

        # Tabela
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        cols = ("id", "code", "name", "price", "stock")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=15)
        self.tree.heading("id", text="ID")
        self.tree.heading("code", text="Código")
        self.tree.heading("name", text="Nome")
        self.tree.heading("price", text="Preço")
        self.tree.heading("stock", text="Estoque")
        self.tree.column("id", width=60, anchor="center")
        self.tree.column("code", width=110, anchor="w")
        self.tree.column("name", width=380, anchor="w")
        self.tree.column("price", width=120, anchor="e")
        self.tree.column("stock", width=100, anchor="center")
        self.tree.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=8)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        _apply_table_style()

    # ---------- Ações ----------

    def refresh(self) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)
        for p in database.list_products(self.entry_search.get().strip()):
            self.tree.insert(
                "",
                "end",
                values=(p["id"], p["code"], p["name"], format_brl(p["price"]), p["stock"]),
            )

    def clear_form(self) -> None:
        self.selected_id = None
        self.entry_code.delete(0, "end")
        self.entry_name.delete(0, "end")
        self.entry_price.delete(0, "end")
        self.entry_stock.delete(0, "end")
        self.entry_code.focus_set()

    def _on_select(self, _event) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        self.selected_id = int(values[0])
        prod = database.get_product_by_id(self.selected_id)
        if not prod:
            return
        self.entry_code.delete(0, "end"); self.entry_code.insert(0, prod["code"])
        self.entry_name.delete(0, "end"); self.entry_name.insert(0, prod["name"])
        self.entry_price.delete(0, "end"); self.entry_price.insert(0, f"{prod['price']:.2f}".replace(".", ","))
        self.entry_stock.delete(0, "end"); self.entry_stock.insert(0, str(prod["stock"]))
        self.entry_stock.configure(state="disabled")

    def save(self) -> None:
        code = self.entry_code.get().strip()
        name = self.entry_name.get().strip()
        if not code or not name:
            messagebox.showwarning("Atenção", "Informe código e nome.")
            return
        try:
            price = parse_decimal(self.entry_price.get())
        except ValueError:
            messagebox.showwarning("Atenção", "Preço inválido.")
            return
        try:
            if self.selected_id is None:
                stock_txt = self.entry_stock.get().strip() or "0"
                stock = int(parse_decimal(stock_txt))
                database.insert_product(code, name, price, stock)
                messagebox.showinfo("Sucesso", "Produto cadastrado.")
            else:
                database.update_product(self.selected_id, code, name, price)
                messagebox.showinfo("Sucesso", "Produto atualizado.")
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return
        self.entry_stock.configure(state="normal")
        self.clear_form()
        self.refresh()

    def delete(self) -> None:
        if self.selected_id is None:
            messagebox.showwarning("Atenção", "Selecione um produto.")
            return
        if not messagebox.askyesno("Confirmar", "Excluir o produto selecionado?"):
            return
        try:
            database.delete_product(self.selected_id)
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return
        self.entry_stock.configure(state="normal")
        self.clear_form()
        self.refresh()


_STYLE_APPLIED = False


def _apply_table_style() -> None:
    global _STYLE_APPLIED
    if _STYLE_APPLIED:
        return
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure(
        "Treeview",
        background="#ffffff",
        fieldbackground="#ffffff",
        foreground="#222",
        rowheight=26,
        bordercolor="#dadada",
        borderwidth=0,
        font=("Segoe UI", 10),
    )
    style.configure(
        "Treeview.Heading",
        background="#1f6aa5",
        foreground="white",
        font=("Segoe UI", 10, "bold"),
        padding=6,
    )
    style.map("Treeview", background=[("selected", "#1f6aa5")], foreground=[("selected", "white")])
    _STYLE_APPLIED = True
