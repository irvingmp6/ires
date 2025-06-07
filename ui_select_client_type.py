from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel
)
from PyQt6.QtCore import Qt

class SelectClientTypeWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Who is this invoice for?")
        title.setProperty("title", True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Buttons
        new_client_btn = QPushButton("➕ New Client")
        new_client_btn.setToolTip("Create an invoice for a new client")
        new_client_btn.clicked.connect(self.create_new_client)
        new_client_btn.setMinimumHeight(60)
        layout.addWidget(new_client_btn)

        existing_client_btn = QPushButton("💼 Existing Client")
        existing_client_btn.setToolTip("Create an invoice for an existing client")
        existing_client_btn.clicked.connect(self.find_existing_client)
        existing_client_btn.setMinimumHeight(60)
        layout.addWidget(existing_client_btn)

        draft_btn = QPushButton("✏️ Resume Draft")
        draft_btn.setToolTip("Continue working on a previously saved draft invoice")
        draft_btn.clicked.connect(self.load_draft)
        draft_btn.setMinimumHeight(60)
        layout.addWidget(draft_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.return_to_main_menu)
        cancel_btn.setMinimumHeight(60)
        layout.addWidget(cancel_btn)

        # Apply button styles
        for btn in [new_client_btn, existing_client_btn, draft_btn, cancel_btn]:
            btn.setStyleSheet("font-size: 18px;")

    def create_new_client(self):
        self.main_window.stack.setCurrentWidget(self.main_window.invoice_page)

    def find_existing_client(self):
        self.main_window.stack.setCurrentWidget(self.main_window.find_existing_client_page)

    def load_draft(self):
        if not hasattr(self.main_window, 'draft_invoices_page'):
            from ui_draft_invoices import DraftInvoicesWidget
            self.main_window.draft_invoices_page = DraftInvoicesWidget(self.main_window)
            self.main_window.stack.addWidget(self.main_window.draft_invoices_page)
        else:
            self.main_window.draft_invoices_page.load_drafts()  # Refresh the list
        self.main_window.stack.setCurrentWidget(self.main_window.draft_invoices_page)

    def return_to_main_menu(self):
        self.main_window.stack.setCurrentIndex(0)
