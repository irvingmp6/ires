import sqlite3
from utils import DB_PATH

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            contact_email TEXT,
            street_address TEXT,
            primary_contact_name TEXT,
            secondary_contact_name TEXT,
            primary_contact_phone TEXT,
            secondary_contact_phone TEXT,
            payment_terms_code TEXT DEFAULT 'DUE ON RECEIPT'
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL UNIQUE,
            date TEXT,
            customer_id INTEGER,
            total_amount TEXT,
            status TEXT DEFAULT 'Active',
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS line_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            short_description TEXT,
            quantity INTEGER,
            unit_price TEXT,
            total TEXT,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id)
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS payment_terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_terms_code TEXT UNIQUE NOT NULL,
            short_description TEXT,
            full_verbiage TEXT NOT NULL
        );""")

        cursor.execute("""
        INSERT OR IGNORE INTO payment_terms (payment_terms_code, short_description, full_verbiage) VALUES
            ('DUE ON RECEIPT', 'Upon invoice delivery', 'Payment is due upon receipt of invoice.'),
            ('NET 7', 'Net 7 days', 'Payment is due within 7 days of the invoice date.'),
            ('NET 10', 'Net 10 days', 'Payment is due within 10 days of the invoice date.'),
            ('NET 15', 'Net 15 days', 'Payment is due within 15 days of the invoice date.'),
            ('NET 30', 'Net 30 days', 'Payment is due within 30 days of the invoice date.'),
            ('NET 45', 'Net 45 days', 'Payment is due within 45 days of the invoice date.'),
            ('NET 60', 'Net 60 days', 'Payment is due within 60 days of the invoice date.'),
            ('NET 90', 'Net 90 days', 'Payment is due within 90 days of the invoice date.'),
            ('EOM', 'End of Month', 'Payment is due at the end of the invoice month.'),
            ('NET EOM 30', 'Net 30 from EOM', 'Payment is due 30 days after the end of the month.'),
            ('COD', 'Cash on Delivery', 'Payment is due in full at the time of delivery.'),
            ('CIA', 'Cash in Advance', 'Full payment is required before service or delivery.'),
            ('PIA', 'Payment in Advance', 'Payment must be received prior to service or product delivery.'),
            ('CWO', 'Cash With Order', 'Payment must be made at the time of placing the order.'),
            ('MONTHLY', 'Monthly recurring', 'Payment is due monthly as per agreement.'),
            ('BI-MONTHLY', 'Twice a month', 'Payment is due every two weeks.'),
            ('QUARTERLY', 'Quarterly recurring', 'Payment is due every 3 months.'),
            ('SEMI-ANNUALLY', 'Twice a year', 'Payment is due every 6 months.'),
            ('ANNUALLY', 'Once a year', 'Payment is due yearly.'),
            ('2/10 NET 30', '2% discount if paid early', '2% discount if paid within 10 days, otherwise full amount due in 30 days.'),
            ('1/10 NET 30', '1% discount if paid early', '1% discount if paid within 10 days, otherwise full amount due in 30 days.'),
            ('NET 30 EOM', 'Net 30 from end of month', 'Payment is due 30 days after the end of the invoice month.'),
            ('NET 30 PROX', 'Net 30 from next month', 'Payment is due 30 days after the beginning of the month following invoice date.'),
            ('PREPAID', 'Fully prepaid', 'Full payment required in advance.'),
            ('STAGE PAYMENT', 'Installments', 'Payment made in agreed-upon milestones or stages.'),
            ('PROGRESS', 'Ongoing partial payments', 'Payments made as project progresses.'),
            ('CONSIGNMENT', 'Pay only on sale of goods', 'Goods are delivered without upfront payment; payment occurs only after goods are sold.');
        """)

        self.conn.commit()

    def get_all_clients(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, business_name, contact_email, street_address, primary_contact_name,
                   primary_contact_phone, secondary_contact_name, secondary_contact_phone,
                   payment_terms_code
            FROM customers ORDER BY business_name ASC
        """)
        return cursor.fetchall()

    def get_terms(self):
        cursor = self.conn.cursor()
        cursor.execute("""SELECT payment_terms_code FROM payment_terms ORDER BY payment_terms_code""")
        codes = [row[0] for row in cursor.fetchall()]
        codes.sort()
        return codes

    def update_client(self, client_id, business_name, contact_email, contact_address,
                      primary_contact_name, primary_contact_phone, 
                      secondary_contact_name, secondary_contact_phone, payment_terms_code):
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE customers
            SET business_name = ?, contact_email = ?, street_address = ?, 
                primary_contact_name = ?, primary_contact_phone = ?,
                secondary_contact_name = ?, secondary_contact_phone = ?,
                payment_terms_code = ?
            WHERE id = ?
        """, (business_name, contact_email, contact_address,
              primary_contact_name, primary_contact_phone,
              secondary_contact_name, secondary_contact_phone,
              payment_terms_code, client_id))
        self.conn.commit()

    def save_invoice(self, invoice_data, line_items):
        cursor = self.conn.cursor()

        # Insert or find customer
        cursor.execute("""
            SELECT id FROM customers WHERE business_name = ? AND street_address = ?""",
            (invoice_data["Business Name"], invoice_data["Contact Email"]))
        result = cursor.fetchone()
        if result:
            customer_id = result[0]
        else:
            cursor.execute("""
                INSERT INTO customers (business_name, contact_email, street_address) VALUES (?, ?, ?)""",
                (
                    invoice_data["Business Name"],
                    invoice_data["Contact Email"],
                    invoice_data["Street Address"]
                )
            )
            customer_id = cursor.lastrowid

        # Insert invoice
        cursor.execute("""
            INSERT OR REPLACE INTO invoices (
                invoice_number, date, customer_id, total_amount
            ) VALUES (?, ?, ?, ?)""",
            (
                invoice_data["Invoice Number"],
                invoice_data["Date"],
                customer_id,
                invoice_data["Total Amount"]
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
                c.business_name, c.contact_email, c.street_address
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
            "Business Name": result[5],
            "Contact Email": result[6],
            "Street Address": result[7],
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
