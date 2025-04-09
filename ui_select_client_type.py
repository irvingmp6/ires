from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel
)
from PyQt6.QtCore import Qt

class SelectClientTypeWidget(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Who is this invoice for?")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        new_client_btn = QPushButton("➕ New Client")
        existing_client_btn = QPushButton("👤 Existing Client")

        new_client_btn.setMinimumHeight(50)
        existing_client_btn.setMinimumHeight(50)

        new_client_btn.clicked.connect(self.go_to_new_invoice)
        existing_client_btn.clicked.connect(self.go_to_existing_client_search)

        layout.addWidget(new_client_btn)
        layout.addWidget(existing_client_btn)

    def go_to_new_invoice(self):
        self.main_window.invoice_page.restore_cached_data()
        self.main_window.stack.setCurrentWidget(self.main_window.invoice_page)

    def go_to_existing_client_search(self):
        self.main_window.find_existing_client_page.load_initial_state()
        self.main_window.stack.setCurrentWidget(self.main_window.find_existing_client_page)
