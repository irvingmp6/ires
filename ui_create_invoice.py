import json
import os
import sys
import decimal
from decimal import Decimal

from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QTextEdit, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QMessageBox,
    QDateEdit, QSpinBox, QDoubleSpinBox, QFileDialog, QComboBox, QGroupBox, 
    QFormLayout, QSizePolicy, QDialog, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QDate, QDateTime, QTimer
from PyQt6.QtGui import QFocusEvent

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from database import Database

from utils import PDF_DIR, JSON_DIR



class CreateInvoiceWidget(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.db = Database()
        self._cached_data = None  # Initialize cache variable
        self.selected_client_id = None
        self.invoice_fields = {}
        self.previous_widget = None  # Store the widget we came from
        
        # Setup auto-save timer
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.setInterval(5 * 60 * 1000)  # 5 minutes in milliseconds
        
        # Status label for auto-save
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray; font-size: 10px;")
        
        # Timer for clearing status message
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.clear_status)
        self.status_timer.setSingleShot(True)
        
        self.init_ui()
        self.generate_invoice_number()  # Generate initial invoice number
        self.auto_save_timer.start()

    def set_previous_widget(self, widget):
        """Set the widget to return to when back button is pressed"""
        self.previous_widget = widget
        # Update back button tooltip based on where we came from
        back_tooltip = "Return to "
        if widget == self.main_window.find_invoice_page:
            back_tooltip += "invoice management"
        elif widget == self.main_window.view_existing_client_page:
            back_tooltip += "client manager"
        elif widget == self.main_window.select_client_type_page:
            back_tooltip += "client type selection"
        else:
            back_tooltip += "previous screen"
        
        # Find and update the back button tooltip
        for i in range(self.layout().count()):
            item = self.layout().itemAt(i)
            if isinstance(item, QHBoxLayout):  # This should be our button layout
                for j in range(item.count()):
                    widget = item.itemAt(j).widget()
                    if isinstance(widget, QPushButton) and widget.text() == "← Back":
                        widget.setToolTip(back_tooltip)
                        break
                break

    # Helper method for uniform field rows
    def create_form_row(self, label_text, widget):
        label = QLabel(label_text)
        label.setFixedWidth(120)  # Uniform label width (optional)

        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        # Expand all the way
        container_layout.addWidget(widget, 15)
        # container_layout.addStretch(1)

        row = QHBoxLayout()
        row.addWidget(label)
        row.addWidget(container)
        return row

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("📜 Create New Invoice")
        title.setProperty("title", True)
        layout.addWidget(title)

        # Client Details Section
        invoice_details = QGroupBox()
        invoice_layout = QVBoxLayout()

        # Two-column section
        two_column_layout = QHBoxLayout()

        # Column 1
        column1_layout = QVBoxLayout()
        self.invoice_fields = {}
        self.invoice_fields["Invoice Number"] = QLineEdit()
        self.invoice_fields["Invoice Number"].setPlaceholderText("Enter invoice number")

        # Invoice number row (with regenerate button)
        invoice_number_widget = QWidget()
        invoice_number_layout = QHBoxLayout(invoice_number_widget)
        invoice_number_layout.setContentsMargins(0, 0, 0, 0)
        invoice_number_layout.addWidget(self.invoice_fields["Invoice Number"], 8)

        regenerate_btn = QPushButton("🔄 Regenerate Number")
        regenerate_btn.setToolTip("Generate a new invoice number")
        regenerate_btn.clicked.connect(self.generate_invoice_number)
        invoice_number_layout.addWidget(regenerate_btn, 2)
        column1_layout.addLayout(self.create_form_row("Invoice Number:", invoice_number_widget))

        self.client_info = {}
        self.client_info["Business Name"] = QLineEdit()
        column1_layout.addLayout(self.create_form_row("Business Name:", self.client_info["Business Name"]))

        self.client_info["Contact Email"] = QLineEdit()
        self.client_info["Contact Email"].textChanged.connect(self.handle_client_email_change)
        column1_layout.addLayout(self.create_form_row("Contact Email:", self.client_info["Contact Email"]))

        self.client_info["Street Address"] = QTextEdit()
        self.client_info["Street Address"].setMaximumHeight(60)
        column1_layout.addLayout(self.create_form_row("Street Address:", self.client_info["Street Address"]))


        # Column 2
        column2_layout = QVBoxLayout()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        column2_layout.addLayout(self.create_form_row("Date:", self.date_edit))

        self.client_info["Contact Name"] = QLineEdit()
        column2_layout.addLayout(self.create_form_row("Contact Name:", self.client_info["Contact Name"]))

        self.client_info["Phone Number"] = QLineEdit()
        column2_layout.addLayout(self.create_form_row("Phone Number:", self.client_info["Phone Number"]))


        self.payment_terms_dropdown = QComboBox()
        self.payment_terms_dropdown.addItems(self.db.get_all_payment_terms_codes())
        self.payment_terms_dropdown.setCurrentText("DUE ON RECEIPT")
        column2_layout.addLayout(self.create_form_row("Payment Terms:", self.payment_terms_dropdown))

        self.term_description = QLabel()
        self.term_description.setWordWrap(True)
        self.term_description.setStyleSheet("color: gray; font-style: italic;")
        column2_layout.addLayout(self.create_form_row("", self.term_description))
        self.update_term_description()
        self.payment_terms_dropdown.currentTextChanged.connect(self.update_term_description)

        # Add columns to two-column layout
        two_column_layout.addLayout(column1_layout)
        two_column_layout.addLayout(column2_layout)
        invoice_layout.addLayout(two_column_layout)


        invoice_details.setLayout(invoice_layout)
        layout.addWidget(invoice_details)

        # Line Items Section
        layout.addWidget(self.init_line_item_section())

        # Totals Section
        layout.addWidget(self.init_totals_section())

        # Job and Notes Section
        job_notes_layout = QVBoxLayout()
        notes_group = QGroupBox("For Internal Use")
        notes_layout = QVBoxLayout()
        self.notes_text = QTextEdit()
        self.notes_text.setPlaceholderText('Add any notes about this invoice. Example: "Customer will pay with Zelle"')
        self.notes_text.setMaximumHeight(40)
        notes_layout.addWidget(self.notes_text)
        notes_group.setLayout(notes_layout)
        job_notes_layout.addWidget(notes_group)
        layout.addLayout(job_notes_layout)

        # Action Buttons
        button_layout = QHBoxLayout()
        clear_btn = QPushButton("🗑️ Clear Form")
        clear_btn.clicked.connect(self.confirm_clear_form)
        clear_btn.setToolTip("Clear all fields and start over")

        save_draft_btn = QPushButton("💾 Save Draft")
        save_draft_btn.clicked.connect(self.save_draft)
        save_draft_btn.setToolTip("Save your progress to continue later without creating the invoice")

        preview_btn = QPushButton("👁️ Preview PDF")
        preview_btn.clicked.connect(self.create_pdf)
        preview_btn.setToolTip("Generate a PDF preview without saving the invoice")

        create_btn = QPushButton("✅ Create Invoice")
        create_btn.clicked.connect(self.save_invoice)
        create_btn.setToolTip("Save the invoice and generate the final PDF")

        back_btn = QPushButton("\u2190 Back")
        back_btn.clicked.connect(self.go_back)
        back_btn.setToolTip("Return to invoice management")

        button_layout.addWidget(clear_btn)
        button_layout.addWidget(save_draft_btn)
        button_layout.addWidget(preview_btn)
        button_layout.addWidget(create_btn)
        button_layout.addWidget(back_btn)

        layout.addLayout(button_layout)
        layout.addWidget(self.status_label)



    def save_invoice(self):
        # Validate required fields
        if not self.validate_fields():
            return

        try:
            # Get invoice details
            invoice_data = {
                'invoice_number': self.invoice_fields["Invoice Number"].text(),
                'date': self.date_edit.date().toString("yyyy-MM-dd"),
                'customer_id': self.selected_client_id,
                'subtotal_amount': self.subtotal_label.text().replace('$', '').strip(),
                'discount_type': self.discount_type.currentText(),
                'discount_value': self.discount_value.text().strip(),
                'discount_description': self.discount_description.text().strip(),
                'sales_tax_amount': self.sales_tax_amount_label.text().replace('$', '').strip(),
                'total_amount': self.total_label.text().replace('$', '').strip(),
                'status': 'Active',  # Use Active status for new invoices
                'job': self.job_text.toPlainText().strip(),
                'notes': self.notes_text.toPlainText().strip()
            }

            # Get line items
            line_items = []
            for row in range(self.line_items_table.rowCount()):
                if not self.line_items_table.item(row, 0):  # Skip empty rows
                    continue
                    
                line_item = {
                    'description': self.line_items_table.item(row, 0).text(),
                    'quantity': self.line_items_table.cellWidget(row, 1).value(),
                    'unit_price': self.line_items_table.cellWidget(row, 2).text().strip(),
                    'discount_type': self.line_items_table.cellWidget(row, 3).currentText(),
                    'discount_value': self.line_items_table.cellWidget(row, 4).text().strip(),
                    'discount_description': self.line_items_table.item(row, 5).text() if self.line_items_table.item(row, 5) else '',
                    'total': self.line_items_table.item(row, 6).text().replace('$', '').strip()
                }
                line_items.append(line_item)

            # Check if we need to create a new customer
            customer_data = None
            email = self.client_info["Contact Email"].text().strip()
            
            if not self.selected_client_id:
                # Double check if customer exists
                client_id = self.db.get_customer_id_by_email(email)
                if client_id:
                    self.selected_client_id = client_id
                    invoice_data['customer_id'] = client_id
                else:
                    # Prepare customer data for creation
                    customer_data = {
                        'business_name': self.client_info["Business Name"].text().strip(),
                        'primary_email': email,
                        'street_address': self.client_info["Street Address"].toPlainText().strip(),
                        'primary_contact_name': self.client_info["Contact Name"].text().strip(),
                        'primary_contact_phone': self.client_info["Phone Number"].text().strip(),
                        'payment_terms_code': self.payment_terms_dropdown.currentText()
                    }

            # Save everything in a single transaction
            invoice_id = self.db.save_invoice_with_customer(invoice_data, line_items, customer_data)
            
            if not invoice_id:
                raise Exception("Failed to save invoice - no invoice ID returned")
            
            # Ask if user wants to generate PDF
            reply = QMessageBox.question(
                self,
                "Generate PDF",
                f"Invoice {invoice_data['invoice_number']} has been created. Generate PDF now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Get save location
                filename, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save Invoice PDF",
                    os.path.join(PDF_DIR, f"{invoice_data['invoice_number']}.pdf"),
                    "PDF Files (*.pdf)"
                )
                
                if filename:  # User didn't cancel
                    try:
                        # Create the PDF
                        self.create_pdf_at_path(filename)
                        
                        # Ask if user wants to open the PDF
                        open_reply = QMessageBox.question(
                            self,
                            "Success",
                            f"PDF has been created. Open now?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                        )
                        
                        if open_reply == QMessageBox.StandardButton.Yes:
                            self.open_pdf_file(filename)
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to create PDF: {str(e)}")
            
            # # Clear the form and generate new invoice number for next invoice
            # self.clear_fields()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save invoice: {str(e)}")
            return None

    def create_pdf_at_path(self, filename):
        """Create PDF at the specified path"""
        # Create PDF
        c = canvas.Canvas(filename, pagesize=LETTER)
        width, height = LETTER

        # Add logo if available
        if hasattr(self.main_window, 'settings') and 'logo_path' in self.main_window.settings:
            logo_path = self.main_window.settings['logo_path']
            if os.path.exists(logo_path):
                c.drawImage(logo_path, width - 200, height - 60, width=150, preserveAspectRatio=True)

        # Title
        c.setFont("Helvetica-Bold", 24)
        c.drawString(50, height - 50, "INVOICE")

        # Invoice details
        y = height - 100
        c.setFont("Helvetica-Bold", 12)
        for label, value in [
            ("Invoice Number", self.invoice_fields["Invoice Number"].text()),
            ("Date", self.date_edit.date().toString("yyyy-MM-dd")),
            ("Business Name", self.client_info["Business Name"].text()),
            ("Contact Email", self.client_info["Contact Email"].text()),
            ("Street Address", self.client_info["Street Address"].toPlainText()),
        ]:
            c.drawString(50, y, f"{label}:")
            c.setFont("Helvetica", 12)
            
            # Handle multiline text (like address)
            if label == "Street Address":
                for line in value.split('\n'):
                    y -= 15
                    c.drawString(200, y, line.strip())
            else:
                c.drawString(200, y, value)
            
            y -= 20
            c.setFont("Helvetica-Bold", 12)

        # Add payment terms
        payment_term = self.payment_terms_dropdown.currentText()
        if payment_term:
            y -= 10
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "Payment Terms:")
            y -= 20
            c.setFont("Helvetica", 12)
            term_description = self.db.get_all_payment_terms_full_verbiage().get(payment_term, payment_term)
            c.drawString(200, y, term_description)
            y -= 20

        # Add job if it exists
        job = self.job_text.toPlainText().strip()
        if job:
            y -= 10
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "Job:")
            y -= 20
            c.setFont("Helvetica", 11)
            # Split job into lines and draw each line
            job_lines = job.split('\n')
            for line in job_lines:
                if y < 100:  # Check if we need a new page
                    c.showPage()
                    y = height - 50
                c.drawString(50, y, line.strip())
                y -= 15

        # Add notes if they exist
        notes = self.notes_text.toPlainText().strip()
        if notes:
            y -= 10
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y, "Notes:")
            y -= 20
            c.setFont("Helvetica", 11)
            # Split notes into lines and draw each line
            notes_lines = notes.split('\n')
            for line in notes_lines:
                if y < 100:  # Check if we need a new page
                    c.showPage()
                    y = height - 50
                c.drawString(50, y, line.strip())
                y -= 15

        # Line items
        y -= 20
        c.drawString(50, y, "Line Items:")
        y -= 30

        # Table header
        c.setFont("Helvetica-Bold", 10)
        columns = [
            (50, "Description"),
            (300, "Quantity"),
            (350, "Unit Price"),
            (400, "Discount"),
            (500, "Total")
        ]
        for x, label in columns:
            c.drawString(x, y, label)

        # Table content
        y -= 20
        c.setFont("Helvetica", 10)
        for row in range(self.line_items_table.rowCount()):
            if y < 100:  # Start new page if near bottom
                c.showPage()
                y = height - 50
                # Redraw header
                c.setFont("Helvetica-Bold", 10)
                for x, label in columns:
                    c.drawString(x, y, label)
                y -= 20
                c.setFont("Helvetica", 10)

            # Get line item data
            desc = self.line_items_table.item(row, 0).text()
            qty = str(self.line_items_table.cellWidget(row, 1).value())
            unit_price = self.format_currency(self.line_items_table.cellWidget(row, 2).text())
            
            # Format discount info
            discount_type = self.line_items_table.cellWidget(row, 3).currentText()
            discount_value = self.line_items_table.cellWidget(row, 4).text()
            if discount_type != "NONE" and discount_value:
                if discount_type == "PERCENTAGE":
                    discount_text = f"{discount_value}%"
                elif discount_type == "FIXED_AMOUNT":
                    discount_text = self.format_currency(discount_value)
                else:
                    discount_text = "NONE"
            else:
                discount_text = "NONE"
            
            total = self.line_items_table.item(row, 6).text()

            # Draw line item
            c.drawString(50, y, desc[:40] + "..." if len(desc) > 40 else desc)
            c.drawString(300, y, qty)
            c.drawString(350, y, unit_price)
            c.drawString(400, y, discount_text)
            c.drawString(500, y, total)
            y -= 15

        # Totals section
        y -= 20
        c.setFont("Helvetica-Bold", 12)
        c.drawString(350, y, "Subtotal:")
        c.drawString(500, y, self.subtotal_label.text())
        
        y -= 20
        if self.discount_type.currentText() != "NONE":
            c.drawString(350, y, "Discount:")
            c.drawString(500, y, self.discount_amount_label.text())
            y -= 20
        
        # Sales Tax
        if self.sales_tax_rate.text().strip():
            c.drawString(350, y, "Sales Tax:")
            c.drawString(500, y, self.sales_tax_amount_label.text())
            y -= 20
        
        c.drawString(350, y, "Final Total:")
        c.drawString(500, y, self.total_label.text())

        c.save()
        QMessageBox.information(self, "Success", f"PDF saved to:\n{filename}")
        
    def open_pdf_file(self, filepath):
        """Open a PDF file using the system's default PDF viewer"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(filepath)
            else:  # macOS and Linux
                import subprocess
                subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', filepath])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open PDF: {str(e)}")

    def update_term_description(self):
        term_code = self.payment_terms_dropdown.currentText()
        term_description = self.db.get_all_payment_terms_full_verbiage().get(term_code, '')
        if term_description:
            self.term_description.setText(term_description)
        else:
            self.term_description.clear()
    
    def load_client_term(self, email_field):
        email = email_field.text()
        saved_term = self.db.get_client_term_code_by_email(email)
        if saved_term:
            self.payment_terms_dropdown.setCurrentText(saved_term)
            self.update_term_description()
        else:
            self.payment_terms_dropdown.setCurrentText("DUE ON RECEIPT") # Default to "DUE ON RECEIPT"
            self.update_term_description()
    
    def generate_invoice_number(self):
        """Generate an invoice number in the format INV-YYYYMMDD-HHMMSS"""
        current_datetime = QDateTime.currentDateTime()
        date_part = current_datetime.toString("yyyyMMdd")
        time_part = current_datetime.toString("hhmmss")
        invoice_number = f"INV-{date_part}-{time_part}"
        self.invoice_fields["Invoice Number"].setText(invoice_number)
    
    def init_line_item_section(self):
        group = QGroupBox()
        layout = QVBoxLayout()

        job_layout = QVBoxLayout()
        self.job_text = QTextEdit()
        self.job_text.setPlaceholderText('Add a Job Description. Example: "Weather damage repair"')
        self.job_text.setMaximumHeight(40)
        job_layout.addWidget(self.job_text)
        layout.addLayout(job_layout)

        # Table for line items
        self.line_items_table = QTableWidget(0, 7)  # Added 2 columns for discount
        self.line_items_table.setHorizontalHeaderLabels([
            "Description", "Quantity", "Unit Price", 
            "Discount Type", "Discount Value", "Discount Description",
            "Total"
        ])
        
        # Set column widths
        self.line_items_table.setColumnWidth(0, 250)  # Description
        self.line_items_table.setColumnWidth(1, 80)   # Quantity
        self.line_items_table.setColumnWidth(2, 100)  # Unit Price
        self.line_items_table.setColumnWidth(3, 120)  # Discount Type
        self.line_items_table.setColumnWidth(4, 100)  # Discount Value
        self.line_items_table.setColumnWidth(5, 150)  # Discount Description
        self.line_items_table.setColumnWidth(6, 100)  # Total

        # Enable row selection
        self.line_items_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.line_items_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        # Buttons layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)  # Add spacing between buttons
        
        # Add line item button
        add_btn = QPushButton("➕ Add Line Item")
        add_btn.setMinimumWidth(200)  # Set minimum width
        add_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Make button expand horizontally
        add_btn.clicked.connect(self.add_line_item)
        button_layout.addWidget(add_btn)

        # Remove line item button
        remove_btn = QPushButton("➖ Remove Selected Item")
        remove_btn.setMinimumWidth(200)  # Set minimum width
        remove_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)  # Make button expand horizontally
        remove_btn.clicked.connect(self.remove_line_item)
        button_layout.addWidget(remove_btn)

        layout.addWidget(self.line_items_table)
        layout.addLayout(button_layout)
        group.setLayout(layout)
        return group

    def remove_line_item(self):
        current_row = self.line_items_table.currentRow()
        if current_row >= 0:
            self.line_items_table.removeRow(current_row)
            self.update_totals()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a line item to remove.")

    def init_totals_section(self):
        group = QGroupBox()
        layout = QFormLayout()

        # Subtotal (before any discounts)
        self.subtotal_label = QLabel("$0.00")
        layout.addRow("Subtotal:", self.subtotal_label)

        # Invoice-level discount
        discount_layout = QHBoxLayout()
        self.discount_type = QComboBox()
        self.discount_type.addItems(["NONE", "PERCENTAGE", "FIXED_AMOUNT"])
        self.discount_type.currentTextChanged.connect(self.update_totals)
        
        self.discount_value = QLineEdit()
        self.discount_value.setPlaceholderText("Enter discount")
        self.discount_value.textChanged.connect(self.update_totals)
        
        self.discount_description = QLineEdit()
        self.discount_description.setPlaceholderText("Discount reason (optional)")
        
        discount_layout.addWidget(self.discount_type)
        discount_layout.addWidget(self.discount_value)
        discount_layout.addWidget(self.discount_description)
        layout.addRow("Invoice Discount:", discount_layout)

        # Discount amount
        self.discount_amount_label = QLabel("$0.00")
        layout.addRow("Discount Amount:", self.discount_amount_label)

        # Sales Tax
        sales_tax_layout = QHBoxLayout()
        self.sales_tax_rate = QLineEdit()
        self.sales_tax_rate.setPlaceholderText("0.00")
        self.sales_tax_rate.textChanged.connect(self.update_totals)
        
        self.sales_tax_amount_label = QLabel("$0.00")
        
        sales_tax_layout.addWidget(self.sales_tax_rate)
        sales_tax_layout.addWidget(QLabel("%"))
        sales_tax_layout.addWidget(self.sales_tax_amount_label)
        layout.addRow("Sales Tax:", sales_tax_layout)

        # Final total
        self.total_label = QLabel("$0.00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addRow("Final Total:", self.total_label)

        group.setLayout(layout)
        return group

    def format_currency(self, amount):
        """Format a number as currency with thousand separators"""
        try:
            # Handle various input types
            if isinstance(amount, str):
                # Remove any existing formatting
                amount = amount.replace("$", "").replace(",", "")
            
            # Convert to Decimal for precise calculation
            value = Decimal(str(amount))
            
            # Ensure non-negative
            value = max(value, Decimal("0.00"))
            
            return "${:,.2f}".format(value)
        except (ValueError, decimal.InvalidOperation):
            return "$0.00"

    def update_totals(self):
        """Calculate and update all totals with proper formatting"""
        subtotal = Decimal("0.00")
        
        # Calculate line item totals and subtotal
        for row in range(self.line_items_table.rowCount()):
            if not self.line_items_table.item(row, 0):  # Skip empty rows
                continue
                
            try:
                qty = Decimal(str(self.line_items_table.cellWidget(row, 1).value()))
                
                # Validate unit price
                price_text = self.line_items_table.cellWidget(row, 2).text().strip()
                if not price_text:  # Empty price
                    unit_price = Decimal("0.00")
                else:
                    try:
                        # Remove any currency symbols and commas
                        price_text = price_text.replace("$", "").replace(",", "")
                        unit_price = Decimal(price_text)
                    except (ValueError, decimal.InvalidOperation):
                        QMessageBox.warning(
                            self,
                            "Invalid Price",
                            f"Invalid price format in row {row + 1}. Please enter a valid number.\nExample: 123.45"
                        )
                        self.line_items_table.cellWidget(row, 2).setText("0.00")
                        unit_price = Decimal("0.00")
                
                # Calculate line item total before discount
                line_total = qty * unit_price
                
                # Apply line item discount
                discount_type = self.line_items_table.cellWidget(row, 3).currentText()
                discount_value_text = self.line_items_table.cellWidget(row, 4).text().strip()
                
                if discount_type != "NONE" and discount_value_text:
                    try:
                        if discount_type == "PERCENTAGE":
                            # Remove % symbol if present
                            discount_value_text = discount_value_text.rstrip("%")
                            discount_value = Decimal(discount_value_text)
                            if discount_value < 0 or discount_value > 100:
                                raise ValueError("Percentage must be between 0 and 100")
                            discount = line_total * (discount_value / Decimal("100"))
                            line_total -= discount
                        elif discount_type == "FIXED_AMOUNT":
                            # Remove currency symbols and commas
                            discount_value_text = discount_value_text.replace("$", "").replace(",", "")
                            discount = Decimal(discount_value_text)
                            if discount < 0:
                                raise ValueError("Discount amount cannot be negative")
                            line_total -= discount

                    except (ValueError, decimal.InvalidOperation) as e:
                        error_msg = str(e) if str(e) != "decimal.InvalidOperation" else "Invalid number format"
                        QMessageBox.warning(
                            self,
                            "Invalid Discount",
                            f"Invalid discount in row {row + 1}: {error_msg}\n\n"
                            "Valid formats:\n"
                            "- Percentage: Enter a number between 0-100\n"
                            "- Fixed Amount: Enter a valid number"
                        )
                        self.line_items_table.cellWidget(row, 4).setText("")
                
                # Update line total display with formatting
                self.line_items_table.item(row, 6).setText(self.format_currency(line_total))
                subtotal += line_total
                
            except (ValueError, decimal.InvalidOperation, AttributeError) as e:
                continue
        
        # Update subtotal display
        self.subtotal_label.setText(self.format_currency(subtotal))
        
        # Calculate invoice-level discount
        discount_amount = Decimal("0.00")
        if self.discount_type.currentText() == "PERCENTAGE":
            try:
                discount_text = self.discount_value.text().strip().rstrip("%")
                if discount_text:
                    percentage = Decimal(discount_text)
                    if percentage < 0 or percentage > 100:
                        raise ValueError("Percentage must be between 0 and 100")
                    discount_amount = subtotal * (percentage / Decimal("100"))
            except (ValueError, decimal.InvalidOperation):
                QMessageBox.warning(
                    self,
                    "Invalid Discount",
                    "Invalid percentage format. Please enter a number between 0-100.\nExample: 25 for 25%"
                )
                self.discount_value.setText("")
        elif self.discount_type.currentText() == "FIXED_AMOUNT":
            try:
                discount_text = self.discount_value.text().strip()
                if discount_text:
                    # Remove currency symbols and commas
                    discount_text = discount_text.replace("$", "").replace(",", "")
                    discount_amount = Decimal(discount_text)
                    if discount_amount < 0:
                        raise ValueError("Discount amount cannot be negative")
                    if discount_amount > subtotal:
                        raise ValueError("Discount cannot be greater than subtotal")
            except (ValueError, decimal.InvalidOperation) as e:
                error_msg = str(e) if "Discount" in str(e) else "Invalid number format"
                QMessageBox.warning(
                    self,
                    "Invalid Discount",
                    f"{error_msg}\nPlease enter a valid amount.\nExample: 123.45"
                )
                self.discount_value.setText("")
        
        # Update discount amount display
        self.discount_amount_label.setText(self.format_currency(discount_amount))
        
        # Calculate sales tax
        sales_tax_amount = Decimal("0.00")
        try:
            sales_tax_rate_text = self.sales_tax_rate.text().strip()
            if sales_tax_rate_text:
                sales_tax_rate = Decimal(sales_tax_rate_text)
                if sales_tax_rate < 0:
                    raise ValueError("Sales tax rate cannot be negative")
                # Calculate sales tax on subtotal after discount
                subtotal_after_discount = max(subtotal - discount_amount, Decimal("0.00"))
                sales_tax_amount = subtotal_after_discount * (sales_tax_rate / Decimal("100"))
        except (ValueError, decimal.InvalidOperation):
            # If invalid, clear the field and show warning
            if self.sales_tax_rate.text().strip():
                QMessageBox.warning(
                    self,
                    "Invalid Sales Tax Rate",
                    "Please enter a valid sales tax rate.\nExample: 8.5 for 8.5%"
                )
                self.sales_tax_rate.setText("")
        
        # Update sales tax amount display
        self.sales_tax_amount_label.setText(self.format_currency(sales_tax_amount))
        
        # Calculate and update final total (subtotal - discount + sales tax)
        subtotal_after_discount = max(subtotal - discount_amount, Decimal("0.00"))
        final_total = subtotal_after_discount + sales_tax_amount
        self.total_label.setText(self.format_currency(final_total))

    def add_line_item(self):
        row = self.line_items_table.rowCount()
        self.line_items_table.insertRow(row)
        
        # Add description field
        self.line_items_table.setItem(row, 0, QTableWidgetItem())
        
        # Add quantity spinbox
        qty_spin = QSpinBox()
        qty_spin.setMinimum(1)
        qty_spin.setMaximum(999999)
        qty_spin.valueChanged.connect(self.update_totals)
        self.line_items_table.setCellWidget(row, 1, qty_spin)
        
        # Add unit price field
        price_edit = QLineEdit()
        price_edit.setPlaceholderText("0.00")
        price_edit.textChanged.connect(self.update_totals)
        self.line_items_table.setCellWidget(row, 2, price_edit)
        
        # Add discount type combo
        discount_type = QComboBox()
        discount_type.addItems(["NONE", "PERCENTAGE", "FIXED_AMOUNT"])
        discount_type.currentTextChanged.connect(self.update_totals)
        self.line_items_table.setCellWidget(row, 3, discount_type)
        
        # Add discount value field
        discount_value = QLineEdit()
        discount_value.setPlaceholderText("0.00")
        discount_value.textChanged.connect(self.update_totals)
        self.line_items_table.setCellWidget(row, 4, discount_value)
        
        # Add discount description field
        self.line_items_table.setItem(row, 5, QTableWidgetItem())
        
        # Add total field (read-only)
        total_item = QTableWidgetItem(self.format_currency(0))
        total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.line_items_table.setItem(row, 6, total_item)

    def handle_client_email_change(self):
        """Handle changes to the client email field"""
        email = self.client_info["Contact Email"].text().strip()
        
        if email:
            # Check if client exists
            client_id = self.db.get_customer_id_by_email(email)
            
            if client_id:
                # Get existing client data
                existing_client = self.db.get_client_by_id(client_id)
                
                if existing_client:
                    # Populate fields with existing client data
                    self.client_info["Business Name"].setText(existing_client.get('business_name', ''))
                    self.client_info["Contact Name"].setText(existing_client.get('primary_contact_name', ''))
                    self.client_info["Phone Number"].setText(existing_client.get('primary_contact_phone', ''))
                    self.client_info["Street Address"].setPlainText(existing_client.get('street_address', ''))
                    
                    # Load client's payment terms
                    self.load_client_term(self.client_info["Contact Email"])
                    
                    # Store the client ID for later use
                    self.selected_client_id = client_id
                    
                    # Show status
                    self.status_label.setText(f"✓ Loaded existing client: {existing_client.get('business_name', '')}")
                    self.status_label.setStyleSheet("color: green;")
                    
                    # Clear status after 3 seconds
                    QTimer.singleShot(3000, self.clear_status)
            # else:
            #     # Clear fields if no existing client found
            #     self.client_info["Business Name"].clear()
            #     self.client_info["Contact Name"].clear()
            #     self.client_info["Phone Number"].clear()
            #     self.client_info["Street Address"].clear()
                
            #     # Reset payment terms to default
            #     self.payment_terms_dropdown.setCurrentIndex(0)  # Default to DUE ON RECEIPT
            #     self.term_description.clear()
                
            #     # Clear the selected client ID
            #     self.selected_client_id = None
                
            #     # Show status
            #     self.status_label.setText("ℹ️ New client - please fill in details")
            #     self.status_label.setStyleSheet("color: white;")
                
            #     # Clear status after 3 seconds
            #     QTimer.singleShot(3000, self.clear_status)

    def save_draft(self):
        """Save the current invoice as a draft"""
        # Validate basic fields
        if not self.client_info["Business Name"].text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a business name before saving draft.")
            return

        try:
            # Prepare draft data
            draft_data = {
                'invoice_number': self.invoice_fields["Invoice Number"].text(),
                'date': self.date_edit.date().toString("yyyy-MM-dd"),
                'business_name': self.client_info["Business Name"].text(),
                'contact_name': self.client_info["Contact Name"].text(),
                'contact_email': self.client_info["Contact Email"].text(),
                'phone_number': self.client_info["Phone Number"].text(),
                'street_address': self.client_info["Street Address"].toPlainText(),
                'customer_id': self.selected_client_id,
                'job': self.job_text.toPlainText().strip(),
                'notes': self.notes_text.toPlainText().strip(),
                'payment_terms': self.payment_terms_dropdown.currentText(),
                'sales_tax_rate': self.sales_tax_rate.text().strip(),
                'line_items': []
            }

            # Get line items
            for row in range(self.line_items_table.rowCount()):
                if not self.line_items_table.item(row, 0):  # Skip empty rows
                    continue
                    
                line_item = {
                    'description': self.line_items_table.item(row, 0).text(),
                    'quantity': self.line_items_table.cellWidget(row, 1).value(),
                    'unit_price': self.line_items_table.cellWidget(row, 2).text(),
                    'discount_type': self.line_items_table.cellWidget(row, 3).currentText(),
                    'discount_value': self.line_items_table.cellWidget(row, 4).text(),
                    'discount_description': self.line_items_table.item(row, 5).text() if self.line_items_table.item(row, 5) else '',
                    'total': self.line_items_table.item(row, 6).text().replace('$', '')
                }
                draft_data['line_items'].append(line_item)

            # Save to database
            self.db.save_invoice_draft(draft_data)
            
            # Show success message with OK button
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText("Draft saved successfully!")
            msg.setWindowTitle("Success")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            
            # Create a timer to auto-close the message
            close_timer = QTimer()
            close_timer.setSingleShot(True)
            close_timer.timeout.connect(msg.close)
            close_timer.start(2000)  # Auto-close after 2 seconds
            
            # Show the message box
            msg.exec()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save draft: {str(e)}")

    def focusOutEvent(self, event: QFocusEvent) -> None:
        """Auto-save when window loses focus"""
        super().focusOutEvent(event)
        self.auto_save()

    def auto_save(self):
        """Automatically save the current invoice as a draft"""
        # Don't auto-save if no business name (indicating a new/empty form)
        if not self.client_info["Business Name"].text().strip():
            return

        try:
            # Prepare draft data
            draft_data = {
                'invoice_number': self.invoice_fields["Invoice Number"].text(),
                'date': self.date_edit.date().toString("yyyy-MM-dd"),
                'business_name': self.client_info["Business Name"].text(),
                'contact_name': self.client_info["Contact Name"].text(),
                'contact_email': self.client_info["Contact Email"].text(),
                'phone_number': self.client_info["Phone Number"].text(),
                'street_address': self.client_info["Street Address"].toPlainText(),
                'customer_id': self.selected_client_id,
                'job': self.job_text.toPlainText().strip(),
                'notes': self.notes_text.toPlainText().strip(),
                'payment_terms': self.payment_terms_dropdown.currentText(),
                'sales_tax_rate': self.sales_tax_rate.text().strip(),
                'line_items': []
            }

            # Get line items
            for row in range(self.line_items_table.rowCount()):
                if not self.line_items_table.item(row, 0):  # Skip empty rows
                    continue
                    
                line_item = {
                    'description': self.line_items_table.item(row, 0).text(),
                    'quantity': self.line_items_table.cellWidget(row, 1).value(),
                    'unit_price': self.line_items_table.cellWidget(row, 2).text(),
                    'discount_type': self.line_items_table.cellWidget(row, 3).currentText(),
                    'discount_value': self.line_items_table.cellWidget(row, 4).text(),
                    'discount_description': self.line_items_table.item(row, 5).text() if self.line_items_table.item(row, 5) else '',
                    'total': self.line_items_table.item(row, 6).text().replace('$', '')
                }
                draft_data['line_items'].append(line_item)

            # Save to database
            self.db.save_invoice_draft(draft_data)
            
            # Show status message
            current_time = QDateTime.currentDateTime().toString("hh:mm:ss")
            self.status_label.setText(f"Auto-saved at {current_time}")
            
            # Clear status message after 3 seconds
            self.status_timer.start(3000)
            
        except Exception as e:
            # Log the error but don't show to user since this is automatic
            print(f"Auto-save failed: {str(e)}")

    def clear_status(self):
        """Clear the status message"""
        self.status_label.clear()

    def closeEvent(self, event):
        """Auto-save when closing the window"""
        self.auto_save()
        super().closeEvent(event)

    def confirm_clear_form(self):
        """Ask for confirmation before clearing the form"""
        reply = QMessageBox.question(
            self,
            "Confirm Clear",
            "Are you sure you want to clear all fields? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Default to No to prevent accidental clearing
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.clear_fields()
            self.generate_invoice_number()  # Generate a new invoice number
            QMessageBox.information(self, "Success", "Form has been cleared.")

    def go_back(self):
        """Return to the previous window"""
        # Cache the current data before navigating away
        self.cache_invoice_data()
        # Go back to wherever we came from, defaulting to invoice management if not set
        if self.previous_widget:
            self.main_window.stack.setCurrentWidget(self.previous_widget)
        else:
            self.main_window.stack.setCurrentWidget(self.main_window.find_invoice_page)

    def open_pdf(self):
        """Open the PDF for the current invoice number"""
        invoice_number = self.invoice_fields["Invoice Number"].text()
        pdf_path = os.path.join(PDF_DIR, f"{invoice_number}.pdf")
        
        if not os.path.exists(pdf_path):
            reply = QMessageBox.question(
                self,
                "PDF Not Found",
                "PDF hasn't been generated yet. Would you like to generate it now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.create_pdf()
            return
            
        try:
            # Use the default system PDF viewer
            if os.name == 'nt':  # Windows
                os.startfile(pdf_path)
            else:  # macOS and Linux
                import subprocess
                subprocess.run(['open' if sys.platform == 'darwin' else 'xdg-open', pdf_path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open PDF: {str(e)}")
    
    def create_pdf(self, exclude_number_check=False):
        """Handle creating and saving a PDF file"""
        # Validate fields, but skip validation if we just created the invoice
        if not exclude_number_check and not self.validate_fields():
            return

        # Get save location
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Invoice PDF",
            os.path.join(PDF_DIR, f"{self.invoice_fields['Invoice Number'].text()}.pdf"),
            "PDF Files (*.pdf)"
        )
        
        if filename:  # User didn't cancel
            try:
                # Create the PDF
                self.create_pdf_at_path(filename)
                
                # Ask if user wants to open the PDF
                reply = QMessageBox.question(
                    self,
                    "Success",
                    f"PDF has been created. Open now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    self.open_pdf_file(filename)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create PDF: {str(e)}")
    
    def cancel_invoice(self):
        """Cache the current data and return to main menu"""
        self.cache_invoice_data()
        self.return_to_main_menu()

    def return_to_main_menu(self):
        """Return to the main menu"""
        self.main_window.stack.setCurrentIndex(0)

    def cache_invoice_data(self):
        """Cache the current invoice data before navigating away"""
        self._cached_data = {
            "Invoice Number": self.invoice_fields["Invoice Number"].text(),
            "Date": self.date_edit.date(),
            "Business Name": self.client_info["Business Name"].text(),
            "Contact Email": self.client_info["Contact Email"].text(),
            "Street Address": self.client_info["Street Address"].toPlainText(),
            "Job": self.job_text.toPlainText(),
            "Notes": self.notes_text.toPlainText(),
            "Payment Terms": self.payment_terms_dropdown.currentText(),
            "Sales Tax Rate": self.sales_tax_rate.text(),
            "Line Items": []
        }

        # Cache line items
        for row in range(self.line_items_table.rowCount()):
            if not self.line_items_table.item(row, 0):  # Skip empty rows
                continue
                
            item = {
                "Description": self.line_items_table.item(row, 0).text(),
                "Quantity": self.line_items_table.cellWidget(row, 1).value(),
                "Unit Price": self.line_items_table.cellWidget(row, 2).text(),
                "Discount Type": self.line_items_table.cellWidget(row, 3).currentText(),
                "Discount Value": self.line_items_table.cellWidget(row, 4).text(),
                "Discount Description": self.line_items_table.item(row, 5).text() if self.line_items_table.item(row, 5) else "",
                "Total": self.line_items_table.item(row, 6).text()
            }
            self._cached_data["Line Items"].append(item)

    def restore_cached_data(self):
        """Restore the previously cached invoice data"""
        if not self._cached_data:
            return

        data = self._cached_data
        self.invoice_fields["Invoice Number"].setText(data["Invoice Number"])
        self.date_edit.setDate(data["Date"])
        self.client_info["Business Name"].setText(data["Business Name"])
        self.client_info["Contact Email"].setText(data["Contact Email"])
        self.client_info["Street Address"].setPlainText(data["Street Address"])
        self.job_text.setPlainText(data.get("Job", ""))
        self.notes_text.setPlainText(data.get("Notes", ""))
        self.payment_terms_dropdown.setCurrentText(data.get("Payment Terms", "NET30"))
        self.sales_tax_rate.setText(data.get("Sales Tax Rate", ""))

        # Clear existing line items
        self.line_items_table.setRowCount(0)

        # Restore line items
        for item in data["Line Items"]:
            row = self.line_items_table.rowCount()
            self.line_items_table.insertRow(row)
            
            # Description
            self.line_items_table.setItem(row, 0, QTableWidgetItem(item["Description"]))
            
            # Quantity
            qty_spin = QSpinBox()
            qty_spin.setMinimum(1)
            qty_spin.setMaximum(999999)
            qty_spin.setValue(item["Quantity"])
            qty_spin.valueChanged.connect(self.update_totals)
            self.line_items_table.setCellWidget(row, 1, qty_spin)
            
            # Unit Price
            price_edit = QLineEdit()
            price_edit.setText(str(item["Unit Price"]))
            price_edit.textChanged.connect(self.update_totals)
            self.line_items_table.setCellWidget(row, 2, price_edit)
            
            # Discount Type
            discount_type = QComboBox()
            discount_type.addItems(["NONE", "PERCENTAGE", "FIXED_AMOUNT"])
            discount_type.setCurrentText(item["Discount Type"])
            discount_type.currentTextChanged.connect(self.update_totals)
            self.line_items_table.setCellWidget(row, 3, discount_type)
            
            # Discount Value
            discount_value = QLineEdit()
            discount_value.setText(item["Discount Value"])
            discount_value.textChanged.connect(self.update_totals)
            self.line_items_table.setCellWidget(row, 4, discount_value)
            
            # Discount Description
            self.line_items_table.setItem(row, 5, QTableWidgetItem(item["Discount Description"]))
            
            # Total
            total_item = QTableWidgetItem(item["Total"])
            total_item.setFlags(total_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.line_items_table.setItem(row, 6, total_item)

        self.update_totals()
        self._cached_data = None
    
    def validate_fields(self):
        """Validate all required fields before saving"""
        # Validate invoice number
        invoice_number = self.invoice_fields["Invoice Number"].text().strip()
        if not invoice_number:
            QMessageBox.warning(self, "Validation Error", "Please enter an invoice number.")
            return False
            
        # Check if invoice number already exists in finalized invoices
        if self.db.invoice_number_exists(invoice_number):
            QMessageBox.warning(
                self,
                "Invoice Number Error", 
                "The invoice number already exists in the system. Either assign the invoice a new number or clear the form to start all over."
            )
            return False

        # Validate required fields
        if not self.client_info["Business Name"].text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a business name.")
            return False

        if not self.client_info["Contact Email"].text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a contact email.")
            return False

        if not self.client_info["Contact Name"].text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a contact name.")
            return False

        if not self.client_info["Phone Number"].text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a phone number.")
            return False

        if not self.client_info["Street Address"].toPlainText().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a street address.")
            return False
            
        if self.line_items_table.rowCount() == 0:
            QMessageBox.warning(self, "Validation Error", "Please add at least one line item.")
            return False
            
        for row in range(self.line_items_table.rowCount()):
            if not self.line_items_table.item(row, 0) or not self.line_items_table.item(row, 0).text():
                QMessageBox.warning(self, "Validation Error", f"Please enter a description for line item {row + 1}.")
                return False
                
            try:
                price = float(self.line_items_table.cellWidget(row, 2).text() or 0)
                if price < Decimal(0):
                    QMessageBox.warning(self, "Validation Error", f"Please enter a valid price for line item {row + 1}.")
                    return False
            except ValueError:
                QMessageBox.warning(self, "Validation Error", f"Invalid price format for line item {row + 1}.")
                return False
                
        return True
    
    def clear_fields(self):
        """Clear all form fields and reset to default state"""
        # Clear invoice fields
        for key, widget in self.invoice_fields.items():
            if isinstance(widget, QTextEdit):
                widget.clear()
            elif isinstance(widget, QLineEdit):
                widget.setText("")
            elif key == "Date":
                widget.setDate(QDate.currentDate())

        # Clear client info
        for widget in self.client_info.values():
            if isinstance(widget, QTextEdit):
                widget.clear()
            elif isinstance(widget, QLineEdit):
                widget.setText("")

        # Clear job and notes
        self.job_text.clear()
        self.notes_text.clear()

        # Reset payment terms
        self.payment_terms_dropdown.setCurrentText("DUE ON RECEIPT") # Default to DUE ON RECEIPT
        self.update_term_description()
        self.term_description.clear()

        # Clear line items
        self.line_items_table.setRowCount(0)

        # Reset totals
        self.subtotal_label.setText(self.format_currency(0))
        self.discount_type.setCurrentText("NONE")
        self.discount_value.clear()
        self.discount_description.clear()
        self.discount_amount_label.setText(self.format_currency(0))
        self.sales_tax_rate.clear()
        self.sales_tax_amount_label.setText(self.format_currency(0))
        self.total_label.setText(self.format_currency(0))

        # Generate new invoice number
        self.generate_invoice_number()
    