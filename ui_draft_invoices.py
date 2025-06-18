from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox
)
from PyQt6.QtCore import Qt, QDate
from database import Database

class DraftInvoicesWidget(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.db = Database()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("📋 Select Draft Invoice")
        title.setProperty("title", True)
        layout.addWidget(title)

        # Table for drafts
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Invoice Number",
            "Date",
            "Business Name",
            "Contact Name",
            "Last Modified"
        ])
        
        # Set column widths
        self.table.setColumnWidth(0, 150)  # Invoice Number
        self.table.setColumnWidth(1, 100)  # Date
        self.table.setColumnWidth(2, 200)  # Business Name
        self.table.setColumnWidth(3, 150)  # Contact Name
        self.table.setColumnWidth(4, 150)  # Last Modified

        # Enable row selection
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.doubleClicked.connect(self.load_selected_draft)
        
        layout.addWidget(self.table)

        # Buttons
        button_layout = QHBoxLayout()
        
        load_btn = QPushButton("📄 Load Draft")
        delete_btn = QPushButton("🗑️ Delete Draft")
        back_btn = QPushButton("← Back to Main Menu")
        
        load_btn.clicked.connect(self.load_selected_draft)
        delete_btn.clicked.connect(self.delete_selected_draft)
        back_btn.clicked.connect(self.return_to_main_menu)
        
        button_layout.addWidget(load_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(back_btn)
        
        layout.addLayout(button_layout)

        # Load drafts when widget is initialized
        self.load_drafts()

    def load_drafts(self):
        """Load all draft invoices into the table"""
        try:
            drafts = self.db.get_invoice_drafts()
            self.table.setRowCount(0)
            
            for draft in drafts:
                row = self.table.rowCount()
                self.table.insertRow(row)
                
                self.table.setItem(row, 0, QTableWidgetItem(draft['invoice_number']))
                self.table.setItem(row, 1, QTableWidgetItem(draft['date']))
                self.table.setItem(row, 2, QTableWidgetItem(draft['business_name']))
                self.table.setItem(row, 3, QTableWidgetItem(draft['contact_name']))
                self.table.setItem(row, 4, QTableWidgetItem(draft['last_modified']))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load drafts: {str(e)}")

    def load_selected_draft(self):
        """Load the selected draft into the create invoice form"""
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a draft to load.")
            return

        try:
            row_index = selected[0].row()
            invoice_number = self.table.item(row_index, 0).text()
            
            # Get draft data from database
            draft_data = self.db.get_invoice_draft(invoice_number)
            if not draft_data:
                QMessageBox.critical(self, "Error", "Failed to load draft data.")
                return

            # Load data into create invoice form
            invoice_form = self.main_window.invoice_page
            
            # Clear line items table without clearing other fields
            invoice_form.line_items_table.setRowCount(0)
            
            # Set invoice fields
            invoice_form.invoice_fields["Invoice Number"].setText(draft_data['invoice_number'])
            invoice_form.date_edit.setDate(QDate.fromString(draft_data['date'], "yyyy-MM-dd"))
            
            # Set client info without triggering email change handler
            invoice_form.client_info["Business Name"].setText(draft_data['business_name'])
            invoice_form.client_info["Contact Name"].setText(draft_data['contact_name'])
            # Temporarily disconnect the email change signal
            invoice_form.client_info["Contact Email"].textChanged.disconnect()
            invoice_form.client_info["Contact Email"].setText(draft_data['contact_email'])
            # Reconnect the signal
            invoice_form.client_info["Contact Email"].textChanged.connect(invoice_form.handle_client_email_change)
            invoice_form.client_info["Phone Number"].setText(draft_data['phone_number'])
            invoice_form.client_info["Street Address"].setPlainText(draft_data['street_address'])
            invoice_form.selected_client_id = draft_data['customer_id']

            # Load line items
            for item in draft_data['line_items']:
                # Call add_line_item to properly initialize the row with widgets
                invoice_form.add_line_item()
                row = invoice_form.line_items_table.rowCount() - 1  # Get the index of the newly added row
                
                # Now set the values for the newly created widgets
                invoice_form.line_items_table.setItem(row, 0, QTableWidgetItem(item['description']))
                
                # Set quantity
                qty_spin = invoice_form.line_items_table.cellWidget(row, 1)
                if qty_spin:  # Check if widget exists
                    try:
                        qty_spin.setValue(int(float(item['quantity'])))  # Convert to float first in case it's a string
                    except (ValueError, TypeError):
                        qty_spin.setValue(1)  # Default to 1 if invalid value
                
                # Set unit price
                price_edit = invoice_form.line_items_table.cellWidget(row, 2)
                if price_edit:
                    price_edit.setText(str(item['unit_price']))
                
                # Set discount type
                discount_type = invoice_form.line_items_table.cellWidget(row, 3)
                if discount_type:
                    discount_type.setCurrentText(str(item['discount_type']))
                
                # Set discount value
                discount_value = invoice_form.line_items_table.cellWidget(row, 4)
                if discount_value:
                    discount_value.setText(str(item['discount_value']))
                
                # Set discount description and total
                invoice_form.line_items_table.setItem(row, 5, QTableWidgetItem(str(item.get('discount_description', ''))))
                invoice_form.line_items_table.setItem(row, 6, QTableWidgetItem(str(item.get('total', '0.00'))))

            # Update totals
            invoice_form.update_totals()
            
            # Set previous widget and switch to create invoice form
            invoice_form.set_previous_widget(self)
            self.main_window.stack.setCurrentWidget(invoice_form)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load draft: {str(e)}")

    def delete_selected_draft(self):
        """Delete the selected draft invoice"""
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "No Selection", "Please select a draft to delete.")
            return

        try:
            row_index = selected[0].row()
            invoice_number = self.table.item(row_index, 0).text()
            
            reply = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete draft invoice {invoice_number}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.db.delete_invoice_draft(invoice_number)
                self.load_drafts()  # Refresh the table
                QMessageBox.information(self, "Success", "Draft deleted successfully!")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete draft: {str(e)}")

    def return_to_main_menu(self):
        """Return to the main menu"""
        self.main_window.stack.setCurrentIndex(0) 