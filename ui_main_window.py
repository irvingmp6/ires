
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QStackedWidget, QMessageBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import os
import json

from utils import resize_image, SETTINGS_FILE, RECOMMENDED_LOGO_SIZE
from ui_create_invoice import CreateInvoiceWidget
from ui_settings import SettingsDialog
from ui_find_existing_clients import FindExistingClientWidget
from ui_select_client_type import SelectClientTypeWidget
from ui_view_client_profile import ViewClientProfileWidget
from ui_find_invoice import FindInvoiceWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Invoice Reconciliation System by Opulatec")
        self.resize(1000, 700)

        self.settings = self.load_settings()
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout(self.central_widget)

        self.logo_label = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.logo_label)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # Instantiate all views
        self.main_menu = self.create_main_menu_view()
        self.select_client_type_page = SelectClientTypeWidget(self)
        self.find_existing_client_page = FindExistingClientWidget(self)
        self.invoice_page = CreateInvoiceWidget(self)
        self.find_invoice_page = FindInvoiceWidget(self)
        self.view_existing_client_page = ViewClientProfileWidget(self)

        # Add to stack
        self.stack.addWidget(self.main_menu)                  # index 0
        self.stack.addWidget(self.select_client_type_page)   # index 1
        self.stack.addWidget(self.find_existing_client_page) # index 2
        self.stack.addWidget(self.invoice_page)              # index 3
        self.stack.addWidget(self.find_invoice_page)         # index 4
        self.stack.addWidget(self.view_existing_client_page)              # index 5

        self.display_logo()
        self.stack.setCurrentIndex(0)

    def create_main_menu_view(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel("IReS — Your Invoice and Reconciliation Specialist")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        buttons = [
            ("Create New Invoice", self.goto_client_type_selector),
            ("Find Invoice", lambda: self.stack.setCurrentWidget(self.find_invoice_page)),
            ("Manage Clients", lambda: self.stack.setCurrentWidget(self.view_existing_client_page)),
            ("Settings", self.open_settings)
        ]

        for label, handler in buttons:
            btn = QPushButton(label)
            btn.setMinimumHeight(60)
            btn.clicked.connect(handler)
            btn.setStyleSheet("font-size: 18px;")
            layout.addWidget(btn)

        return widget

    def goto_client_type_selector(self):
        self.stack.setCurrentWidget(self.select_client_type_page)

    def display_logo(self):
        logo_path = self.settings.get("logo_path")
        if logo_path and os.path.exists(logo_path):
            try:
                pixmap = resize_image(logo_path, *RECOMMENDED_LOGO_SIZE)
                self.logo_label.setPixmap(pixmap)
            except Exception as e:
                QMessageBox.critical(self, "Logo Error", f"Failed to load logo: {e}")
        else:
            self.logo_label.clear()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                QMessageBox.critical(self, "Settings Error", f"Failed to load settings: {e}")
        return {}

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save settings: {e}")

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            self.settings = dlg.settings
            self.save_settings()
            self.display_logo()
