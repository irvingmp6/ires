from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
from database import Database
from PyQt6.QtWidgets import QFileDialog

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
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.layout.addWidget(title)

        # Invoice ID search bar
        input_layout = QHBoxLayout()
        self.invoice_id_input = QLineEdit()
        self.invoice_id_input.setPlaceholderText("Enter Invoice Number")
        find_btn = QPushButton("Find")
        cancel_btn = QPushButton("Cancel")

        find_btn.clicked.connect(self.find_invoice)
        cancel_btn.clicked.connect(self.return_to_main_menu)

        input_layout.addWidget(self.invoice_id_input)
        input_layout.addWidget(find_btn)
        input_layout.addWidget(cancel_btn)
        self.layout.addLayout(input_layout)

        # Info area
        self.info_label = QLabel()
        self.layout.addWidget(self.info_label)

        # Read-only data fields
        self.fields = {}
        for label_text in ["Invoice Number", "Date", "Business Name", "Contact Email", "Street Address", "Total Amount", "Status"]:
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
        self.table.setVisible(False)

        # Action buttons
        self.void_btn = QPushButton("Void Invoice")
        self.pdf_btn = QPushButton("Export as PDF")
        self.void_btn.clicked.connect(self.void_invoice)
        self.pdf_btn.clicked.connect(self.export_pdf)

        self.void_btn.setVisible(False)
        self.pdf_btn.setVisible(False)

        btns_layout = QHBoxLayout()
        btns_layout.addWidget(self.void_btn)
        btns_layout.addWidget(self.pdf_btn)
        self.layout.addLayout(btns_layout)

    def find_invoice(self):
        invoice_number = self.invoice_id_input.text().strip()
        if not invoice_number:
            QMessageBox.warning(self, "Missing ID", "Please enter an Invoice Number.")
            return

        invoice = self.db.find_invoice(invoice_number)
        if not invoice:
            self.info_label.setText("❌ No invoice found with that ID.")
            self.clear_fields()
            self.table.setVisible(False)
            self.void_btn.setVisible(False)
            self.pdf_btn.setVisible(False)
            return

        self.invoice_data = invoice
        self.info_label.setText("✅ Invoice found.")

        for key in self.fields:
            self.fields[key].setText(invoice.get(key, ""))

        self.table.setRowCount(0)
        self.table.setVisible(True)
        for item in invoice["Line Items"]:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(item["Description"]))
            self.table.setItem(row, 1, QTableWidgetItem(str(item["Quantity"])))
            self.table.setItem(row, 2, QTableWidgetItem(str(item["Unit Price"])))
            self.table.setItem(row, 3, QTableWidgetItem(str(item["Total"])))

        self.void_btn.setVisible(True)
        self.pdf_btn.setVisible(True)

    def void_invoice(self):
        if not self.invoice_data:
            return

        invoice_number = self.invoice_data["Invoice Number"]
        self.db.void_invoice(invoice_number)
        QMessageBox.information(self, "Voided", f"Invoice {invoice_number} marked as Voided.")
        self.fields["Status"].setText("Voided")

    def export_pdf(self):
        if not self.invoice_data:
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Export PDF", f"{self.invoice_data['Invoice Number']}.pdf", "PDF Files (*.pdf)")
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
        c.drawString(40, y, f"Invoice: {self.invoice_data['Invoice Number']}")
        y -= 30

        for key in ["Date", "Business Name", "Contact Email", "Street Address", "Status"]:
            c.setFont("Helvetica", 10)
            c.drawString(40, y, f"{key}: {self.invoice_data[key]}")
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
            c.drawString(40, y, item["Description"])
            c.drawString(250, y, str(item["Quantity"]))
            c.drawString(300, y, str(item["Unit Price"]))
            c.drawString(400, y, str(item["Total"]))
            y -= 15
            if y < 100:
                c.showPage()
                y = height - 40

        draw_line()
        c.setFont("Helvetica-Bold", 12)
        c.drawString(400, y - 10, f"Total: ${self.invoice_data['Total Amount']}")
        c.save()

        QMessageBox.information(self, "Exported", f"Invoice PDF saved to:\n{save_path}")

    def clear_fields(self):
        for field in self.fields.values():
            field.clear()
        self.table.setRowCount(0)

    def return_to_main_menu(self):
        self.main_window.stack.setCurrentIndex(0)

