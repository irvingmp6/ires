from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QTextEdit,
    QDialog, QComboBox
)
from PyQt6.QtCore import Qt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
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
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def get_selected_status(self):
        return self.status_combo.currentText()

class ViewInvoiceWidget(QWidget):
    def __init__(self, main_window, parent_widget=None):
        super().__init__()
        self.main_window = main_window
        self.parent_widget = parent_widget
        self.db = Database()
        self.invoice_data = None
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)

        title = QLabel("📄 View Invoice")
        title.setProperty("title", True)
        self.layout.addWidget(title)

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
        self.table.setHorizontalHeaderLabels(["Description", "Qty", "Unit Price", "Total"])
        self.layout.addWidget(self.table)

        # Action buttons
        btns_layout = QHBoxLayout()
        
        self.back_btn = QPushButton("← Back")
        self.back_btn.clicked.connect(self.go_back)
        
        self.change_status_btn = QPushButton("Change Status")
        self.change_status_btn.clicked.connect(self.change_invoice_status)
        
        self.pdf_btn = QPushButton("Export as PDF")
        self.pdf_btn.clicked.connect(self.export_pdf)

        btns_layout.addWidget(self.back_btn)
        btns_layout.addWidget(self.change_status_btn)
        btns_layout.addWidget(self.pdf_btn)
        self.layout.addLayout(btns_layout)

    def display_invoice(self, invoice_number):
        invoice = self.db.find_invoice(invoice_number)
        if not invoice:
            QMessageBox.warning(self, "Error", "Invoice not found.")
            return

        self.invoice_data = invoice

        # Map database field names to display field names
        field_mapping = {
            "Invoice Number": invoice.get("invoice_number", ""),
            "Invoice Date": invoice.get("date", ""),
            "Business Name": invoice.get("business_name", ""),
            "Contact Email": invoice.get("primary_email", ""),
            "Street Address": invoice.get("street_address", ""),
            "Total Amount": invoice.get("total_amount", ""),
            "Status": invoice.get("status", "")
        }

        for key in self.fields:
            self.fields[key].setText(str(field_mapping.get(key, "")))

        self.table.setRowCount(0)
        for item in invoice["Line Items"]:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(item["Description"])))
            self.table.setItem(row, 1, QTableWidgetItem(str(item["Quantity"])))
            self.table.setItem(row, 2, QTableWidgetItem(str(item["Unit Price"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(item["Total"])))

    def go_back(self):
        if self.parent_widget:
            self.main_window.stack.setCurrentWidget(self.parent_widget)

    def change_invoice_status(self):
        if not self.invoice_data:
            QMessageBox.warning(self, "No Invoice", "No invoice is currently loaded.")
            return

        dialog = ChangeStatusDialog(self)
        if dialog.exec():
            new_status = dialog.get_selected_status()
            invoice_number = self.invoice_data["invoice_number"]
            self.db.update_invoice_status(invoice_number, new_status)
            self.fields["Status"].setText(new_status)
            QMessageBox.information(self, "Success", f"Invoice status updated to: {new_status}")

            # Update parent widget's invoice list if it exists
            if self.parent_widget and hasattr(self.parent_widget, 'load_client_invoices'):
                self.parent_widget.load_client_invoices()

    def export_pdf(self):
        if not self.invoice_data:
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Export PDF", 
            f"{self.invoice_data['invoice_number']}.pdf", 
            "PDF Files (*.pdf)")
        if not save_path:
            return

        c = canvas.Canvas(save_path, pagesize=LETTER)
        width, height = LETTER
        y = height - 40

        def draw_line():
            nonlocal y
            c.line(40, y, width - 40, y)
            y -= 20

        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, y, f"Invoice: {self.invoice_data['invoice_number']}")
        y -= 30

        # Map database field names to display names
        field_mapping = {
            "Date": self.invoice_data.get("date", ""),
            "Business Name": self.invoice_data.get("business_name", ""),
            "Contact Email": self.invoice_data.get("primary_email", ""),
            "Street Address": self.invoice_data.get("street_address", ""),
            "Status": self.invoice_data.get("status", "")
        }

        for key in ["Date", "Business Name", "Contact Email", "Street Address", "Status"]:
            c.setFont("Helvetica", 10)
            c.drawString(40, y, f"{key}: {field_mapping[key]}")
            y -= 15

        draw_line()
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, "Description")
        c.drawString(250, y, "Qty")
        c.drawString(300, y, "Unit Price")
        c.drawString(400, y, "Total")
        y -= 15

        c.setFont("Helvetica", 10)
        for item in self.invoice_data["Line Items"]:
            c.drawString(40, y, str(item["Description"]))
            c.drawString(250, y, str(item["Quantity"]))
            c.drawString(300, y, str(item["Unit Price"]))
            c.drawString(400, y, str(item["Total"]))
            y -= 15
            if y < 100:
                c.showPage()
                y = height - 40

        draw_line()
        c.setFont("Helvetica-Bold", 12)
        c.drawString(400, y - 10, f"Total: ${self.invoice_data['total_amount']}")
        c.save()

        QMessageBox.information(self, "Exported", f"Invoice PDF saved to:\n{save_path}") 