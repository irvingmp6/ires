from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QComboBox, QDateEdit, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, QDate
from database import Database
from ui_find_invoice import FindInvoiceWidget

class ManageInvoicesWidget(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("📋 Manage Invoices")
        title.setProperty("title", True)
        layout.addWidget(title)

        # Search filters group
        filters_group = QGroupBox("Search Filters")
        filters_layout = QFormLayout()

        # Invoice number filter
        self.invoice_number_input = QLineEdit()
        self.invoice_number_input.setPlaceholderText("Enter invoice number...")
        filters_layout.addRow("Invoice Number:", self.invoice_number_input)

        # Business name filter
        self.business_name_input = QLineEdit()
        self.business_name_input.setPlaceholderText("Enter business name...")
        filters_layout.addRow("Business Name:", self.business_name_input)

        # Date range filters
        date_range_layout = QHBoxLayout()
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        
        date_range_layout.addWidget(QLabel("From:"))
        date_range_layout.addWidget(self.date_from)
        date_range_layout.addWidget(QLabel("To:"))
        date_range_layout.addWidget(self.date_to)
        filters_layout.addRow("Date Range:", date_range_layout)

        # Status filter
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "All",
            "Active",
            "Void",
            "Paid - Pending Reconciliation",
            "Paid - Fully Reconciled"
        ])
        filters_layout.addRow("Status:", self.status_combo)

        # Amount range filters
        amount_range_layout = QHBoxLayout()
        self.amount_from = QLineEdit()
        self.amount_from.setPlaceholderText("Min amount")
        self.amount_to = QLineEdit()
        self.amount_to.setPlaceholderText("Max amount")
        amount_range_layout.addWidget(self.amount_from)
        amount_range_layout.addWidget(QLabel("to"))
        amount_range_layout.addWidget(self.amount_to)
        filters_layout.addRow("Amount Range ($):", amount_range_layout)

        filters_group.setLayout(filters_layout)
        layout.addWidget(filters_group)

        # Search button
        search_btn = QPushButton("🔍 Search")
        search_btn.clicked.connect(self.search_invoices)
        layout.addWidget(search_btn)

        # Results table
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "Invoice Number",
            "Date",
            "Business Name",
            "Total Amount",
            "Status",
            "Last Modified"
        ])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.doubleClicked.connect(self.view_invoice)
        
        # Set column widths
        self.table.setColumnWidth(0, 180)  # Invoice Number
        self.table.setColumnWidth(1, 100)  # Date
        self.table.setColumnWidth(2, 200)  # Business Name
        self.table.setColumnWidth(3, 120)  # Total Amount
        self.table.setColumnWidth(4, 150)  # Status
        self.table.setColumnWidth(5, 150)  # Last Modified
        
        layout.addWidget(self.table)

        # Return to main menu button
        back_btn = QPushButton("← Back to Main Menu")
        back_btn.clicked.connect(self.return_to_main_menu)
        layout.addWidget(back_btn)

    def search_invoices(self):
        # Clear existing results
        self.table.setRowCount(0)

        # Gather filter values
        filters = {
            'invoice_number': self.invoice_number_input.text().strip(),
            'business_name': self.business_name_input.text().strip(),
            'date_from': self.date_from.date().toString("yyyy-MM-dd"),
            'date_to': self.date_to.date().toString("yyyy-MM-dd"),
            'status': self.status_combo.currentText() if self.status_combo.currentText() != "All" else None,
            'amount_from': self.amount_from.text().strip(),
            'amount_to': self.amount_to.text().strip()
        }

        # Query database with filters
        results = self.db.search_invoices(filters)

        # Display results
        for row, invoice in enumerate(results):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(invoice['Invoice Number']))
            self.table.setItem(row, 1, QTableWidgetItem(invoice['Date']))
            self.table.setItem(row, 2, QTableWidgetItem(invoice['Business Name']))
            self.table.setItem(row, 3, QTableWidgetItem(f"${invoice['Total Amount']}"))
            self.table.setItem(row, 4, QTableWidgetItem(invoice['Status']))
            self.table.setItem(row, 5, QTableWidgetItem(invoice.get('Last Modified', 'N/A')))

            # Make row read-only
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

    def view_invoice(self):
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            invoice_number = self.table.item(selected_row, 0).text()
            
            # Get the invoice data first
            invoice_data = self.db.view_invoice(invoice_number)
            if not invoice_data:
                QMessageBox.warning(self, "Error", "Failed to load invoice data.")
                return
                
            # Create and show the FindInvoiceWidget
            find_invoice_widget = FindInvoiceWidget(self.main_window)
            find_invoice_widget.invoice_data = invoice_data  # Set the data first
            find_invoice_widget.display_invoice_data(invoice_data)  # Display it
            
            # Add and show the widget
            self.main_window.stack.addWidget(find_invoice_widget)
            self.main_window.stack.setCurrentWidget(find_invoice_widget)

    def return_to_main_menu(self):
        self.main_window.stack.setCurrentIndex(0) 