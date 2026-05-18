"""Camada de acesso ao banco de dados SQLite do PDV."""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, date
from typing import Iterator, Optional


DB_FILENAME = "pdv.db"


def get_db_path() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, DB_FILENAME)


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                code        TEXT UNIQUE NOT NULL,
                name        TEXT NOT NULL,
                price       REAL NOT NULL CHECK (price >= 0),
                stock       INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
                created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS sales (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                datetime        TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                total           REAL NOT NULL,
                payment_method  TEXT NOT NULL,
                amount_paid     REAL NOT NULL,
                change_value    REAL NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS sale_items (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id     INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
                product_id  INTEGER NOT NULL REFERENCES products(id),
                code        TEXT NOT NULL,
                name        TEXT NOT NULL,
                quantity    REAL NOT NULL,
                unit_price  REAL NOT NULL,
                subtotal    REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS stock_movements (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id  INTEGER NOT NULL REFERENCES products(id),
                datetime    TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                type        TEXT NOT NULL,
                quantity    REAL NOT NULL,
                reason      TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_sale_items_sale ON sale_items(sale_id);
            CREATE INDEX IF NOT EXISTS idx_sales_date ON sales(datetime);
            CREATE INDEX IF NOT EXISTS idx_movements_product ON stock_movements(product_id);
            """
        )


# ---------- Produtos ----------

def list_products(search: str = "") -> list[sqlite3.Row]:
    sql = "SELECT * FROM products"
    params: tuple = ()
    if search:
        sql += " WHERE code LIKE ? OR name LIKE ?"
        like = f"%{search}%"
        params = (like, like)
    sql += " ORDER BY name"
    with connect() as conn:
        return conn.execute(sql, params).fetchall()


def get_product_by_code(code: str) -> Optional[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM products WHERE code = ?", (code,)
        ).fetchone()


def get_product_by_id(product_id: int) -> Optional[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()


def insert_product(code: str, name: str, price: float, stock: int) -> int:
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO products (code, name, price, stock) VALUES (?, ?, ?, ?)",
            (code, name, price, stock),
        )
        product_id = cur.lastrowid
        if stock > 0:
            conn.execute(
                "INSERT INTO stock_movements (product_id, type, quantity, reason)"
                " VALUES (?, 'entrada', ?, 'Cadastro inicial')",
                (product_id, stock),
            )
        return product_id


def update_product(product_id: int, code: str, name: str, price: float) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE products SET code = ?, name = ?, price = ? WHERE id = ?",
            (code, name, price, product_id),
        )


def delete_product(product_id: int) -> None:
    with connect() as conn:
        sold = conn.execute(
            "SELECT 1 FROM sale_items WHERE product_id = ? LIMIT 1", (product_id,)
        ).fetchone()
        if sold:
            raise ValueError(
                "Este produto já foi utilizado em vendas e não pode ser excluído."
            )
        conn.execute("DELETE FROM stock_movements WHERE product_id = ?", (product_id,))
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))


# ---------- Estoque ----------

def adjust_stock(product_id: int, quantity: float, movement_type: str, reason: str = "") -> None:
    """movement_type: 'entrada' | 'saida' | 'ajuste'."""
    with connect() as conn:
        row = conn.execute(
            "SELECT stock FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        if row is None:
            raise ValueError("Produto não encontrado.")
        current = row["stock"]
        if movement_type == "entrada":
            new_stock = current + quantity
        elif movement_type == "saida":
            if quantity > current:
                raise ValueError("Quantidade superior ao estoque disponível.")
            new_stock = current - quantity
        elif movement_type == "ajuste":
            new_stock = quantity
        else:
            raise ValueError("Tipo de movimento inválido.")
        conn.execute(
            "UPDATE products SET stock = ? WHERE id = ?", (new_stock, product_id)
        )
        conn.execute(
            "INSERT INTO stock_movements (product_id, type, quantity, reason)"
            " VALUES (?, ?, ?, ?)",
            (product_id, movement_type, quantity, reason),
        )


def list_stock_movements(product_id: Optional[int] = None, limit: int = 200) -> list[sqlite3.Row]:
    sql = (
        "SELECT m.*, p.code AS product_code, p.name AS product_name "
        "FROM stock_movements m JOIN products p ON p.id = m.product_id"
    )
    params: tuple = ()
    if product_id:
        sql += " WHERE m.product_id = ?"
        params = (product_id,)
    sql += " ORDER BY m.datetime DESC LIMIT ?"
    params = params + (limit,)
    with connect() as conn:
        return conn.execute(sql, params).fetchall()


# ---------- Vendas ----------

def create_sale(
    items: list[dict],
    payment_method: str,
    amount_paid: float,
) -> int:
    """items: [{product_id, code, name, quantity, unit_price}]."""
    if not items:
        raise ValueError("A venda precisa ter pelo menos um item.")

    total = round(sum(i["quantity"] * i["unit_price"] for i in items), 2)
    if amount_paid + 1e-6 < total:
        raise ValueError("Valor pago menor que o total da venda.")
    change = round(amount_paid - total, 2)

    with connect() as conn:
        # Validar estoque
        for it in items:
            row = conn.execute(
                "SELECT stock, name FROM products WHERE id = ?", (it["product_id"],)
            ).fetchone()
            if row is None:
                raise ValueError(f"Produto '{it['name']}' não encontrado.")
            if it["quantity"] > row["stock"]:
                raise ValueError(
                    f"Estoque insuficiente para '{row['name']}'. "
                    f"Disponível: {row['stock']}."
                )

        cur = conn.execute(
            "INSERT INTO sales (total, payment_method, amount_paid, change_value)"
            " VALUES (?, ?, ?, ?)",
            (total, payment_method, amount_paid, change),
        )
        sale_id = cur.lastrowid

        for it in items:
            subtotal = round(it["quantity"] * it["unit_price"], 2)
            conn.execute(
                "INSERT INTO sale_items "
                "(sale_id, product_id, code, name, quantity, unit_price, subtotal) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    sale_id,
                    it["product_id"],
                    it["code"],
                    it["name"],
                    it["quantity"],
                    it["unit_price"],
                    subtotal,
                ),
            )
            conn.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (it["quantity"], it["product_id"]),
            )
            conn.execute(
                "INSERT INTO stock_movements (product_id, type, quantity, reason)"
                " VALUES (?, 'saida', ?, ?)",
                (it["product_id"], it["quantity"], f"Venda #{sale_id}"),
            )

        return sale_id


def get_sale(sale_id: int) -> Optional[sqlite3.Row]:
    with connect() as conn:
        return conn.execute("SELECT * FROM sales WHERE id = ?", (sale_id,)).fetchone()


def get_sale_items(sale_id: int) -> list[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            "SELECT * FROM sale_items WHERE sale_id = ? ORDER BY id", (sale_id,)
        ).fetchall()


def list_sales(
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 500,
) -> list[sqlite3.Row]:
    sql = "SELECT * FROM sales WHERE 1=1"
    params: list = []
    if start:
        sql += " AND datetime >= ?"
        params.append(start + " 00:00:00")
    if end:
        sql += " AND datetime <= ?"
        params.append(end + " 23:59:59")
    sql += " ORDER BY datetime DESC LIMIT ?"
    params.append(limit)
    with connect() as conn:
        return conn.execute(sql, params).fetchall()


# ---------- Relatórios ----------

def report_summary(start: str, end: str) -> dict:
    with connect() as conn:
        totals = conn.execute(
            "SELECT COUNT(*) AS qtd, COALESCE(SUM(total), 0) AS total "
            "FROM sales WHERE datetime BETWEEN ? AND ?",
            (start + " 00:00:00", end + " 23:59:59"),
        ).fetchone()

        by_payment = conn.execute(
            "SELECT payment_method, COUNT(*) AS qtd, SUM(total) AS total "
            "FROM sales WHERE datetime BETWEEN ? AND ? "
            "GROUP BY payment_method ORDER BY total DESC",
            (start + " 00:00:00", end + " 23:59:59"),
        ).fetchall()

        top_products = conn.execute(
            "SELECT si.name, SUM(si.quantity) AS qtd, SUM(si.subtotal) AS total "
            "FROM sale_items si JOIN sales s ON s.id = si.sale_id "
            "WHERE s.datetime BETWEEN ? AND ? "
            "GROUP BY si.product_id ORDER BY qtd DESC LIMIT 10",
            (start + " 00:00:00", end + " 23:59:59"),
        ).fetchall()

    return {
        "qtd_vendas": totals["qtd"],
        "total": totals["total"] or 0.0,
        "por_pagamento": [dict(r) for r in by_payment],
        "top_produtos": [dict(r) for r in top_products],
    }


def today_str() -> str:
    return date.today().isoformat()
