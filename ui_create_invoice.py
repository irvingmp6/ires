import json
import os
from decimal import Decimal

from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QTextEdit, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView, QMessageBox,
    QDateEdit, QSpinBox, QDoubleSpinBox, QFileDialog
)
from PyQt6.QtCore import Qt, QDate

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from database import Database

from utils import PDF_DIR, JSON_DIR



class CreateInvoiceWidget(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window


        self.invoice_fields = {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Create New Invoice")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        # === Invoice Fields ===
        self.invoice_fields['Invoice Number'] = self._add_labeled_input("Invoice Number:", layout)
        self.invoice_fields['Date'] = self._add_labeled_date("Date:", layout)
        self.invoice_fields['Business Name'] = self._add_labeled_input("Business Name:", layout)
        self.invoice_fields['Contact Email'] = self._add_labeled_input("Contact Email:", layout)
        self.invoice_fields['Street Address'] = self._add_labeled_textarea("Street Address:", layout)

        # === Line Items Table ===
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Description", "Quantity", "Unit Price", "Total"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        # === Add/Remove Buttons ===
        btn_layout = QHBoxLayout()

        add_item_btn = QPushButton("+ Add Line Item")
        add_item_btn.clicked.connect(self.add_line_item)

        remove_item_btn = QPushButton("– Remove Selected Item")
        remove_item_btn.clicked.connect(self.remove_selected_line_item)

        btn_layout.addWidget(add_item_btn)
        btn_layout.addWidget(remove_item_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)

        # === Total ===
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        self.total_label = QLabel("Total: $0.00")
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        total_layout.addWidget(self.total_label)
        layout.addLayout(total_layout)

        # === Create PDF Button ===
        pdf_btn = QPushButton("🖨️ Create PDF")
        pdf_btn.clicked.connect(self.create_pdf)
        layout.addWidget(pdf_btn)

        # === Save Button ===
        save_btn = QPushButton("💾 Save for Later")
        save_btn.clicked.connect(self.save_invoice)
        layout.addWidget(save_btn)

        # === Cancel Button ===
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.cancel_invoice)
        layout.addWidget(cancel_btn)


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
        invoice = {
            "Invoice Number": self.invoice_fields["Invoice Number"].text(),
            "Date": self.invoice_fields["Date"].date().toString("yyyy-MM-dd"),
            "Business Name": self.invoice_fields["Business Name"].text(),
            "Contact Email": self.invoice_fields["Contact Email"].text(),
            "Street Address": self.invoice_fields["Street Address"].toPlainText(),
            "Line Items": [],
            "Total Amount": self.total_label.text().replace("Total: $", "")
        }

        # Validate
        if not invoice["Invoice Number"] or not invoice["Business Name"]:
            QMessageBox.warning(self, "Validation Error", "Invoice Number and Business Name are required.")
            return

        # Extract line items
        for row in range(self.table.rowCount()):
            item = {
                "Description": self.table.item(row, 0).text(),
                "Quantity": self.table.cellWidget(row, 1).value(),
                "Unit Price": self.table.cellWidget(row, 2).value(),
                "Total": self.table.item(row, 3).text()
            }
            invoice["Line Items"].append(item)

        filename = os.path.join(JSON_DIR, f"{invoice['Invoice Number']}.json")


        try:
            with open(filename, 'w') as f:
                json.dump(invoice, f, indent=4)
            QMessageBox.information(self, "Saved", f"Invoice saved as {filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save invoice: {e}")

    def cancel_invoice(self):
        self.cache_invoice_data()
        self.main_window.stack.setCurrentIndex(0)

    def cache_invoice_data(self):
        self._cached_data = {
            "Invoice Number": self.invoice_fields["Invoice Number"].text(),
            "Date": self.invoice_fields["Date"].date(),
            "Business Name": self.invoice_fields["Business Name"].text(),
            "Contact Email": self.invoice_fields["Contact Email"].text(),
            "Street Address": self.invoice_fields["Street Address"].toPlainText(),
            "Line Items": []
        }

        for row in range(self.table.rowCount()):
            item = {
                "Description": self.table.item(row, 0).text(),
                "Quantity": self.table.cellWidget(row, 1).value(),
                "Unit Price": self.table.cellWidget(row, 2).value()
            }
            self._cached_data["Line Items"].append(item)

    def restore_cached_data(self):
        if not hasattr(self, "_cached_data"):
            return

        data = self._cached_data
        self.invoice_fields["Invoice Number"].setText(data["Invoice Number"])
        self.invoice_fields["Date"].setDate(data["Date"])
        self.invoice_fields["Business Name"].setText(data["Business Name"])
        self.invoice_fields["Contact Email"].setText(data["Contact Email"])
        self.invoice_fields["Street Address"].setPlainText(data["Street Address"])

        self.table.setRowCount(0)
        for item in data["Line Items"]:
            self.add_line_item()
            row = self.table.rowCount() - 1
            self.table.item(row, 0).setText(item["Description"])
            self.table.cellWidget(row, 1).setValue(item["Quantity"])
            self.table.cellWidget(row, 2).setValue(item["Unit Price"])

        self.update_total()

    def clear_fields(self):
        for key, widget in self.invoice_fields.items():
            if isinstance(widget, QTextEdit):
                widget.clear()
            elif isinstance(widget, QLineEdit):
                widget.setText("")
            elif key == "Date":
                widget.setDate(QDate.currentDate())
        self.table.setRowCount(0)
        self.total_label.setText("Total: $0.00")

    def create_pdf(self):
        invoice_number = self.invoice_fields["Invoice Number"].text() or "unnamed"
        save_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Invoice PDF", 
            os.path.join(PDF_DIR, f"{invoice_number}.pdf"), 
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
        c.drawString(40, y, "Invoice")
        y -= 30

        c.setFont("Helvetica", 10)
        fields = [
            ("Invoice Number", self.invoice_fields["Invoice Number"].text()),
            ("Date", self.invoice_fields["Date"].date().toString("yyyy-MM-dd")),
            ("Business Name", self.invoice_fields["Business Name"].text()),
            ("Contact Email", self.invoice_fields["Contact Email"].text()),
            ("Street Address", self.invoice_fields["Street Address"].toPlainText()),
        ]
        for label, value in fields:
            c.drawString(40, y, f"{label}: {value}")
            y -= 15

        draw_line()
        y -= 10

        # Table Header
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
            c.drawString(400, y, f"${total}")
            y -= 15
            if y < 100:
                c.showPage()
                y = height - 40

        draw_line()

        c.setFont("Helvetica-Bold", 12)
        c.drawString(400, y - 10, f"Total: {self.total_label.text().replace('Total: ', '')}")

        c.save()
        QMessageBox.information(self, "PDF Created", f"PDF saved to:\n{save_path}")

        # Save to DB
        db = Database()
        invoice = {
            "Invoice Number": self.invoice_fields["Invoice Number"].text(),
            "Date": self.invoice_fields["Date"].date().toString("yyyy-MM-dd"),
            "Business Name": self.invoice_fields["Business Name"].text(),
            "Contact Email": self.invoice_fields["Contact Email"].text(),
            "Street Address": self.invoice_fields["Street Address"].toPlainText(),
            "Line Items": [],
            "Total Amount": self.total_label.text().replace("Total: $", "")
        }
        db.save_invoice(invoice, invoice["Line Items"], save_path)
