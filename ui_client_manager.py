from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QLineEdit, QTextEdit, QComboBox, QMessageBox,
    QSplitter, QHeaderView
)
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtCore import Qt, QRegularExpression

from database import Database
from ui_view_invoice import ViewInvoiceWidget

EMAIL_REGEX = r"^[\w\.-]+@[\w\.-]+\.\w+$"
PHONE_REGEX = r"^\+?[0-9\-\s]{7,15}$"

class ClientManagerWidget(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.db = Database()
        self.selected_client_id = None
        self.all_clients = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("👥 Client Manager")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setProperty("title", True)
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search clients...")
        self.search_input.textChanged.connect(self.filter_clients)
        layout.addWidget(self.search_input)

        # Create a splitter for the tables
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStretchFactor(0, 2)  # Give more stretch to the client list
        splitter.setStretchFactor(1, 1)  # Less stretch to the invoices
        layout.addWidget(splitter)

        # Clients table
        clients_widget = QWidget()
        clients_layout = QVBoxLayout(clients_widget)
        clients_label = QLabel("Clients")
        clients_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        clients_layout.addWidget(clients_label)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Business Name", "Email", "Address"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self.load_selected_client)
        self.table.setStyleSheet("font-size: 12px;")
        
        # Set column widths for clients table
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Business Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Email
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Address
        self.table.setColumnWidth(0, 200)  # Set Business Name column width to 200 pixels
        
        clients_layout.addWidget(self.table)
        splitter.addWidget(clients_widget)

        # Invoices table
        invoices_widget = QWidget()
        invoices_layout = QVBoxLayout(invoices_widget)
        invoices_label = QLabel("Related Invoices")
        invoices_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        invoices_layout.addWidget(invoices_label)

        self.invoices_table = QTableWidget()
        self.invoices_table.setColumnCount(4)
        self.invoices_table.setHorizontalHeaderLabels(["Invoice Number", "Date", "Amount", "Status"])
        self.invoices_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.invoices_table.itemDoubleClicked.connect(self.view_invoice)
        self.invoices_table.setStyleSheet("font-size: 12px;")
        
        # Set column widths for invoices table
        invoice_header = self.invoices_table.horizontalHeader()
        invoice_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Invoice Number
        invoice_header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Date
        invoice_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Amount
        invoice_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Status
        self.invoices_table.setColumnWidth(0, 180)  # Set Invoice Number column width to 180 pixels
        
        invoices_layout.addWidget(self.invoices_table)
        splitter.addWidget(invoices_widget)

        # Client details form
        details_layout = QVBoxLayout()
        
        # Business details (full width)
        business_group = QVBoxLayout()
        business_title = QLabel("Business Information")
        business_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        business_group.addWidget(business_title)
        
        self.business_name_input = QLineEdit()
        self.contact_address_input = QTextEdit()
        self.contact_address_input.setMaximumHeight(60)
        
        # Set font size for input fields
        input_style = "font-size: 12px;"
        self.business_name_input.setStyleSheet(input_style)
        self.contact_address_input.setStyleSheet(input_style)
        
        for label_text, widget in [
            ("Business Name:", self.business_name_input),
            ("Street Address:", self.contact_address_input),
        ]:
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 12px;")
            business_group.addWidget(label)
            business_group.addWidget(widget)
        
        details_layout.addLayout(business_group)
        
        # Contact Information (two columns)
        contacts_layout = QHBoxLayout()
        
        # Primary Contact (left column)
        primary_group = QVBoxLayout()
        primary_title = QLabel("Primary Contact")
        primary_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        primary_group.addWidget(primary_title)
        
        self.primary_contact_input = QLineEdit()
        self.primary_email_input = QLineEdit()
        self.primary_contact_phone_input = QLineEdit()
        
        # Set font size for primary contact inputs
        for widget in [self.primary_contact_input, self.primary_email_input, self.primary_contact_phone_input]:
            widget.setStyleSheet(input_style)
        
        for label_text, widget in [
            ("Name:", self.primary_contact_input),
            ("Email:", self.primary_email_input),
            ("Phone:", self.primary_contact_phone_input),
        ]:
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 12px;")
            primary_group.addWidget(label)
            primary_group.addWidget(widget)
            
        contacts_layout.addLayout(primary_group)
        
        # Secondary Contact (right column)
        secondary_group = QVBoxLayout()
        secondary_title = QLabel("Secondary Contact")
        secondary_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        secondary_group.addWidget(secondary_title)
        
        self.secondary_contact_name_input = QLineEdit()
        self.secondary_email_input = QLineEdit()
        self.secondary_contact_phone_input = QLineEdit()
        
        # Set font size for secondary contact inputs
        for widget in [self.secondary_contact_name_input, self.secondary_email_input, self.secondary_contact_phone_input]:
            widget.setStyleSheet(input_style)
        
        for label_text, widget in [
            ("Name:", self.secondary_contact_name_input),
            ("Email:", self.secondary_email_input),
            ("Phone:", self.secondary_contact_phone_input),
        ]:
            label = QLabel(label_text)
            label.setStyleSheet("font-size: 12px;")
            secondary_group.addWidget(label)
            secondary_group.addWidget(widget)
            
        contacts_layout.addLayout(secondary_group)
        
        # Add contacts layout to details
        details_layout.addLayout(contacts_layout)
        
        # Payment Terms (full width)
        terms_group = QVBoxLayout()
        terms_title = QLabel("Payment Terms")
        terms_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        terms_group.addWidget(terms_title)
        
        self.payment_terms_dropdown = QComboBox()
        self.payment_terms_dropdown.setStyleSheet("font-size: 12px;")
        self.payment_terms_dropdown.addItems(self.db.get_all_payment_terms_codes())
        terms_group.addWidget(self.payment_terms_dropdown)
        
        details_layout.addLayout(terms_group)
        
        # Add the details layout to the main layout
        layout.addLayout(details_layout)

        # Set up validators
        email_validator = QRegularExpressionValidator(QRegularExpression(EMAIL_REGEX))
        phone_validator = QRegularExpressionValidator(QRegularExpression(PHONE_REGEX))
        self.primary_email_input.setValidator(email_validator)
        self.secondary_email_input.setValidator(email_validator)
        self.primary_contact_phone_input.setValidator(phone_validator)
        self.secondary_contact_phone_input.setValidator(phone_validator)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Save Changes")
        refresh_btn = QPushButton("🔄 Refresh")
        cancel_btn = QPushButton("Cancel")

        save_btn.clicked.connect(self.save_client)
        refresh_btn.clicked.connect(self.load_clients)
        cancel_btn.clicked.connect(lambda: self.main_window.stack.setCurrentIndex(0))

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.load_clients()

    def load_clients(self):
        self.all_clients = self.db.get_all_clients()
        self.display_clients(self.all_clients)
        self.selected_client_id = None
        self.clear_fields()
        self.invoices_table.setRowCount(0)

    def filter_clients(self):
        phrase = self.search_input.text().lower()
        filtered = [
            c for c in self.all_clients if
            phrase in (c[1] or "").lower() or
            phrase in (c[2] or "").lower() or
            phrase in (c[3] or "").lower()
        ]
        self.display_clients(filtered)

    def display_clients(self, clients, highlight_client_id=None):
        self.table.setRowCount(0)
        for row, client in enumerate(clients):
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(client[1]))  # Business Name
            self.table.setItem(row, 1, QTableWidgetItem(client[2]))  # Email
            self.table.setItem(row, 2, QTableWidgetItem(client[3]))  # Address
            if highlight_client_id and client[0] == highlight_client_id:
                self.table.selectRow(row)

    def load_selected_client(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return
        row = selected[0].row()
        client = self.all_clients[row]
        self.selected_client_id = client[0]
        self.business_name_input.setText(client[1] or "")
        self.primary_email_input.setText(client[2] or "")
        self.contact_address_input.setPlainText(client[3] or "")
        self.primary_contact_input.setText(client[4] or "")
        self.primary_contact_phone_input.setText(client[5] or "")
        self.secondary_contact_name_input.setText(client[6] or "")
        self.secondary_email_input.setText(client[7] or "")
        self.secondary_contact_phone_input.setText(client[8] or "")
        self.payment_terms_dropdown.setCurrentText(client[9] or "")

        # Load related invoices
        self.load_client_invoices()

    def load_client_invoices(self):
        if not self.selected_client_id:
            self.invoices_table.setRowCount(0)
            return

        invoices = self.db.get_invoices_by_client_id(self.selected_client_id)
        self.invoices_table.setRowCount(0)
        for invoice in invoices:
            row = self.invoices_table.rowCount()
            self.invoices_table.insertRow(row)
            self.invoices_table.setItem(row, 0, QTableWidgetItem(str(invoice[0])))  # Invoice Number
            self.invoices_table.setItem(row, 1, QTableWidgetItem(str(invoice[1])))  # Date
            self.invoices_table.setItem(row, 2, QTableWidgetItem(f"${invoice[2]}"))  # Amount
            self.invoices_table.setItem(row, 3, QTableWidgetItem(str(invoice[3])))  # Status

    def view_invoice(self, item):
        row = item.row()
        invoice_number = self.invoices_table.item(row, 0).text()
        
        # Create the view invoice widget if it doesn't exist
        if not hasattr(self.main_window, 'view_invoice_page'):
            self.main_window.view_invoice_page = ViewInvoiceWidget(self.main_window, self)
            self.main_window.stack.addWidget(self.main_window.view_invoice_page)
        else:
            # Update the parent widget reference
            self.main_window.view_invoice_page.parent_widget = self
        
        # Display the invoice and switch to the view
        self.main_window.view_invoice_page.display_invoice(invoice_number)
        self.main_window.stack.setCurrentWidget(self.main_window.view_invoice_page)

    def clear_fields(self):
        for widget in [
            self.business_name_input, self.primary_email_input,
            self.contact_address_input, self.primary_contact_input,
            self.primary_contact_phone_input, self.secondary_contact_name_input,
            self.secondary_email_input, self.secondary_contact_phone_input
        ]:
            if isinstance(widget, QTextEdit):
                widget.clear()
            else:
                widget.setText("")
        self.payment_terms_dropdown.setCurrentIndex(0)

    def save_client(self):
        if self.selected_client_id is None:
            QMessageBox.warning(self, "No Selection", "Please select a client to edit.")
            return

        self.db.update_client(
            self.selected_client_id,
            self.business_name_input.text(),
            self.primary_email_input.text(),
            self.contact_address_input.toPlainText(),
            self.primary_contact_input.text(),
            self.primary_contact_phone_input.text(),
            self.secondary_contact_name_input.text(),
            self.secondary_email_input.text(),
            self.secondary_contact_phone_input.text(),
            self.payment_terms_dropdown.currentText()
        )

        QMessageBox.information(self, "Success", "Client updated successfully.")
        self.all_clients = self.db.get_all_clients()
        self.display_clients(self.all_clients, highlight_client_id=self.selected_client_id)
