import json
import os
from decimal import Decimal

from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QTextEdit, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QMessageBox,
    QDateEdit, QSpinBox, QDoubleSpinBox, QFileDialog, QComboBox, QGroupBox, QFormLayout, QSizePolicy
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

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("📝 Create New Invoice")
        title.setProperty("title", True)
        layout.addWidget(title)

        # Invoice Details Section
        invoice_details = QGroupBox("Invoice Details")
        invoice_layout = QFormLayout()

        # Invoice number field with regenerate button
        invoice_number_layout = QHBoxLayout()
        self.invoice_fields = {}
        self.invoice_fields["Invoice Number"] = QLineEdit()
        self.invoice_fields["Invoice Number"].setPlaceholderText("Enter invoice number")
        
        regenerate_btn = QPushButton("🔄")
        regenerate_btn.setToolTip("Generate a new invoice number")
        regenerate_btn.setMaximumWidth(30)  # Make the button compact
        regenerate_btn.clicked.connect(self.generate_invoice_number)
        
        invoice_number_layout.addWidget(self.invoice_fields["Invoice Number"])
        invoice_number_layout.addWidget(regenerate_btn)
        invoice_layout.addRow("Invoice Number:", invoice_number_layout)

        # Date field
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.dateChanged.connect(self.generate_invoice_number)  # Regenerate number when date changes
        invoice_layout.addRow("Date:", self.date_edit)

        # Client info
        self.client_info = {}
        
        # Business Name - single line
        self.client_info["Business Name"] = QLineEdit()
        invoice_layout.addRow("Business Name:", self.client_info["Business Name"])
        
        # Contact Name - single line
        self.client_info["Contact Name"] = QLineEdit()
        invoice_layout.addRow("Contact Name:", self.client_info["Contact Name"])
        
        # Contact Email - single line
        self.client_info["Contact Email"] = QLineEdit()
        self.client_info["Contact Email"].textChanged.connect(self.handle_client_email_change)
        invoice_layout.addRow("Contact Email:", self.client_info["Contact Email"])
        
        # Phone Number - single line
        self.client_info["Phone Number"] = QLineEdit()
        invoice_layout.addRow("Phone Number:", self.client_info["Phone Number"])
        
        # Street Address - multi-line
        self.client_info["Street Address"] = QTextEdit()
        self.client_info["Street Address"].setMaximumHeight(60)
        invoice_layout.addRow("Street Address:", self.client_info["Street Address"])

        invoice_details.setLayout(invoice_layout)
        layout.addWidget(invoice_details)

        # Line Items Section
        layout.addWidget(self.init_line_item_section())

        # Totals Section
        layout.addWidget(self.init_totals_section())

        # Add status label at the bottom
        layout.addWidget(self.status_label)

        # Action Buttons
        button_layout = QHBoxLayout()
        
        save_draft_btn = QPushButton("💾 Save Draft")
        save_draft_btn.clicked.connect(self.save_draft)
        save_draft_btn.setToolTip("Save your progress to continue later without creating the invoice")
        
        preview_btn = QPushButton("👁️ Preview PDF")
        preview_btn.clicked.connect(self.create_pdf)
        preview_btn.setToolTip("Generate a PDF preview without saving the invoice")
        
        create_btn = QPushButton("✅ Create Invoice")
        create_btn.clicked.connect(self.save_invoice)
        create_btn.setToolTip("Save the invoice and generate the final PDF")
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.cancel_invoice)
        
        button_layout.addWidget(save_draft_btn)
        button_layout.addWidget(preview_btn)
        button_layout.addWidget(create_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)

    def _add_labeled_input(self, label_text, layout):
        label = QLabel(label_text)
        input_field = QLineEdit()
        layout.addWidget(label)
        layout.addWidget(input_field)
        return input_field

    def _add_labeled_textarea(self, label_text, layout):
        label = QLabel(label_text)
        input_field = QTextEdit()
        layout.addWidget(label)
        layout.addWidget(input_field)
        return input_field

    def _add_labeled_date(self, label_text, layout):
        label = QLabel(label_text)
        input_field = QDateEdit()
        input_field.setCalendarPopup(True)
        input_field.setDate(QDate.currentDate())
        layout.addWidget(label)
        layout.addWidget(input_field)
        return input_field

    def add_line_item(self):
        row = self.table.rowCount()
        self.table.insertRow(row)

        desc_item = QTableWidgetItem("Item description")
        qty_widget = QSpinBox()
        qty_widget.setMinimum(1)
        qty_widget.setMaximum(999999)
        qty_widget.valueChanged.connect(self.update_total)

        price_widget = QDoubleSpinBox()
        price_widget.setDecimals(2)
        price_widget.setMinimum(0)
        price_widget.setMaximum(999999)
        price_widget.valueChanged.connect(self.update_total)

        total_item = QTableWidgetItem("0.00")
        total_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Make total read-only

        self.table.setItem(row, 0, desc_item)
        self.table.setCellWidget(row, 1, qty_widget)
        self.table.setCellWidget(row, 2, price_widget)
        self.table.setItem(row, 3, total_item)

    def remove_selected_line_item(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select a row to remove.")
            return
        selected_row = selected_items[0].row()
        self.table.removeRow(selected_row)
        self.update_total()


    def update_total(self):
        total = Decimal("0.00")
        for row in range(self.table.rowCount()):
            qty = self.table.cellWidget(row, 1).value()
            price = self.table.cellWidget(row, 2).value()
            line_total = Decimal(qty) * Decimal(price)
            self.table.item(row, 3).setText(f"{line_total:.2f}")
            total += line_total
        self.total_label.setText(f"Total: ${total:.2f}")

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
                'subtotal_amount': self.subtotal_label.text().replace('$', ''),
                'discount_type': self.discount_type.currentText(),
                'discount_value': self.discount_value.text(),
                'discount_description': self.discount_description.text(),
                'total_amount': self.total_label.text().replace('$', '')
            }

            # Get line items
            line_items = []
            for row in range(self.line_items_table.rowCount()):
                if not self.line_items_table.item(row, 0):  # Skip empty rows
                    continue
                    
                line_item = {
                    'description': self.line_items_table.item(row, 0).text(),
                    'quantity': self.line_items_table.cellWidget(row, 1).value(),
                    'unit_price': self.line_items_table.cellWidget(row, 2).text(),
                    'discount_type': self.line_items_table.cellWidget(row, 3).currentText(),
                    'discount_value': self.line_items_table.cellWidget(row, 4).text(),
                    'discount_description': self.line_items_table.item(row, 5).text(),
                    'total': self.line_items_table.item(row, 6).text().replace('$', '')
                }
                line_items.append(line_item)

            # Save to database
            self.db.save_invoice(invoice_data, line_items)
            
            # Delete any existing draft for this invoice
            try:
                self.db.delete_invoice_draft(invoice_data['invoice_number'])
            except Exception as draft_e:
                # Log the error but don't stop the process since the invoice was saved successfully
                print(f"Warning: Failed to delete draft after invoice creation: {str(draft_e)}")
            
            QMessageBox.information(self, "Success", "Invoice created successfully!")
            
            # Ask user if they want to generate PDF now
            reply = QMessageBox.question(
                self,
                "Generate PDF",
                "Would you like to generate the PDF for this invoice now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.create_pdf()
            
            self.return_to_main_menu()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save invoice: {str(e)}")

    def validate_fields(self):
        """Validate all required fields before saving"""
        # Validate invoice number
        invoice_number = self.invoice_fields["Invoice Number"].text().strip()
        if not invoice_number:
            QMessageBox.warning(self, "Validation Error", "Please enter an invoice number.")
            return False
            
        # Check if invoice number already exists
        if self.db.invoice_number_exists(invoice_number):
            QMessageBox.warning(
                self, 
                "Validation Error", 
                "This invoice number already exists. Please use a different number or click the regenerate button."
            )
            return False

        if not self.selected_client_id:
            QMessageBox.warning(self, "Validation Error", "Please select a client first.")
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
                if price <= 0:
                    QMessageBox.warning(self, "Validation Error", f"Please enter a valid price for line item {row + 1}.")
                    return False
            except ValueError:
                QMessageBox.warning(self, "Validation Error", f"Invalid price format for line item {row + 1}.")
                return False
                
        return True

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
                "Discount Description": self.line_items_table.item(row, 5).text(),
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

        # Clear line items
        self.line_items_table.setRowCount(0)

        # Reset totals
        self.subtotal_label.setText(self.format_currency(0))
        self.discount_type.setCurrentText("NONE")
        self.discount_value.clear()
        self.discount_description.clear()
        self.discount_amount_label.setText(self.format_currency(0))
        self.total_label.setText(self.format_currency(0))

        # Generate new invoice number
        self.generate_invoice_number()

    def create_pdf(self):
        # Validate fields
        if not self.validate_fields():
            return

        # Get save location
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Invoice PDF",
            os.path.join(PDF_DIR, f"{self.invoice_fields['Invoice Number'].text()}.pdf"),
            "PDF Files (*.pdf)"
        )
        
        if not filename:
            return

        # Prepare data
        fields = [
            ("Invoice Number", self.invoice_fields["Invoice Number"].text()),
            ("Date", self.date_edit.date().toString("yyyy-MM-dd")),
            ("Business Name", self.client_info["Business Name"].text()),
            ("Contact Email", self.client_info["Contact Email"].text()),
            ("Street Address", self.client_info["Street Address"].toPlainText()),
        ]

        try:
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
            for label, value in fields:
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
                    else:  # BULK
                        discount_text = f"Buy {discount_value}"
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
            
            c.drawString(350, y, "Final Total:")
            c.drawString(500, y, self.total_label.text())

            c.save()
            QMessageBox.information(self, "Success", f"PDF saved to:\n{filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create PDF: {str(e)}")

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
            self.payment_terms_dropdown.setCurrentIndex(0)
            self.term_description.clear()
    
    def generate_invoice_number(self):
        """Generate an invoice number in the format INV-YYYYMMDD-HHMMSS"""
        current_datetime = QDateTime.currentDateTime()
        date_part = current_datetime.toString("yyyyMMdd")
        time_part = current_datetime.toString("hhmmss")
        invoice_number = f"INV-{date_part}-{time_part}"
        self.invoice_fields["Invoice Number"].setText(invoice_number)
    
    def init_line_item_section(self):
        group = QGroupBox("Line Items")
        layout = QVBoxLayout()

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
        group = QGroupBox("Invoice Totals")
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
                        elif discount_type == "BULK":
                            # Parse bulk discount format (e.g., "3:1" means buy 3 get 1 free)
                            if ":" not in discount_value_text:
                                raise ValueError("Bulk discount must be in format 'X:Y'")
                            buy, get = map(int, discount_value_text.split(":"))
                            if buy <= 0 or get <= 0:
                                raise ValueError("Bulk discount values must be positive")
                            if get >= buy:
                                raise ValueError("Buy quantity must be greater than free quantity")
                            total_sets = int(qty) // (buy + get)
                            discount = (total_sets * get) * unit_price
                            line_total -= discount
                    except (ValueError, decimal.InvalidOperation) as e:
                        error_msg = str(e) if str(e) != "decimal.InvalidOperation" else "Invalid number format"
                        QMessageBox.warning(
                            self,
                            "Invalid Discount",
                            f"Invalid discount in row {row + 1}: {error_msg}\n\n"
                            "Valid formats:\n"
                            "- Percentage: Enter a number between 0-100\n"
                            "- Fixed Amount: Enter a valid number\n"
                            "- Bulk: Enter in format 'X:Y' (e.g., '3:1' for buy 3 get 1 free)"
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
        
        # Calculate and update final total
        final_total = max(subtotal - discount_amount, Decimal("0.00"))  # Ensure total never goes negative
        self.total_label.setText(self.format_currency(final_total))

    def add_line_item(self):
        row = self.line_items_table.rowCount()
        self.line_items_table.insertRow(row)
        
        # Add description field
        self.line_items_table.setItem(row, 0, QTableWidgetItem())
        
        # Add quantity spinbox
        qty_spin = QSpinBox()
        qty_spin.setMinimum(1)
        qty_spin.valueChanged.connect(self.update_totals)
        self.line_items_table.setCellWidget(row, 1, qty_spin)
        
        # Add unit price field
        price_edit = QLineEdit()
        price_edit.setPlaceholderText("0.00")
        price_edit.textChanged.connect(self.update_totals)
        self.line_items_table.setCellWidget(row, 2, price_edit)
        
        # Add discount type combo
        discount_type = QComboBox()
        discount_type.addItems(["NONE", "PERCENTAGE", "FIXED_AMOUNT", "BULK"])
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
        """Handle client email changes and update selected_client_id"""
        email = self.client_info["Contact Email"].text().strip()
        if not email:
            self.selected_client_id = None
            return

        # Try to find existing client
        client_id = self.db.get_customer_id_by_email(email)
        if client_id:
            # Use existing client automatically
            self.selected_client_id = client_id
            # Load their information
            client_info = self.db.get_client_by_id(client_id)
            if client_info:
                self.client_info["Business Name"].setText(client_info.get('business_name', ''))
                self.client_info["Contact Name"].setText(client_info.get('primary_contact_name', ''))
                self.client_info["Phone Number"].setText(client_info.get('primary_contact_phone', ''))
                self.client_info["Street Address"].setPlainText(client_info.get('street_address', ''))
        else:
            # No existing client found - create new one
            try:
                client_data = {
                    'business_name': self.client_info["Business Name"].text().strip(),
                    'primary_email': email,
                    'street_address': self.client_info["Street Address"].toPlainText().strip(),
                    'primary_contact_name': self.client_info["Contact Name"].text().strip(),
                    'primary_contact_phone': self.client_info["Phone Number"].text().strip(),
                    'secondary_contact_name': '',
                    'secondary_email': '',
                    'secondary_contact_phone': '',
                    'payment_terms_code': 'NET30'  # Default payment terms
                }
                self.selected_client_id = self.db.create_new_client(client_data)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to create new client: {str(e)}")
                self.selected_client_id = None
    
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
            
            # Show a temporary status message
            status_msg = QMessageBox(self)
            status_msg.setIcon(QMessageBox.Icon.Information)
            status_msg.setText("Draft saved successfully!")
            status_msg.setWindowTitle("Success")
            status_msg.setStandardButtons(QMessageBox.StandardButton.NoButton)
            status_msg.show()
            
            # Auto-close the message after 1.5 seconds
            QTimer.singleShot(1500, status_msg.close)
            
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
    