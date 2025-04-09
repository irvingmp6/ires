from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog,
    QHBoxLayout, QCheckBox, QMessageBox
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import os

from utils import resize_image, SUPPORTED_IMAGE_FORMATS

class SettingsDialog(QDialog):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.setWindowTitle("Settings")
        self.setMinimumSize(400, 300)
        self.settings = main_window.settings
        self.parent_window = main_window

        self.logo_path = self.settings.get("logo_path", "")
        self.enable_logging = self.settings.get("enable_logging", False)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Logo Path
        logo_label = QLabel("Logo Path:")
        self.logo_entry = QLineEdit(self.logo_path)
        self.logo_entry.setReadOnly(True)

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_logo)

        logo_layout = QHBoxLayout()
        logo_layout.addWidget(self.logo_entry)
        logo_layout.addWidget(browse_btn)

        layout.addWidget(logo_label)
        layout.addLayout(logo_layout)

        # Thumbnail Display
        self.thumbnail = QLabel()
        self.thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.thumbnail)
        self.update_thumbnail()

        # Logging checkbox
        self.logging_checkbox = QCheckBox("Enable Logging")
        self.logging_checkbox.setChecked(self.enable_logging)
        layout.addWidget(self.logging_checkbox)

        # Save and Cancel
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def browse_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Logo Image",
            "",
            "Image Files (*.png *.gif)"
        )
        if file_path:
            self.logo_path = file_path
            self.logo_entry.setText(file_path)
            self.update_thumbnail()

    def update_thumbnail(self):
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                pixmap = resize_image(self.logo_path, 150, 75)
                self.thumbnail.setPixmap(pixmap)
            except Exception as e:
                QMessageBox.warning(self, "Image Error", f"Could not load thumbnail: {e}")
        else:
            self.thumbnail.clear()

    def save_settings(self):
        # Validate file
        if self.logo_path:
            ext = os.path.splitext(self.logo_path)[1].lower()
            if ext not in [".png", ".gif"]:
                QMessageBox.warning(self, "Invalid Logo", "Only PNG or GIF logos are supported.")
                return
            if not os.path.exists(self.logo_path):
                QMessageBox.warning(self, "Missing File", "Selected logo does not exist.")
                return
            self.settings["logo_path"] = self.logo_path
        else:
            self.settings.pop("logo_path", None)

        self.settings["enable_logging"] = self.logging_checkbox.isChecked()
        self.parent_window.save_settings()
        self.accept()
