from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QSpinBox, QComboBox, 
    QDateEdit, QMessageBox, QHeaderView, QDoubleSpinBox, QFileDialog
)
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtCore import QDate, QRegularExpression, Qt
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
import json
import os
from datetime import datetime
from database import Database
from utils import PDF_DIR, JSON_DIR

class CreateInvoiceWidget(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.db = Database()
        self.cached_invoice_data = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.invoice_fields = {}

        # Fields
        self.invoice_fields["Invoice Number"] = QLineEdit(self.generate_invoice_id())
        self.invoice_fields["Invoice Date"] = QDateEdit()
        self.invoice_fields["Invoice Date"].setDisplayFormat("MM/dd/yyyy")
        self.invoice_fields["Invoice Date"].setDate(QDate.currentDate())
        self.invoice_fields["Business Name"] = QLineEdit()
        self.invoice_fields["Client Email"] = QLineEdit()
        self.invoice_fields["Client Address"] = QTextEdit()

        for label, widget in self.invoice_fields.items():
            layout.addWidget(QLabel(label))
            layout.addWidget(widget)

        # Validators
        email_validator = QRegularExpressionValidator(QRegularExpression(r"^[\w\.-]+@[\w\.-]+\.\w+$"))
        self.invoice_fields["Client Email"].setValidator(email_validator)

        layout.addWidget(QLabel("Term:"))
        self.term_dropdown = QComboBox()
        self.term_dropdown.addItems(self.db.get_terms())
        layout.addWidget(self.term_dropdown)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Description", "Qty", "Unit Price", "Total"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        add_btn = QPushButton("➕ Add Line Item")
        remove_btn = QPushButton("➖ Remove Selected Item")
        add_btn.clicked.connect(self.add_line_item)
        remove_btn.clicked.connect(self.remove_selected_item)
        btns.addWidget(add_btn)
        btns.addWidget(remove_btn)
        layout.addLayout(btns)

        self.total_label = QLabel("Total: $0.00")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.total_label.setStyleSheet("padding-right: 14px; font-weight: bold;")
        layout.addWidget(self.total_label)

        actions = QHBoxLayout()

        # ==== Import Button ====
        import_btn = QPushButton("⬇️ Import")
        import_btn.clicked.connect(self.import_invoice)
        actions.addWidget(import_btn)

        # ==== Save for Later Button ====
        save_btn = QPushButton("💾 Save for Later")
        save_btn.clicked.connect(self.save_invoice)
        actions.addWidget(save_btn)

        # ==== Create PDF Button ====
        pdf_btn = QPushButton("🖨️ Create PDF")
        pdf_btn.clicked.connect(self.create_pdf)
        actions.addWidget(pdf_btn)

        # ====Clear Button ====
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.clicked.connect(self.clear_fields)
        actions.addWidget(clear_btn)

        # ==== Cancel Button ====
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.cancel_invoice)
        actions.addWidget(cancel_btn)

        layout.addLayout(actions)

    def generate_invoice_id(self):
        now = datetime.now()
        prefix = "BXRINV"
        date_part = now.strftime("%y%m%d")
        sequence_part = f"{(now.hour * 60) + now.minute + 1:04d}"
        return f"{prefix}-{date_part}-{sequence_part}"

    def add_line_item(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(""))

        qty = QSpinBox()
        qty.setMinimum(1)
        qty.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        qty.valueChanged.connect(self.update_total)
        self.table.setCellWidget(row, 1, qty)

        price = QDoubleSpinBox()
        price.setMinimum(0.00)
        price.setMaximum(100000.00)
        price.setDecimals(2)
        price.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        price.setPrefix("$")
        price.valueChanged.connect(self.update_total)
        self.table.setCellWidget(row, 2, price)

        self.table.setItem(row, 3, QTableWidgetItem("$0.00"))
        self.update_total()

    def remove_selected_item(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self.update_total()

    def update_total(self):
        total = 0.0
        for row in range(self.table.rowCount()):
            qty = self.table.cellWidget(row, 1).value()
            price = self.table.cellWidget(row, 2).value()
            line_total = qty * price
            total_item = QTableWidgetItem(f"${line_total:.2f}  ")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 3, total_item)
            total += line_total
        self.total_label.setText(f"Total: ${total:.2f}")

    def cancel_invoice(self):
        self.cache_invoice_data()
        self.main_window.stack.setCurrentIndex(0)

    def cache_invoice_data(self):
        for key, widget in self.invoice_fields.items():
            if key == "Invoice Date":
                self.cached_invoice_data[key] = widget.date().toString("MM/dd/yyyy")
            elif isinstance(widget, QTextEdit):
                self.cached_invoice_data[key] = widget.toPlainText()
            else:
                self.cached_invoice_data[key] = widget.text()
        self.cached_invoice_data["Term"] = self.term_dropdown.currentText()

    def restore_cached_data(self):
        for key, value in self.cached_invoice_data.items():
            widget = self.invoice_fields.get(key)
            if widget:
                if key == "Invoice Date":
                    widget.setDate(QDate.fromString(value, "MM/dd/yyyy"))
                elif isinstance(widget, QTextEdit):
                    widget.setPlainText(value)
                else:
                    widget.setText(value)
        if "Term" in self.cached_invoice_data:
            self.term_dropdown.setCurrentText(self.cached_invoice_data["Term"])

    def save_invoice(self):
        invoice = {
            "Invoice Number": self.invoice_fields["Invoice Number"].text(),
            "Invoice Date": self.invoice_fields["Invoice Date"].date().toString("MM/dd/yyyy"),
            "Business Name": self.invoice_fields["Business Name"].text(),
            "Client Email": self.invoice_fields["Client Email"].text(),
            "Client Address": self.invoice_fields["Client Address"].toPlainText(),
            "Term": self.term_dropdown.currentText(),
            "Line Items": [],
            "Total Amount": self.total_label.text().replace("Total: $", "")
        }
        for row in range(self.table.rowCount()):
            invoice["Line Items"].append({
                "Description": self.table.item(row, 0).text(),
                "Quantity": self.table.cellWidget(row, 1).value(),
                "Unit Price": self.table.cellWidget(row, 2).value(),
                "Total": self.table.item(row, 3).text()
            })
        os.makedirs(JSON_DIR, exist_ok=True)
        path = os.path.join(JSON_DIR, f"{invoice['Invoice Number']}.json")
        with open(path, "w") as f:
            json.dump(invoice, f, indent=4)
        QMessageBox.information(self, "Saved", f"Invoice saved to {path}")

    def create_pdf(self):
        invoice_number = self.invoice_fields["Invoice Number"].text() or "unnamed"
        options = QFileDialog.Option.ShowDirsOnly
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Invoice PDF",
            f"{invoice_number}.pdf",
            "PDF Files (*.pdf);;All Files (*)",
            options=options
        )
        if not file_path:
            return
        save_path = file_path

        c = canvas.Canvas(save_path, pagesize=LETTER)
        width, height = LETTER
        y = height - 40
        c.setFont("Helvetica-Bold", 16)
        c.drawString(40, y, "Invoice")
        y -= 30
        fields = [
            ("Invoice Number", self.invoice_fields["Invoice Number"].text()),
            ("Invoice Date", self.invoice_fields["Invoice Date"].date().toString("MM/dd/yyyy")),
            ("Business Name", self.invoice_fields["Business Name"].text()),
            ("Client Email", self.invoice_fields["Client Email"].text()),
            ("Client Address", self.invoice_fields["Client Address"].toPlainText()),
            ("Term", self.term_dropdown.currentText())
        ]
        for label, value in fields:
            c.drawString(40, y, f"{label}: {value}")
            y -= 15
        c.line(40, y, width - 40, y)
        y -= 20
        c.setFont("Helvetica-Bold", 10)
        c.drawString(40, y, "Description")
        c.drawString(250, y, "Qty")
        c.drawString(300, y, "Unit Price")
        c.drawString(400, y, "Total")
        y -= 15
        c.setFont("Helvetica", 10)
        for row in range(self.table.rowCount()):
            desc = self.table.item(row, 0).text()
            qty = self.table.cellWidget(row, 1).value()
            price = self.table.cellWidget(row, 2).value()
            total = self.table.item(row, 3).text()
            c.drawString(40, y, desc)
            c.drawString(250, y, str(qty))
            c.drawString(300, y, f"${price:.2f}")
            c.drawString(400, y, total)
            y -= 15
        c.drawString(400, y - 10, f"Total: {self.total_label.text().replace('Total: ', '')}")
        c.save()
        QMessageBox.information(self, "PDF Created", f"Invoice PDF saved to: {save_path}")

        # Save to DB
        db = Database()
        invoice_db_input = {
            "Invoice Number": self.invoice_fields["Invoice Number"].text(),
            "Invoice Date": self.invoice_fields["Invoice Date"].date().toString("MM/dd/yyyy"),
            "Business Name": self.invoice_fields["Business Name"].text(),
            "Contact Email": self.invoice_fields["Client Email"].text(),
            "Street Address": self.invoice_fields["Client Address"].toPlainText(),
            "Term": self.term_dropdown.currentText(),
            "Line Items": [],
            "Total Amount": self.total_label.text().replace("Total: $", "")
        }
        for row in range(self.table.rowCount()):
            invoice_db_input["Line Items"].append({
                "Description": self.table.item(row, 0).text(),
                "Quantity": self.table.cellWidget(row, 1).value(),
                "Unit Price": self.table.cellWidget(row, 2).value(),
                "Total": self.table.item(row, 3).text()
            })
        db.save_invoice(invoice_db_input, invoice_db_input["Line Items"])

    def import_invoice(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Invoice",
            JSON_DIR,
            "JSON Files (*.json);;All Files (*)"
        )
        if not file_path:
            return
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            self.clear_fields()
            self.invoice_fields["Invoice Number"].setText(data.get("Invoice Number", ""))
            self.invoice_fields["Invoice Date"].setDate(QDate.fromString(data.get("Invoice Date", ""), "MM/dd/yyyy"))
            self.invoice_fields["Business Name"].setText(data.get("Business Name", ""))
            self.invoice_fields["Client Email"].setText(data.get("Client Email", ""))
            self.invoice_fields["Client Address"].setPlainText(data.get("Client Address", ""))
            self.term_dropdown.setCurrentText(data.get("Term", ""))

            self.table.setRowCount(0)
            for item in data.get("Line Items", []):
                self.add_line_item()
                row = self.table.rowCount() - 1
                self.table.setItem(row, 0, QTableWidgetItem(item.get("Description", "")))
                self.table.cellWidget(row, 1).setValue(item.get("Quantity", 1))
                self.table.cellWidget(row, 2).setValue(float(item.get("Unit Price", 0)))
                self.table.setItem(row, 3, QTableWidgetItem(item.get("Total", "$0.00")))
            self.update_total()
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", f"Failed to import invoice:\n{e}")
    

    def clear_fields(self):
        for key, widget in self.invoice_fields.items():
            if isinstance(widget, QTextEdit):
                widget.clear()
            elif isinstance(widget, QDateEdit):
                widget.setDate(QDate.currentDate())
            else:
                widget.setText("")
        self.term_dropdown.setCurrentIndex(0)
        self.table.setRowCount(0)
        self.total_label.setText("Total: $0.00")
    