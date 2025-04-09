import sqlite3
import os

from utils import DB_PATH
DB_FILE = DB_PATH


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            address TEXT
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL UNIQUE,
            date TEXT,
            customer_id INTEGER,
            total_amount TEXT,
            status TEXT DEFAULT 'Active',
            pdf_path TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS line_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            description TEXT,
            quantity INTEGER,
            unit_price TEXT,
            total TEXT,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id)
        )""")

        self.conn.commit()

    def save_invoice(self, invoice_data, line_items, pdf_path):
        cursor = self.conn.cursor()

        # Insert or find customer
        cursor.execute("""
            SELECT id FROM customers WHERE name = ? AND email = ?""",
            (invoice_data["Client Name"], invoice_data["Client Email"])
        )
        result = cursor.fetchone()
        if result:
            customer_id = result[0]
        else:
            cursor.execute("""
                INSERT INTO customers (name, email, address) VALUES (?, ?, ?)""",
                (
                    invoice_data["Client Name"],
                    invoice_data["Client Email"],
                    invoice_data["Client Address"]
                )
            )
            customer_id = cursor.lastrowid

        # Insert invoice
        cursor.execute("""
            INSERT OR REPLACE INTO invoices (
                invoice_number, date, customer_id, total_amount, pdf_path
            ) VALUES (?, ?, ?, ?, ?)""",
            (
                invoice_data["Invoice Number"],
                invoice_data["Date"],
                customer_id,
                invoice_data["Total Amount"],
                pdf_path
            )
        )
        invoice_id = cursor.lastrowid

        # Delete old line items (if any)
        cursor.execute("DELETE FROM line_items WHERE invoice_id = ?", (invoice_id,))

        # Insert line items
        for item in line_items:
            cursor.execute("""
                INSERT INTO line_items (invoice_id, description, quantity, unit_price, total)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    invoice_id,
                    item["Description"],
                    item["Quantity"],
                    item["Unit Price"],
                    item["Total"]
                )
            )

        self.conn.commit()

    def find_invoice(self, invoice_number):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT i.id, i.invoice_number, i.date, i.total_amount, i.status,
                c.name, c.email, c.address
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            WHERE i.invoice_number = ?
        """, (invoice_number,))
        result = cursor.fetchone()
        if not result:
            return None

        invoice = {
            "id": result[0],
            "Invoice Number": result[1],
            "Date": result[2],
            "Total Amount": result[3],
            "Status": result[4],
            "Client Name": result[5],
            "Client Email": result[6],
            "Client Address": result[7],
            "Line Items": []
        }

        cursor.execute("""
            SELECT description, quantity, unit_price, total
            FROM line_items WHERE invoice_id = ?
        """, (invoice["id"],))

        invoice["Line Items"] = [dict(zip(["Description", "Quantity", "Unit Price", "Total"], row)) for row in cursor.fetchall()]
        return invoice

    def void_invoice(self, invoice_number):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE invoices SET status = 'Voided' WHERE invoice_number = ?", (invoice_number,))
        self.conn.commit()
