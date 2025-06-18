import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QTextEdit,
    QDialog, QComboBox
)
from PyQt6.QtCore import Qt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode import qr
from database import Database
from PyQt6.QtWidgets import QFileDialog

class ChangeStatusDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Change Invoice Status")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Status dropdown
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "Active",
            "Void",
            "Paid - Pending Reconciliation",
            "Paid - Fully Reconciled"
        ])
        layout.addWidget(QLabel("Select New Status:"))
        layout.addWidget(self.status_combo)

        # Buttons
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        back_btn = QPushButton("← Back")
        ok_btn.clicked.connect(self.accept)
        back_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(back_btn)
        layout.addLayout(btn_layout)

    def get_selected_status(self):
        return self.status_combo.currentText()

class FindInvoiceWidget(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.db = Database()
        self.invoice_data = None
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)

        title = QLabel("🔍 Find Invoice")
        title.setProperty("title", True)
        self.layout.addWidget(title)

        # Invoice ID search bar
        input_layout = QHBoxLayout()
        self.invoice_id_input = QLineEdit()
        self.invoice_id_input.setPlaceholderText("Enter Invoice Number")
        find_btn = QPushButton("Find")
        find_btn.clicked.connect(self.find_invoice)

        input_layout.addWidget(self.invoice_id_input)
        input_layout.addWidget(find_btn)
        self.layout.addLayout(input_layout)

        # Info area
        self.info_label = QLabel()
        self.layout.addWidget(self.info_label)

        # Read-only data fields
        self.fields = {}
        for label_text in ["Invoice Number", "Invoice Date", "Business Name", "Contact Email", "Street Address", "Total Amount", "Status"]:
            label = QLabel(f"{label_text}:")
            text = QTextEdit()
            text.setReadOnly(True)
            text.setMaximumHeight(50)
            self.layout.addWidget(label)
            self.layout.addWidget(text)
            self.fields[label_text] = text

        # Line item table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Description", "Quantity", "Unit Price", "Total"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.layout.addWidget(self.table)

        # Action buttons
        action_layout = QHBoxLayout()
        
        change_status_btn = QPushButton("Change Status")
        change_status_btn.clicked.connect(self.change_invoice_status)
        action_layout.addWidget(change_status_btn)
        
        reprint_btn = QPushButton("🖨️ Reprint PDF")
        reprint_btn.clicked.connect(self.reprint_pdf)
        action_layout.addWidget(reprint_btn)

        back_btn = QPushButton("← Back to Main Menu")
        back_btn.clicked.connect(self.return_to_main_menu)
        action_layout.addWidget(back_btn)
        
        self.layout.addLayout(action_layout)

    def change_invoice_status(self):
        if not self.invoice_data:
            QMessageBox.warning(self, "No Invoice", "Please find an invoice first.")
            return

        dialog = ChangeStatusDialog(self)
        if dialog.exec():
            new_status = dialog.get_selected_status()
            invoice_number = self.invoice_data["invoice_number"]
            try:
                self.db.update_invoice_status(invoice_number, new_status)
                self.fields["Status"].setText(new_status)
                QMessageBox.information(self, "Success", f"Invoice status updated to: {new_status}")
                
                # Update our local data to reflect the change
                self.invoice_data["status"] = new_status
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update invoice status: {str(e)}")

    def find_invoice(self):
        invoice_number = self.invoice_id_input.text().strip()
        if not invoice_number:
            QMessageBox.warning(self, "No Input", "Please enter an invoice number.")
            return

        try:
            self.invoice_data = self.db.view_invoice(invoice_number)
            if not self.invoice_data:
                QMessageBox.warning(self, "Not Found", "No invoice found with that number.")
                return

            self.display_invoice_data(self.invoice_data)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load invoice: {str(e)}")

    def return_to_main_menu(self):
        self.main_window.stack.setCurrentIndex(0)

    def reprint_pdf(self):
        if not self.invoice_data:
            QMessageBox.warning(self, "No Invoice", "Please find an invoice first.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Invoice PDF", 
            f"{self.invoice_data['Invoice Number']}.pdf",
            "PDF Files (*.pdf)"
        )
        if not save_path:
            return

        c = canvas.Canvas(save_path, pagesize=LETTER)
        width, height = LETTER
        y = height - 40
        page_number = 1

        def draw_line():
            nonlocal y
            c.line(40, y, width - 40, y)
            y -= 20

        def add_page_number():
            c.saveState()
            c.setFont("Helvetica", 8)
            text = f"Page {page_number}"
            c.drawString(width/2 - 20, 30, text)
            c.restoreState()

        def get_status_color():
            status = self.invoice_data['Status']
            if status == "Void":
                return colors.red
            elif status == "Paid - Fully Reconciled":
                return colors.green
            elif status == "Paid - Pending Reconciliation":
                return colors.orange
            return colors.black

        # Add logo if available
        if hasattr(self.main_window, 'settings') and 'logo_path' in self.main_window.settings:
            logo_path = self.main_window.settings['logo_path']
            if os.path.exists(logo_path):
                c.drawImage(logo_path, width - 200, height - 60, width=150, preserveAspectRatio=True)

        # Title
        c.setFont("Helvetica-Bold", 24)
        c.drawString(40, y, "INVOICE")
        y -= 40

        # Invoice Details with colored status
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, f"Invoice Number: {self.invoice_data['Invoice Number']}")
        
        # Draw status with appropriate color
        status_color = get_status_color()
        c.setFillColor(status_color)
        c.drawString(300, y, f"Status: {self.invoice_data['Status']}")
        c.setFillColor(colors.black)  # Reset color
        y -= 25

        c.setFont("Helvetica", 12)
        c.drawString(40, y, f"Date: {self.invoice_data['Date']}")
        y -= 30

        # Add watermark for voided invoices
        if self.invoice_data['Status'] == "Void":
            c.saveState()
            c.setFont("Helvetica-Bold", 80)
            c.setFillColor(colors.red, alpha=0.3)
            c.rotate(45)
            c.drawString(150, 100, "VOID")
            c.restoreState()

        # Business Details
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Bill To:")
        y -= 20

        c.setFont("Helvetica", 12)
        c.drawString(40, y, self.invoice_data['Business Name'])
        y -= 15
        
        # Split address into lines and draw each line
        address_lines = self.invoice_data['Street Address'].split('\n')
        for line in address_lines:
            c.drawString(40, y, line.strip())
            y -= 15

        c.drawString(40, y, self.invoice_data['Contact Email'])
        y -= 30

        # Line Items Header
        draw_line()
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "Description")
        c.drawString(300, y, "Quantity")
        c.drawString(380, y, "Unit Price")
        c.drawString(460, y, "Total")
        y -= 15
        draw_line()

        # Line Items
        c.setFont("Helvetica", 11)
        for item in self.invoice_data["Line Items"]:
            # Check if we need a new page
            if y < 100:
                add_page_number()
                c.showPage()
                page_number += 1
                y = height - 40

                # Add watermark on new page if voided
                if self.invoice_data['Status'] == "Void":
                    c.saveState()
                    c.setFont("Helvetica-Bold", 80)
                    c.setFillColor(colors.red, alpha=0.3)
                    c.rotate(45)
                    c.drawString(150, 100, "VOID")
                    c.restoreState()

                # Redraw headers on new page
                c.setFont("Helvetica-Bold", 12)
                c.drawString(40, y, "Description")
                c.drawString(300, y, "Quantity")
                c.drawString(380, y, "Unit Price")
                c.drawString(460, y, "Total")
                y -= 15
                draw_line()
                c.setFont("Helvetica", 11)

            c.drawString(40, y, item["Description"])
            c.drawString(300, y, str(item["Quantity"]))
            c.drawString(380, y, f"${item['Unit Price']}")
            c.drawString(460, y, f"${item['Total']}")
            y -= 20

        # Total
        y -= 10
        draw_line()
        c.setFont("Helvetica-Bold", 14)
        total_text = f"Total Amount: ${self.invoice_data['Total Amount']}"
        c.drawString(width - 200, y, total_text)

        # Payment Terms
        if 'Term' in self.invoice_data:
            y -= 40
            c.setFont("Helvetica-Bold", 11)
            c.drawString(40, y, "Payment Terms:")
            c.setFont("Helvetica", 11)
            c.drawString(130, y, self.invoice_data['Term'])

        # Add final page number
        add_page_number()

        c.save()
        QMessageBox.information(self, "Success", f"PDF saved to:\n{save_path}")

    def display_invoice_data(self, invoice_data):
        """Display invoice data in the form without modifying the database."""
        if not invoice_data:
            return

        # Display invoice data using correct case from database
        self.fields["Invoice Number"].setText(invoice_data["invoice_number"])
        self.fields["Invoice Date"].setText(invoice_data["date"])
        self.fields["Business Name"].setText(invoice_data["business_name"])
        self.fields["Contact Email"].setText(invoice_data["primary_email"])
        self.fields["Street Address"].setText(invoice_data["street_address"])
        self.fields["Total Amount"].setText(invoice_data["total_amount"])
        self.fields["Status"].setText(invoice_data["status"])

        # Display line items
        self.table.setRowCount(0)
        for item in invoice_data["Line Items"]:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(item["Description"]))
            self.table.setItem(row, 1, QTableWidgetItem(str(item["Quantity"])))
            self.table.setItem(row, 2, QTableWidgetItem(f"${item['Unit Price']}"))
            self.table.setItem(row, 3, QTableWidgetItem(f"${item['Total']}"))

