import sqlite3
from utils import DB_PATH
import json

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()

        # Enable foreign key support
        cursor.execute("PRAGMA foreign_keys = ON")

        # Create tables only if they don't exist (don't drop existing tables)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            primary_email TEXT,
            street_address TEXT,
            primary_contact_name TEXT,
            primary_contact_phone TEXT,
            secondary_contact_name TEXT,
            secondary_email TEXT,
            secondary_contact_phone TEXT,
            payment_terms_code TEXT DEFAULT 'DUE ON RECEIPT',
            date_created DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL UNIQUE,
            date TEXT,
            customer_id INTEGER,
            subtotal_amount TEXT,
            discount_type TEXT CHECK(discount_type IN ('NONE', 'PERCENTAGE', 'FIXED_AMOUNT')),
            discount_value TEXT,
            discount_description TEXT,
            total_amount TEXT,
            status TEXT DEFAULT 'Active' CHECK(
                status IN (
                    'Active',
                    'Void',
                    'Paid - Pending Reconciliation',
                    'Paid - Fully Reconciled'
                )
            ),
            notes TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS line_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            short_description TEXT,
            quantity INTEGER,
            unit_price TEXT,
            discount_type TEXT CHECK(discount_type IN ('NONE', 'PERCENTAGE', 'FIXED_AMOUNT', 'BULK')),
            discount_value TEXT,
            discount_description TEXT,
            total TEXT,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
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
            ('NET 07', 'Net 7 days', 'Payment is due within 7 days of the invoice date.'),
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

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoice_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            draft_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        self.conn.commit()

    def get_all_clients(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, business_name, primary_email, street_address, primary_contact_name,
                   primary_contact_phone, secondary_contact_name, secondary_email,
                   secondary_contact_phone, payment_terms_code
            FROM customers 
            ORDER BY date_created DESC, business_name ASC
        """)
        return cursor.fetchall()

    def get_all_payment_terms_codes(self):
        cursor = self.conn.cursor()
        cursor.execute("""SELECT payment_terms_code FROM payment_terms ORDER BY id ASC""")
        codes = [row[0] for row in cursor.fetchall()]
        codes.sort()
        return codes

    def get_all_payment_terms_full_verbiage(self):
        cursor = self.conn.cursor()
        cursor.execute("""SELECT payment_terms_code, full_verbiage FROM payment_terms ORDER BY payment_terms_code ASC""")
        ordered_dict = {}
        for row in cursor.fetchall():
            ordered_dict[row[0]] = row[1]
        return ordered_dict

    def update_client(self, client_id, business_name, primary_email, contact_address,
                      primary_contact_name, primary_contact_phone, 
                      secondary_contact_name, secondary_email,
                      secondary_contact_phone, payment_terms_code):
        cursor = self.conn.cursor()

        client_id = self.get_customer_id_by_email(primary_email)

        cursor.execute("""
            UPDATE customers
            SET business_name = ?, primary_email = ?, street_address = ?, 
                primary_contact_name = ?, primary_contact_phone = ?,
                secondary_contact_name = ?, secondary_email = ?,
                secondary_contact_phone = ?, payment_terms_code = ?
            WHERE id = ?
        """, (business_name, primary_email, contact_address,
              primary_contact_name, primary_contact_phone,
              secondary_contact_name, secondary_email,
              secondary_contact_phone, payment_terms_code, client_id))
        self.conn.commit()

    def get_customer_id_by_email(self, email):
        if not email:
            return None
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id FROM customers 
            WHERE primary_email = ? OR secondary_email = ?
        """, (email, email))
        result = cursor.fetchone()
        return result[0] if result else None

    def save_invoice_with_customer(self, invoice_data, line_items, customer_data=None):
        """Save invoice and optionally create a new customer in a single transaction.
        
        Args:
            invoice_data: Dictionary containing invoice details
            line_items: List of line items for the invoice
            customer_data: Optional dictionary containing customer details. If provided,
                         a new customer will be created before saving the invoice.
        """
        cursor = self.conn.cursor()
        
        try:
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")
            
            # Create customer if needed
            if customer_data:
                cursor.execute("""
                    INSERT INTO customers (
                        business_name, primary_email, street_address,
                        primary_contact_name, primary_contact_phone,
                        secondary_contact_name, secondary_email,
                        secondary_contact_phone, payment_terms_code,
                        date_created
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    customer_data['business_name'],
                    customer_data['primary_email'],
                    customer_data['street_address'],
                    customer_data['primary_contact_name'],
                    customer_data['primary_contact_phone'],
                    customer_data.get('secondary_contact_name', ''),
                    customer_data.get('secondary_email', ''),
                    customer_data.get('secondary_contact_phone', ''),
                    customer_data.get('payment_terms_code', 'NET30')
                ))
                invoice_data['customer_id'] = cursor.lastrowid
            
            # Insert invoice
            cursor.execute("""
                INSERT INTO invoices (
                    invoice_number, date, customer_id, 
                    subtotal_amount, discount_type, discount_value,
                    discount_description, total_amount, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_data['invoice_number'],
                invoice_data['date'],
                invoice_data['customer_id'],
                invoice_data['subtotal_amount'],
                invoice_data['discount_type'],
                invoice_data['discount_value'],
                invoice_data['discount_description'],
                invoice_data['total_amount'],
                invoice_data.get('status', 'Active'),  # Use provided status or default to 'Active'
                invoice_data.get('notes', '')  # Include notes field
            ))
            
            invoice_id = cursor.lastrowid

            # Insert line items (no need to delete old ones since this is a new invoice)
            for item in line_items:
                cursor.execute("""
                    INSERT INTO line_items (
                        invoice_id, short_description, quantity, 
                        unit_price, discount_type, discount_value,
                        discount_description, total
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    invoice_id,
                    item['description'],
                    item['quantity'],
                    item['unit_price'],
                    item['discount_type'],
                    item['discount_value'],
                    item['discount_description'],
                    item['total']
                ))
            
            # Commit transaction
            self.conn.commit()
            return invoice_id
            
        except Exception as e:
            # Rollback on error
            self.conn.rollback()
            raise e

    def find_invoice(self, invoice_number):
        """Find an invoice by its number and return all its details."""
        cursor = self.conn.cursor()
        
        try:
            # Get invoice details
            cursor.execute("""
                SELECT i.*, c.business_name, c.primary_email, c.street_address
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                WHERE i.invoice_number = ?
            """, (invoice_number,))
            
            invoice = cursor.fetchone()
            if not invoice:
                return None
                
            # Convert to dictionary
            invoice_dict = dict(invoice)
            
            # Get line items
            cursor.execute("""
                SELECT short_description as Description, 
                       quantity as Quantity,
                       unit_price as "Unit Price",
                       discount_type as "Discount Type",
                       discount_value as "Discount Value",
                       discount_description as "Discount Description",
                       total as Total
                FROM line_items 
                WHERE invoice_id = ?
            """, (invoice['id'],))
            
            line_items = [dict(row) for row in cursor.fetchall()]
            invoice_dict['Line Items'] = line_items
            
            # Ensure notes field exists
            if 'notes' not in invoice_dict:
                invoice_dict['notes'] = ''
            
            return invoice_dict
            
        except Exception as e:
            print(f"Error finding invoice: {e}")
            return None

    def view_invoice(self, invoice_number):
        """View an invoice by its number without modifying it."""
        cursor = self.conn.cursor()
        
        try:
            # Start read-only transaction
            cursor.execute("PRAGMA query_only = ON")
            cursor.execute("BEGIN TRANSACTION")
            
            cursor.execute("""
                SELECT i.*, c.business_name, c.primary_email, c.street_address
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                WHERE i.invoice_number = ?
            """, (invoice_number,))
            
            invoice = cursor.fetchone()
            if not invoice:
                cursor.execute("ROLLBACK")
                cursor.execute("PRAGMA query_only = OFF")
                return None
                
            # Convert to dictionary
            invoice_dict = dict(invoice)
            
            # Get line items
            cursor.execute("""
                SELECT short_description as Description, 
                       quantity as Quantity,
                       unit_price as "Unit Price",
                       discount_type as "Discount Type",
                       discount_value as "Discount Value",
                       discount_description as "Discount Description",
                       total as Total
                FROM line_items 
                WHERE invoice_id = ?
            """, (invoice['id'],))
            
            line_items = [dict(row) for row in cursor.fetchall()]
            invoice_dict['Line Items'] = line_items
            
            # Ensure notes field exists
            if 'notes' not in invoice_dict:
                invoice_dict['notes'] = ''
            
            cursor.execute("ROLLBACK")
            cursor.execute("PRAGMA query_only = OFF")
            return invoice_dict
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            cursor.execute("PRAGMA query_only = OFF")
            print(f"Error viewing invoice: {e}")
            return None

    def update_invoice_status(self, invoice_number, new_status):
        """Update the status of an invoice."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE invoices 
            SET status = ? 
            WHERE invoice_number = ?
        """, (new_status, invoice_number))
        self.conn.commit()

    def update_invoice_notes(self, invoice_number, notes):
        """Update the notes for an invoice."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE invoices 
            SET notes = ? 
            WHERE invoice_number = ?
        """, (notes, invoice_number))
        self.conn.commit()

    def get_invoice_notes(self, invoice_number):
        """Get the notes for an invoice."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT notes 
            FROM invoices 
            WHERE invoice_number = ?
        """, (invoice_number,))
        result = cursor.fetchone()
        return result[0] if result else ""

    def void_invoice(self, invoice_number):
        self.update_invoice_status(invoice_number, "Void")

    def get_client_term_code_by_email(self, email):
        client_id = self.get_customer_id_by_email(email)
        if not client_id:
            return None
        cursor = self.conn.cursor()
        
        cursor.execute("""SELECT payment_terms_code FROM customers WHERE id = ?""", (client_id,))
        return cursor.fetchone()[0]

    def get_invoices_by_client_id(self, client_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT i.invoice_number, i.date, i.total_amount, i.status
            FROM invoices i
            WHERE i.customer_id = ?
            ORDER BY i.date DESC
        """, (client_id,))
        return cursor.fetchall()

    def search_invoices(self, filters):
        """
        Search for invoices based on the provided filters
        filters: dict containing search criteria
        """
        query = """
            SELECT 
                i.invoice_number as "Invoice Number",
                i.date as "Date",
                c.business_name as "Business Name",
                i.total_amount as "Total Amount",
                i.status as "Status",
                i.date as "Last Modified"
            FROM invoices i
            JOIN customers c ON i.customer_id = c.id
            WHERE 1=1
        """
        params = []

        if filters['invoice_number']:
            query += " AND i.invoice_number LIKE ?"
            params.append(f"%{filters['invoice_number']}%")

        if filters['business_name']:
            query += " AND c.business_name LIKE ?"
            params.append(f"%{filters['business_name']}%")

        if filters['date_from']:
            query += " AND i.date >= ?"
            params.append(filters['date_from'])

        if filters['date_to']:
            query += " AND i.date <= ?"
            params.append(filters['date_to'])

        if filters['status']:
            query += " AND i.status = ?"
            params.append(filters['status'])

        if filters['amount_from']:
            try:
                amount = float(filters['amount_from'])
                query += " AND CAST(i.total_amount AS REAL) >= ?"
                params.append(amount)
            except ValueError:
                pass

        if filters['amount_to']:
            try:
                amount = float(filters['amount_to'])
                query += " AND CAST(i.total_amount AS REAL) <= ?"
                params.append(amount)
            except ValueError:
                pass

        query += " ORDER BY i.date DESC, i.invoice_number DESC"

        cursor = self.conn.cursor()
        cursor.row_factory = sqlite3.Row  # Set row factory for this cursor
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]  # Convert Row objects to dictionaries

    def create_new_client(self, client_data):
        """Create a new client and return their ID"""
        cursor = self.conn.cursor()
        
        # Check if client already exists
        cursor.execute("""
            SELECT id FROM customers 
            WHERE primary_email = ? OR secondary_email = ?
        """, (client_data['primary_email'], client_data['primary_email']))
        
        existing = cursor.fetchone()
        if existing:
            return existing[0]  # Return existing client ID
            
        # Insert new client
        cursor.execute("""
            INSERT INTO customers (
                business_name, primary_email, street_address,
                primary_contact_name, primary_contact_phone,
                secondary_contact_name, secondary_email,
                secondary_contact_phone, payment_terms_code,
                date_created
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            client_data['business_name'],
            client_data['primary_email'],
            client_data['street_address'],
            client_data['primary_contact_name'],
            client_data['primary_contact_phone'],
            client_data['secondary_contact_name'],
            client_data['secondary_email'],
            client_data['secondary_contact_phone'],
            client_data['payment_terms_code']
        ))
        
        self.conn.commit()
        return cursor.lastrowid

    def get_client_by_id(self, client_id):
        """Get client information by ID"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                business_name,
                primary_email,
                street_address,
                primary_contact_name,
                primary_contact_phone,
                secondary_contact_name,
                secondary_email,
                secondary_contact_phone,
                payment_terms_code
            FROM customers 
            WHERE id = ?
        """, (client_id,))
        
        row = cursor.fetchone()
        if row:
            return {
                'business_name': row[0],
                'primary_email': row[1],
                'street_address': row[2],
                'primary_contact_name': row[3],
                'primary_contact_phone': row[4],
                'secondary_contact_name': row[5],
                'secondary_email': row[6],
                'secondary_contact_phone': row[7],
                'payment_terms_code': row[8]
            }
        return None

    def save_invoice_draft(self, draft_data):
        """Save an invoice draft to the database"""
        cursor = self.conn.cursor()
        try:
            # Convert draft data to JSON for storage
            draft_json = json.dumps(draft_data)
            
            # Check if draft already exists
            cursor.execute("""
                SELECT id FROM invoice_drafts 
                WHERE invoice_number = ?
            """, (draft_data['invoice_number'],))
            
            existing_draft = cursor.fetchone()
            
            if existing_draft:
                # Update existing draft
                cursor.execute("""
                    UPDATE invoice_drafts 
                    SET draft_data = ?,
                        last_modified = CURRENT_TIMESTAMP
                    WHERE invoice_number = ?
                """, (draft_json, draft_data['invoice_number']))
            else:
                # Insert new draft
                cursor.execute("""
                    INSERT INTO invoice_drafts (
                        invoice_number,
                        draft_data,
                        created_at,
                        last_modified
                    ) VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (draft_data['invoice_number'], draft_json))
            
            self.conn.commit()
            
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Failed to save draft: {str(e)}")
        finally:
            cursor.close()

    def get_invoice_drafts(self):
        """Get all draft invoices"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT invoice_number, draft_data, created_at, last_modified 
                FROM invoice_drafts 
                ORDER BY last_modified DESC
            """)
            
            drafts = []
            for row in cursor.fetchall():
                draft_data = json.loads(row[1])
                drafts.append({
                    'invoice_number': row[0],
                    'date': draft_data.get('date', ''),
                    'business_name': draft_data.get('business_name', ''),
                    'contact_name': draft_data.get('contact_name', ''),
                    'last_modified': row[3]
                })
            
            return drafts
            
        except Exception as e:
            raise Exception(f"Failed to get drafts: {str(e)}")
        finally:
            cursor.close()

    def get_invoice_draft(self, invoice_number):
        """Get a specific draft invoice"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT draft_data 
                FROM invoice_drafts 
                WHERE invoice_number = ?
            """, (invoice_number,))
            
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None
            
        except Exception as e:
            raise Exception(f"Failed to get draft: {str(e)}")
        finally:
            cursor.close()

    def delete_invoice_draft(self, invoice_number):
        """Delete a draft invoice"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                DELETE FROM invoice_drafts 
                WHERE invoice_number = ?
            """, (invoice_number,))
            
            self.conn.commit()
            
        except Exception as e:
            self.conn.rollback()
            raise Exception(f"Failed to delete draft: {str(e)}")
        finally:
            cursor.close()

    def invoice_number_exists(self, invoice_number):
        """Check if an invoice number already exists in finalized invoices.
        
        Args:
            invoice_number: The invoice number to check
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM invoices 
                WHERE invoice_number = ?
            """, (invoice_number,))
            
            return cursor.fetchone()[0] > 0
            
        except Exception as e:
            raise Exception(f"Failed to check invoice number: {str(e)}")
        finally:
            cursor.close()

    def find_clients_by_email(self, email):
        """Find all clients that match the given email in either primary or secondary email fields"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, business_name, primary_email, street_address,
                   primary_contact_name, primary_contact_phone,
                   secondary_contact_name, secondary_email,
                   secondary_contact_phone, payment_terms_code
            FROM customers 
            WHERE primary_email LIKE ? OR secondary_email LIKE ?
            ORDER BY business_name ASC
        """, (f"%{email}%", f"%{email}%"))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'business_name': row[1],
                'primary_email': row[2],
                'street_address': row[3],
                'primary_contact_name': row[4],
                'primary_contact_phone': row[5],
                'secondary_contact_name': row[6],
                'secondary_email': row[7],
                'secondary_contact_phone': row[8],
                'payment_terms_code': row[9]
            })
        return results