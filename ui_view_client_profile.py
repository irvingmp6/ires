from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QLineEdit, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt
from database import Database


class ViewClientProfileWidget(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.db = Database()
        self.selected_client_id = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("👥 Client Manager")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Contact Email", "Contact Address"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self.load_selected_client)
        layout.addWidget(self.table)

        self.name_input = QLineEdit()
        self.contact_email_input = QLineEdit()
        self.contact_address_input = QTextEdit()
        self.contact_address_input.setMaximumHeight(60)

        self.primary_contact_input = QLineEdit()
        self.secondary_contact_name_input = QLineEdit()
        self.primary_contact_phone_input = QLineEdit()
        self.secondary_contact_phone_input = QLineEdit()
        self.refund_name_input = QLineEdit()

        for label_text, widget in [
            ("Client Name:", self.name_input),
            ("Contact Email:", self.contact_email_input),
            ("Contact Street Address:", self.contact_address_input),
            ("Primary Contact Name:", self.primary_contact_input),
            ("Secondary Contact Name:", self.secondary_contact_name_input),
            ("Primary Contact Phone:", self.primary_contact_phone_input),
            ("Secondary Contact Phone:", self.secondary_contact_phone_input),
            ("Refund Full Name:", self.refund_name_input),
        ]:
            layout.addWidget(QLabel(label_text))
            layout.addWidget(widget)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("💾 Save Changes")
        cancel_btn = QPushButton("← Back to Main Menu")

        save_btn.clicked.connect(self.save_client)
        cancel_btn.clicked.connect(lambda: self.main_window.stack.setCurrentIndex(0))

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.load_clients()

    def load_clients(self):
        self.table.setRowCount(0)
        clients = self.db.get_all_clients()
        for client in clients:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(client[1]))  # Name
            self.table.setItem(row, 1, QTableWidgetItem(client[2]))  # Contact Email
            self.table.setItem(row, 2, QTableWidgetItem(client[3]))  # Address
        self.selected_client_id = None
        self.clear_fields()

    def load_selected_client(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        client = self.db.get_all_clients()[row]
        self.selected_client_id = client[0]
        self.name_input.setText(client[1])
        self.contact_email_input.setText(client[2] or "")
        self.contact_address_input.setPlainText(client[3] or "")
        self.primary_contact_input.setText(client[4] or "")
        self.secondary_contact_name_input.setText(client[5] or "")
        self.primary_contact_phone_input.setText(client[6] or "")
        self.secondary_contact_phone_input.setText(client[7] or "")
        self.refund_name_input.setText(client[8] or "")

    def clear_fields(self):
        self.name_input.clear()
        self.contact_email_input.clear()
        self.contact_address_input.clear()
        self.primary_contact_input.clear()
        self.secondary_contact_name_input.clear()
        self.primary_contact_phone_input.clear()
        self.secondary_contact_phone_input.clear()
        self.refund_name_input.clear()

    def save_client(self):
        if self.selected_client_id is None:
            QMessageBox.warning(self, "No Selection", "Please select a client to edit.")
            return

        self.db.update_client(
            self.selected_client_id,
            self.name_input.text(),
            self.contact_email_input.text(),
            self.contact_address_input.toPlainText(),
            self.primary_contact_input.text(),
            self.secondary_contact_name_input.text(),
            self.primary_contact_phone_input.text(),
            self.secondary_contact_phone_input.text(),
            self.refund_name_input.text()
        )

        QMessageBox.information(self, "Success", "Client updated successfully.")
        self.load_clients()
