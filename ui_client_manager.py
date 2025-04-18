from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QLineEdit, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from database import Database


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
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search clients...")
        self.search_input.textChanged.connect(self.filter_clients)
        layout.addWidget(self.search_input)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Business Name", "Email", "Address"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self.load_selected_client)
        layout.addWidget(self.table)

        self.business_name_input = QLineEdit()
        self.primary_email_input = QLineEdit()
        self.contact_address_input = QTextEdit()
        self.contact_address_input.setMaximumHeight(60)
        self.primary_contact_input = QLineEdit()
        self.primary_contact_phone_input = QLineEdit()
        self.secondary_contact_name_input = QLineEdit()
        self.secondary_contact_phone_input = QLineEdit()

        for label_text, widget in [
            ("Business Name:", self.business_name_input),
            ("Contact Email:", self.primary_email_input),
            ("Contact Street Address:", self.contact_address_input),
            ("Primary Contact Name:", self.primary_contact_input),
            ("Primary Contact Phone:", self.primary_contact_phone_input),
            ("Secondary Contact Name:", self.secondary_contact_name_input),
            ("Secondary Contact Phone:", self.secondary_contact_phone_input),
        ]:
            layout.addWidget(QLabel(label_text))
            layout.addWidget(widget)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Save Changes")
        refresh_btn = QPushButton("🔄 Refresh")
        cancel_btn = QPushButton("← Back to Main Menu")

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
        self.secondary_contact_phone_input.setText(client[7] or "")

    def clear_fields(self):
        for widget in [
            self.business_name_input, self.primary_email_input,
            self.contact_address_input, self.primary_contact_input,
            self.primary_contact_phone_input, self.secondary_contact_name_input,
            self.secondary_contact_phone_input
        ]:
            if isinstance(widget, QTextEdit):
                widget.clear()
            else:
                widget.setText("")

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
            self.secondary_contact_phone_input.text(),
        )

        QMessageBox.information(self, "Success", "Client updated successfully.")
        self.all_clients = self.db.get_all_clients()
        self.display_clients(self.all_clients, highlight_client_id=self.selected_client_id)
