"""Diálogo de impressão estilo Ctrl+P (seletor de impressora + cópias)."""

import sys
from tkinter import messagebox
import customtkinter as ctk


def show_print_dialog(parent, content: str) -> None:
    if sys.platform.startswith("win"):
        _show_windows_dialog(parent, content)
    else:
        _show_unix_dialog(parent, content)


# ---------- Windows ----------

def _list_windows_printers() -> tuple[list[str], str]:
    try:
        import win32print
    except ImportError:
        return [], ""
    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    printers = win32print.EnumPrinters(flags)
    names = sorted({p[2] for p in printers})
    try:
        default = win32print.GetDefaultPrinter()
    except Exception:
        default = names[0] if names else ""
    return names, default


def _print_windows(printer_name: str, content: str, copies: int) -> tuple[bool, str]:
    try:
        import win32ui
    except ImportError:
        return False, "pywin32 não instalado."

    try:
        for _ in range(copies):
            dc = win32ui.CreateDC()
            dc.CreatePrinterDC(printer_name)
            dc.StartDoc("Cupom Nao Fiscal")
            dc.StartPage()

            font = win32ui.CreateFont({
                "name": "Courier New",
                "height": 48,  # ~10pt em MM_TEXT
                "weight": 400,
            })
            dc.SelectObject(font)

            x = 80
            y = 80
            line_height = 56
            for line in content.split("\n"):
                dc.TextOut(x, y, line)
                y += line_height

            dc.EndPage()
            dc.EndDoc()
        return True, f"Enviado para '{printer_name}'."
    except Exception as e:
        return False, f"Falha ao imprimir: {e}"


def _show_windows_dialog(parent, content: str) -> None:
    printers, default = _list_windows_printers()
    if not printers:
        messagebox.showwarning(
            "Imprimir", "Nenhuma impressora instalada foi encontrada.", parent=parent
        )
        return

    win = ctk.CTkToplevel(parent)
    win.title("Imprimir cupom")
    win.geometry("460x340")
    win.resizable(False, False)
    win.transient(parent)

    win.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        win, text="Imprimir cupom", font=ctk.CTkFont(size=20, weight="bold")
    ).grid(row=0, column=0, padx=22, pady=(20, 4), sticky="w")

    ctk.CTkLabel(win, text="Selecione a impressora e o número de cópias.",
                 text_color="gray").grid(row=1, column=0, padx=22, pady=(0, 14), sticky="w")

    ctk.CTkLabel(win, text="Impressora").grid(
        row=2, column=0, padx=22, pady=(4, 4), sticky="w"
    )
    selected = ctk.StringVar(value=default if default in printers else printers[0])
    combo = ctk.CTkOptionMenu(win, values=printers, variable=selected, width=420)
    combo.grid(row=3, column=0, padx=22, pady=(0, 12), sticky="ew")

    ctk.CTkLabel(win, text="Cópias").grid(
        row=4, column=0, padx=22, pady=(4, 4), sticky="w"
    )
    entry_copies = ctk.CTkEntry(win, width=100)
    entry_copies.insert(0, "1")
    entry_copies.grid(row=5, column=0, padx=22, sticky="w")

    btns = ctk.CTkFrame(win, fg_color="transparent")
    btns.grid(row=6, column=0, padx=22, pady=(24, 20), sticky="ew")
    btns.grid_columnconfigure((0, 1), weight=1)

    def do_print() -> None:
        try:
            copies = int(entry_copies.get())
            if copies < 1 or copies > 50:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Atenção", "Número de cópias inválido (1 a 50).", parent=win
            )
            return
        win.config(cursor="wait")
        win.update_idletasks()
        ok, msg = _print_windows(selected.get(), content, copies)
        win.config(cursor="")
        if ok:
            messagebox.showinfo("Impressão", msg, parent=win)
            win.destroy()
        else:
            messagebox.showerror("Impressão", msg, parent=win)

    ctk.CTkButton(
        btns, text="Cancelar", fg_color="gray", hover_color="#555", command=win.destroy
    ).grid(row=0, column=0, padx=4, sticky="ew")
    ctk.CTkButton(
        btns, text="Imprimir", fg_color="#1f6aa5", command=do_print
    ).grid(row=0, column=1, padx=4, sticky="ew")

    win.bind("<Return>", lambda _: do_print())
    win.bind("<Escape>", lambda _: win.destroy())

    # grab_set após a janela estar visível, evita erro em algumas versões do CTk
    win.after(120, lambda: (win.grab_set(), win.focus_force()))


# ---------- Linux / macOS ----------

def _show_unix_dialog(parent, content: str) -> None:
    import subprocess
    import tempfile
    try:
        result = subprocess.run(["lpstat", "-p"], capture_output=True, text=True)
        printers = [
            line.split()[1] for line in result.stdout.splitlines()
            if line.startswith("printer")
        ]
    except FileNotFoundError:
        messagebox.showerror("Impressão", "CUPS (lpstat) não encontrado.", parent=parent)
        return

    if not printers:
        messagebox.showwarning("Imprimir", "Nenhuma impressora encontrada.", parent=parent)
        return

    win = ctk.CTkToplevel(parent)
    win.title("Imprimir cupom")
    win.geometry("420x260")
    win.transient(parent)
    win.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(win, text="Imprimir cupom",
                 font=ctk.CTkFont(size=18, weight="bold")).grid(
        row=0, column=0, padx=20, pady=(20, 10), sticky="w"
    )
    ctk.CTkLabel(win, text="Impressora").grid(row=1, column=0, padx=20, sticky="w")
    sel = ctk.StringVar(value=printers[0])
    ctk.CTkOptionMenu(win, values=printers, variable=sel).grid(
        row=2, column=0, padx=20, pady=(0, 12), sticky="ew"
    )
    ctk.CTkLabel(win, text="Cópias").grid(row=3, column=0, padx=20, sticky="w")
    e = ctk.CTkEntry(win)
    e.insert(0, "1")
    e.grid(row=4, column=0, padx=20, sticky="w")

    def go():
        try:
            copies = int(e.get())
        except ValueError:
            messagebox.showwarning("Atenção", "Cópias inválido.", parent=win); return
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
        tmp.write(content); tmp.close()
        try:
            subprocess.run(["lp", "-d", sel.get(), "-n", str(copies), tmp.name], check=True)
            messagebox.showinfo("Impressão", "Enviado.", parent=win)
            win.destroy()
        except Exception as ex:
            messagebox.showerror("Impressão", str(ex), parent=win)

    bf = ctk.CTkFrame(win, fg_color="transparent")
    bf.grid(row=5, column=0, padx=20, pady=20, sticky="ew")
    bf.grid_columnconfigure((0, 1), weight=1)
    ctk.CTkButton(bf, text="Cancelar", fg_color="gray", command=win.destroy).grid(row=0, column=0, padx=4, sticky="ew")
    ctk.CTkButton(bf, text="Imprimir", command=go).grid(row=0, column=1, padx=4, sticky="ew")
