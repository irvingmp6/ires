from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt
from database import Database


class FindExistingClientWidget(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.db = Database()
        self.matching_clients = []
        self.selected_row = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        self.info_label = QLabel("Search for an existing client")
        self.info_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.info_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter email, contact name, or client ID")
        layout.addWidget(self.search_input)

        button_layout = QHBoxLayout()
        search_btn = QPushButton("Search")
        back_btn = QPushButton("← Back to Main Menu")
        search_btn.clicked.connect(self.perform_search)
        back_btn.clicked.connect(lambda: self.main_window.stack.setCurrentIndex(0))
        button_layout.addWidget(search_btn)
        button_layout.addWidget(back_btn)
        layout.addLayout(button_layout)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Primary Email", "Secondary Email", "Primary Contact"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.table)

        self.create_invoice_btn = QPushButton("Create Invoice for Selected Client")
        self.create_invoice_btn.clicked.connect(self.create_invoice_for_selected)
        self.create_invoice_btn.setVisible(False)
        layout.addWidget(self.create_invoice_btn)

    def load_initial_state(self):
        self.search_input.clear()
        self.table.setRowCount(0)
        self.create_invoice_btn.setVisible(False)

    def perform_search(self):
        query = self.search_input.text().strip().lower()
        if not query:
            QMessageBox.information(self, "Empty Search", "Please enter a search term.")
            return

        all_clients = self.db.get_all_clients()
        self.matching_clients = [
            c for c in all_clients if
            query in str(c[0]).lower() or  # ID
            query in (c[1] or "").lower() or  # Business Name
            query in (c[2] or "").lower() or  # Primary Email
            query in (c[7] or "").lower() or  # Secondary Email
            query in (c[4] or "").lower()  # Primary Contact Name
        ]

        self.table.setRowCount(0)
        if not self.matching_clients:
            QMessageBox.information(self, "No Matches", "No matching client records found.")
            self.create_invoice_btn.setVisible(False)
            return

        for client in self.matching_clients:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(client[0])))  # ID
            self.table.setItem(row, 1, QTableWidgetItem(client[1]))      # Name
            self.table.setItem(row, 2, QTableWidgetItem(client[2] or ""))# Primary Email
            self.table.setItem(row, 3, QTableWidgetItem(client[7] or ""))# Secondary Email
            self.table.setItem(row, 4, QTableWidgetItem(client[4] or ""))# Primary Contact

        self.create_invoice_btn.setVisible(True)

    def create_invoice_for_selected(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a client record.")
            return

        row_index = selected[0].row()
        client_data = self.matching_clients[row_index]

        # Fill invoice form with selected client
        invoice_form = self.main_window.invoice_page
        invoice_form.clear_fields()
        invoice_form.invoice_fields["Business Name"].setText(client_data[1])
        invoice_form.invoice_fields["Contact Email"].setText(client_data[2] or "")  # Primary Email
        invoice_form.invoice_fields["Street Address"].setPlainText(client_data[3] or "")
        invoice_form.set_previous_widget(self)
        self.main_window.stack.setCurrentWidget(invoice_form)
