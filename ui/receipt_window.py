"""Janela do cupom não fiscal: preview + ações manuais (TXT, PDF, Imprimir)."""

import os
from tkinter import filedialog, messagebox
import customtkinter as ctk

from utils.receipt import build_receipt_text, save_text, save_pdf, default_receipts_dir
from ui.print_dialog import show_print_dialog


class ReceiptWindow(ctk.CTkToplevel):
    def __init__(self, master, sale: dict, items: list[dict]) -> None:
        super().__init__(master)
        self.sale = sale
        self.items = items
        self.content = build_receipt_text(sale, items)

        self.title(f"Cupom não fiscal - Venda #{sale['id']}")
        self.geometry("480x640")
        self.minsize(420, 480)
        self.transient(master)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            self,
            text=f"Venda #{sale['id']} concluída",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(14, 6))

        # Preview do cupom (texto monoespaçado, igual ao que sai na impressora)
        self.textbox = ctk.CTkTextbox(
            self, font=("Consolas", 12), wrap="none",
            activate_scrollbars=True,
        )
        self.textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.textbox.insert("1.0", self.content)
        self.textbox.configure(state="disabled")

        # Barra de ações
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 12))
        btns.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="b")

        ctk.CTkButton(
            btns, text="⬇  Baixar TXT", command=self._save_txt, height=40,
        ).grid(row=0, column=0, padx=4, sticky="ew")
        ctk.CTkButton(
            btns, text="⬇  Baixar PDF", command=self._save_pdf, height=40,
        ).grid(row=0, column=1, padx=4, sticky="ew")
        ctk.CTkButton(
            btns, text="🖨  Imprimir",
            fg_color="#1f6aa5", hover_color="#175a8c",
            command=self._print, height=40,
        ).grid(row=0, column=2, padx=4, sticky="ew")
        ctk.CTkButton(
            btns, text="Fechar", fg_color="gray", hover_color="#555",
            command=self.destroy, height=40,
        ).grid(row=0, column=3, padx=4, sticky="ew")

        # Foco e visibilidade — sem auto-print, sem auto-save
        self.bind("<Escape>", lambda _: self.destroy())
        self.bind("<Control-p>", lambda _: self._print())
        self.bind("<Control-s>", lambda _: self._save_txt())
        self.after(80, self._raise)

    def _raise(self) -> None:
        self.lift()
        self.focus_force()

    # ---------- Ações ----------

    def _default_filename(self, ext: str) -> str:
        return f"cupom_venda_{self.sale['id']:06d}.{ext}"

    def _initial_dir(self) -> str:
        try:
            return default_receipts_dir()
        except Exception:
            return os.path.expanduser("~")

    def _save_txt(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Baixar cupom como TXT",
            defaultextension=".txt",
            initialdir=self._initial_dir(),
            initialfile=self._default_filename("txt"),
            filetypes=[("Arquivo de texto", "*.txt"), ("Todos os arquivos", "*.*")],
        )
        if not path:
            return
        try:
            save_text(path, self.content)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível salvar:\n{e}", parent=self)
            return
        messagebox.showinfo("Salvo", f"Cupom salvo em:\n{path}", parent=self)

    def _save_pdf(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Baixar cupom como PDF",
            defaultextension=".pdf",
            initialdir=self._initial_dir(),
            initialfile=self._default_filename("pdf"),
            filetypes=[("PDF", "*.pdf"), ("Todos os arquivos", "*.*")],
        )
        if not path:
            return
        try:
            save_pdf(path, self.content)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível gerar PDF:\n{e}", parent=self)
            return
        messagebox.showinfo("Salvo", f"PDF salvo em:\n{path}", parent=self)

    def _print(self) -> None:
        show_print_dialog(self, self.content)
