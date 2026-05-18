"""PDV Simples - Ponto de Venda em Python com CustomTkinter + SQLite."""

import customtkinter as ctk

import database
from ui.sale_screen import SaleScreen
from ui.products_screen import ProductsScreen
from ui.stock_screen import StockScreen
from ui.history_screen import HistoryScreen
from ui.report_screen import ReportScreen


APP_TITLE = "PDV Simples"
APP_VERSION = "1.0"


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title(f"{APP_TITLE} v{APP_VERSION}")
        self.geometry("1180x720")
        self.minsize(1024, 640)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_container()

        self.screens: dict[str, ctk.CTkFrame] = {}
        self._register_screens()
        self.show_screen("venda")

        # Atalho global F9 -> finaliza venda (delegado ao SaleScreen)
        self.bind("<F9>", self._on_f9)

    def _on_f9(self, _event) -> None:
        sale = self.screens.get("venda")
        if sale is not None and hasattr(sale, "_finalize"):
            sale._finalize()

    # ---------- Layout ----------

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=210, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsw")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(10, weight=1)

        ctk.CTkLabel(
            sidebar,
            text="PDV\nSIMPLES",
            font=ctk.CTkFont(size=22, weight="bold"),
            justify="center",
        ).grid(row=0, column=0, padx=20, pady=(28, 24))

        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        nav_items = [
            ("venda", "🛒  Venda"),
            ("produtos", "📦  Produtos"),
            ("estoque", "🗃️  Estoque"),
            ("historico", "📜  Histórico"),
            ("relatorio", "📊  Relatórios"),
        ]
        for i, (key, label) in enumerate(nav_items, start=1):
            btn = ctk.CTkButton(
                sidebar,
                text=label,
                anchor="w",
                height=44,
                corner_radius=8,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray80", "gray25"),
                font=ctk.CTkFont(size=14),
                command=lambda k=key: self.show_screen(k),
            )
            btn.grid(row=i, column=0, padx=14, pady=4, sticky="ew")
            self.nav_buttons[key] = btn

        ctk.CTkLabel(
            sidebar,
            text=f"v{APP_VERSION}",
            text_color="gray",
            font=ctk.CTkFont(size=11),
        ).grid(row=11, column=0, pady=10)

    def _build_container(self) -> None:
        self.container = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray95", "gray15"))
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

    def _register_screens(self) -> None:
        self.screens["venda"] = SaleScreen(self.container)
        self.screens["produtos"] = ProductsScreen(self.container)
        self.screens["estoque"] = StockScreen(self.container)
        self.screens["historico"] = HistoryScreen(self.container)
        self.screens["relatorio"] = ReportScreen(self.container)
        for screen in self.screens.values():
            screen.grid(row=0, column=0, sticky="nsew")
            screen.grid_remove()

    def show_screen(self, key: str) -> None:
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(fg_color=("gray80", "gray25"))
            else:
                btn.configure(fg_color="transparent")
        for k, screen in self.screens.items():
            if k == key:
                screen.grid()
                if hasattr(screen, "on_show"):
                    screen.on_show()
            else:
                screen.grid_remove()


def main() -> None:
    database.init_db()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
