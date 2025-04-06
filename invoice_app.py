import json
import math
import os
import tkinter as tk

from decimal import Decimal
from tkinter import ttk, filedialog, messagebox, simpledialog

from PIL import Image, ImageTk


SETTINGS_FILE = 'settings.json'
SUPPORTED_IMAGE_FORMATS = [("PNG files", "*.png"), ("GIF files", "*.gif")]
RECOMMENDED_LOGO_SIZE = (300, 150)  # Width x Height in pixels
MAX_LOGO_WIDTH = 200
MAX_LOGO_HEIGHT = 200


class InvoiceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Invoice Applications")

        # **Removed Fixed Window Size**
        # Allow resizing in all directions
        self.root.resizable(True, True)

        self.settings = self.load_settings()
        self.logo_image = None # To prevent garbage collection

        # Create a container frame to hold all other frames
        self.container = ttk.Frame(self.root)
        self.container.pack(fill=tk.BOTH, expand=True)

        # Initialize all frames
        self.frames = {}
        for F in (MainFrame, CreateInvoiceFrame):
            frame = F(parent=self.container, controller=self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Initialize Settings as a separate Toplevel window
        self.settings_window = None

        self.show_frame(MainFrame)

        # Define custom styles
        self.define_styles()

    def define_styles(self):
        style = ttk.Style()
        # Ensure a default theme is set for better stlying consitency
        style.theme_use('clam') # Options include 'default', 'clam', 'alt', 'classic', 'etc'.
        # Define a large button style
        style.configure('Large.TButton', font=('Helvetica', 16, 'bold'), padding=10)

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                return settings
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load settings: {e}")
                return {}
        else:
            return {}

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def show_frame(self, frame_class):
        frame = self.frames[frame_class]
        frame.tkraise()
        if frame_class == MainFrame:
            frame.display_logo()

    def open_settings(self):
        if self.settings_window and self.settings_window.winfo_exists():
            # If settings window is already open, bring it to the front
            self.settings_window.lift()
            return
        self.settings_window = SettingsWindow(self)
        self.settings_window.grab_set() # Make the settings window modal

    def refresh_main_frame(self):
        # Refresh the main frame (e.g., after changing the logo)
        self.show_frame(MainFrame)

    def not_implemented(self):
        messagebox.showinfo("Info", "This feature is not yet implemented.")

class MainFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding="10")
        self.controller = controller
        self.logo_image = None # Reference to prevent garbage collection

        # Display Logo if set
        self.logo_label = ttk.Label(self)
        self.logo_label.pack(pady=10)

        # Title
        title = ttk.Label(self, text="Invoice Application", font=("Helvetica", 24, "bold"))
        title.pack(pady=10)

        # Buttons Frame
        buttons_frame = ttk.Frame(self)
        buttons_frame.pack(pady=20, fill=tk.BOTH, expand=True)

        # Configure buttons_frame to stack buttons vertically
        buttons_frame.columnconfigure(0, weight=1)

        # Buttons using the 'Large.TButton' style
        create_invoice_btn = ttk.Button(buttons_frame, text="Create New Invoice",
                                        command=lambda: controller.show_frame(CreateInvoiceFrame),
                                        style='Large.TButton')
        create_invoice_btn.pack(fill=tk.X, pady=10, padx=50)

        update_invoice_btn = ttk.Button(buttons_frame, text="Update Existing Invoice",
                                        command=controller.not_implemented,
                                        style='Large.TButton')
        update_invoice_btn.pack(fill=tk.X, pady=10, padx=50)

        create_report_btn = ttk.Button(buttons_frame, text="Create Report",
                                        command=controller.not_implemented,
                                        style='Large.TButton')
        create_report_btn.pack(fill=tk.X, pady=10, padx=50)

        settings_btn = ttk.Button(buttons_frame, text="Settings",
                                        command=controller.open_settings,
                                        style='Large.TButton')
        settings_btn.pack(fill=tk.X, pady=10, padx=50)

    def display_logo(self):
        logo_path = self.controller.settings.get("logo_path")
        if logo_path and os.path.exists(logo_path):
            try:
                image = Image.open(self.controller.settings['logo_path'])
                image.thumbnail(RECOMMENDED_LOGO_SIZE, Image.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(image)
                self.logo_label.configure(image=self.logo_image)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load logo: {e}")


    def resize_image(image_path, max_width=300, max_height=150):
        try:
            image = Image.open(image)
            image.thumbnail((max_width, max_height), Image.LANCZOS)
            return ImageTk.PhotoImage(image)
        except Exception as e:
            messagebox.showerror("Image Error", f"Could not resize logo: {e}")
            return None

class CreateInvoiceFrame(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, padding="10")
        self.controller = controller

        # Title
        title = ttk.Label(self, text="Create New Invoice", font=("Helvetica", 20, "bold"))
        title.grid(row=0, column=0, columnspan=4, pady=10, sticky="w")

        # Define labels and entry fields
        labels = ["Invoice Number", "Date", "Client Name", "Client Address"]
        self.entries = {}

        for idx, label_text in enumerate(labels, start=1):
            label = ttk.Label(self, text=label_text + ":")
            label.grid(row=idx, column=0, sticky=tk.W, pady=5, padx=5)

            entry = ttk.Entry(self, width=50)
            entry.grid(row=idx, column=1, pady=5, padx=5, sticky="w")
            self.entries[label_text] = entry

        # Line Items Section
        line_items_label = ttk.Label(self, text="Line Items:", font=("Helvetica", 14, "bold"))
        line_items_label.grid(row=idx + 1, column=0, pady=(20, 10), sticky="w")

        # Treeview for Line Items
        columns = ("Description", "Quantity", "Unit Price", "Total")
        self.tree = ttk.Treeview(self, columns=columns, show='headings', selectmode='browse')
        for col in columns:
            self.tree.heading(col, text=col)
            if col == "Description":
                self.tree.column(col, width=300)
            else:
                self.tree.column(col, width=100, anchor=tk.CENTER)
        self.tree.grid(row=idx + 2, column=0, columnspan=4, pady=5, padx=5, sticky="nsew")

        # Configure scrollbar for the treeview
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=idx + 2, column=4, sticky='ns')

        # Button to Add and Remove Line Items
        add_button = ttk.Button(self, text="Add Item", command=self.add_item)
        add_button.grid(row=idx + 3, column=0, pady=10, padx=5, sticky="w")

        remove_button = ttk.Button(self, text="Remove Selected Item", command=self.remove_item)
        remove_button.grid(row=idx + 3, column=1, pady=10, padx=5, sticky="w")

        # Total Amount Display
        self.total_var = tk.StringVar(value="0.00") # Directly defined as an instance variable
        total_label = ttk.Label(self, text="Total Amount: ")
        total_label.grid(row=idx + 4, column=2, pady=10, padx=5, sticky="e")

        total_amount_label = ttk.Label(self, textvariable=self.total_var, font=("Helvetica", 12, "bold"))
        total_amount_label.grid(row=idx + 4, column=3, pady=10, padx=5, sticky="w")

        # Buttons Frame
        buttons_frame = ttk.Frame(self)
        buttons_frame.grid(row=idx + 5, column=0, columnspan=4, pady=20)

        # Configure grid for button_frame
        for i in range(5):
            buttons_frame.columnconfigure(i, weight=1, pad=5)

        # Buttons
        create_btn = ttk.Button(buttons_frame, text="Create", command=self.create_invoice)
        create_btn.grid(row=0, column=0, padx=5, sticky="nsew")

        save_btn = ttk.Button(buttons_frame, text="Save for Later", command=self.save_for_later)
        save_btn.grid(row=0, column=1, padx=5, sticky="nsew")

        import_btn = ttk.Button(buttons_frame, text="Import Saved Invoice", command=self.import_invoice)
        import_btn.grid(row=0, column=2, padx=5, sticky="nsew")

        clear_btn = ttk.Button(buttons_frame, text="Clear", command=self.clear_fields)
        clear_btn.grid(row=0, column=3, padx=5, sticky="nsew")

        cancel_btn = ttk.Button(buttons_frame, text="Cancel", command=self.cancel)
        cancel_btn.grid(row=0, column=4, padx=5, sticky="nsew")

        # Bind double-click on treeview to edit items
        self.tree.bind("<Double-1>", self.edit_item)

        # Configure grid weights for responsiveness
        self.grid_rowconfigure(idx + 2, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def add_item(self):
        # Prompt user to enter item details
        item_description = simpledialog.askstring("Input", "Entry Item Description:", parent=self)
        if item_description is None or item_description.strip() == "":
            return # User cancelled or entered empty description

        quantity_input = simpledialog.askstring("Input", "Entry Quantity:", parent=self)
        if quantity_input is None or quantity_input.strip() == "":
            return

        unit_price_input = simpledialog.askstring("Input", "Enter Unit Price:", parent=self)
        if unit_price_input is None or unit_price_input.strip() == "":
            return

        # Validate quantity and unit price
        try:
            quantity = float(quantity_input)
            unit_price = float(unit_price_input)
            if quantity <= 0 or unit_price < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Validation Error",
                                    "Quantity must be a positive number and Unit Price must be a non-negative number.")
            return

        total = Decimal(quantity_input) * Decimal(unit_price_input)

        # Insert the item into the treeview
        self.tree.insert("", "end", values=(item_description, f"{quantity}", f"{unit_price}", f"{total}"))

        # Update total amount
        self.update_total_amount()

    def remove_item(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select an item to remove.")
            return
        self.tree.delete(selected_item)
        self.update_total_amount()

    def edit_item(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        item = self.tree.item(selected_item)
        values = item['values']

        # Prompt user to edit item details
        new_description = simpledialog.askstring("Input", "Edit Item Description:", initialvalue=values[0], parent=self)
        if new_description is None or new_description.strip() == "":
            return

        new_quantity_input = simpledialog.askstring("Input", "Edit Quantity:", initialvalue=values[1], parent=self)
        if new_quantity_input is None or new_quantity_input.strip() == "":
            return

        new_unit_price_input = simpledialog.askstring("Input", "Edit Unit Price:", initialvalue=values[2], parent=self)
        if new_unit_price_input is None or new_unit_price_input.strip() == "":
            return

        # Validate quanitity and unit price
        try:
            new_quantity = float(new_quantity_input)
            new_unit_price = float(new_unit_price_input)
            if new_quantity <= 0 or new_unit_price < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Validation Error",
                                    "Quantity must be a positive number and Unit Price must be a non-negative number.")
            return

        new_total = Decimal(new_quantity_input) * Decimal(new_unit_price_input)

        # Update the item in the treeview
        self.tree.item(selected_item, values=(new_description, f"{new_quantity}", f"{new_unit_price:.2f}",
                                                f"{new_total:.2f}"))

        # Update total amount
        self.update_total_amount()

    def update_total_amount(self):
        total = Decimal("0")
        print(total)
        for child in self.tree.get_children():
            item_total = Decimal(self.tree.item(child)['values'][3])
            total += item_total
        self.total_var.set(f"{total:.2f}")

    def create_invoice(self):
        data = self.get_entries()
        if not self.validate_entries(data):
            return

        # Contruct the invoice data with line items
        invoice_data = {
            "Invoice Number": data["Invoice Number"],
            "Date": data["Date"],
            "Client Name": data["Client Name"],
            "Client Address": data["Client Address"],
            "Line Items": data["Line Items"],
            "Total Amount": self.total_var.get()
        }

        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
            title="Save Invoice as JSON"
        )
        if save_path:
            try:
                with open(save_path, 'w') as f:
                    json.dump(invoice_data, f, indent=4)
                messagebox.showinfo("Success", f"Invoice saved as {save_path}")
                self.clear_fields()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save JSON: {e}")

    def save_for_later(self):
        data = self.get_entries()
        # if not self.validate_entries(data):
        #     return

        # Construct the invoice data with line items
        invoice_data = {
            "Invoice Number": data["Invoice Number"],
            "Date": data["Date"],
            "Client Name": data["Client Name"],
            "Client Address": data["Client Address"],
            "Line Items": data["Line Items"],
            "Total Amount": self.total_var.get()
        }

        # Customize the save path or naming convention for "Save for Later"
        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
        title="Save Invoice for Later as JSON"
        )
        if save_path:
            try:
                with open(save_path, 'w') as f:
                    json.dump(invoice_data, f, indent=4)
                messagebox.showinfo("Success", f"Invoice details saved for later as {save_path}")
                self.clear_fields()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save JSON: {e}")

    def import_invoice(self):
        file_path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")],
        title="Import Invoice from JSON"
    )
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    invoice_data = json.load(f)

                # Populate the main fields
                self.entries["Invoice Number"].delete(0, tk.END)
                self.entries["Invoice Number"].insert(0, invoice_data.get("Invoice Number", ""))

                self.entries["Date"].delete(0, tk.END)
                self.entries["Date"].insert(0, invoice_data.get("Date", ""))

                self.entries["Client Name"].delete(0, tk.END)
                self.entries["Client Name"].insert(0, invoice_data.get("Client Name", ""))

                self.entries["Client Address"].delete(0, tk.END)
                self.entries["Client Address"].insert(0, invoice_data.get("Client Address", ""))

                # Clear existing line items
                for child in self.tree.get_children():
                    self.tree.delete(child)

                # Populate line items
                for item in invoice_data.get("Line Items", []):
                    description = item.get("Description", "")
                    quantity = item.get("quantity", "0")
                    unit_price = item.get("Unit Price", "0.00")
                    total = item.get("Total", "0.00")
                    self.tree.insert("", values=(description, quantity, unit_price, total))

                # Update total amount
                self.update_total_amount()

                messagebox.showinfo("Success", f"Invoice details loaded from {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load JSON: {e}")

    def clear_fields(self):
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        for child in self.tree.get_children():
            self.tree.delete(child)
        self.total_var.set("0.00")

    def get_entries(self):
        # Father main fields
        data = {
        "Invoice Number": self.entries["Invoice Number"].get(),
        "Date": self.entries["Date"].get(),
        "Client Name": self.entries["Client Name"].get(),
        "Client Address": self.entries["Client Address"].get(),
        "Line Items": []
        }

        # Gather line items from the treeview
        for child in self.tree.get_children():
            item = self.tree.item(child)['values']
            line_item = {
                "Description": item[0],
                "Quantity": item[1],
                "Unit Price": item[2],
                "Total": item[3]
            }
            data["Line Items"].append(line_item)

        return data

    def validate_entries(self, data):
        required_fields = [
        "Invoice Number",
        "Date",
        "Client Name",
        "Line Items"
    ]
        missing = [field for field in required_fields if not data.get(field)]
        if missing:
            messagebox.showwarning(
                "Validation Error",
                f"Please fill out the following fields {', '.join(missing)}"
            )
            return False

        # Ensure there is at least one line item
        if not data["Line Items"]:
            messagebox.showwarning(
                "Validation Error",
                "Please add at least one line item to the invoice."
            )
            return False

        # Validate each line item
        for idx, item in enumerate(data["Line Items"], start=1):
            description = item.get("Description", "")
            quantity = item.get("Quantity", "0")
            unit_price = item.get("Unit Price", "0.00")

            if not description.strip():
                messagebox.showwarning(
                    "Validation Error",
                    f"Line item {idx} is missing a description."
                )
                return False

            try:
                quantity = Decimal(quantity)
                unit_price = Decimal(unit_price)
                if quantity <= 0 or unit_price < 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning(
                    "Validation Error",
                    f"Line item {idx} has invalid quantity or unit_price. Ensure they are positive numbers."
                )
                return False

        return True

    def cancel(self):
        self.clear_fields()
        self.controller.show_frame(MainFrame)

class SettingsWindow(tk.Toplevel):
    def __init__(self, controller):
        super().__init__(controller.root)
        self.controller = controller
        self.title("Settings")
        # Set initial size (can be adjusted or removed for dynamic sizing)
        self.geometry("500x350")
        # Allow resizing
        self.resizable(True, True)
        self.grab_set() # Make the settings window modal

        self.logo_image = None # To prevent garbage collection
        self.thumbnail_image = None # For thumnail display

        self.create_widgets()

    def create_widgets(self):
        # Logo Section
        logo_frame = ttk.Frame(self, padding="10")
        logo_frame.pack(fill=tk.BOTH, expand=True)

        logo_label = tk.Label(logo_frame, text="Logo:")
        logo_label.grid(row=0, column=0, sticky=tk.W, pady=10, padx=10)

        self.logo_path_var = tk.StringVar(value=self.controller.settings.get('logo_path', ''))
        self.logo_entry = ttk.Entry(logo_frame, textvariable=self.logo_path_var, width=40, state='readonly')
        self.logo_entry.grid(row=0, column=1, pady=10, padx=10)

        browse_button = ttk.Button(logo_frame, text="Browse...", command=self.browse_logo, style='Large.TButton')
        browse_button.grid(row=0, column=2, pady=10, padx=10)

        # Optional: Display current logo thumnail
        self.thumbnail_label = ttk.Label(logo_frame)
        self.thumbnail_label.grid(row=1, column=0, columnspan=3, pady=10)

        self.display_thumbnail()

        # Save and Cancel Buttons
        buttons_frame = ttk.Frame(logo_frame)
        buttons_frame.grid(row=1, column=0, columnspan=3, pady=20)

        save_btn = ttk.Button(buttons_frame, text="Save", command=self.save_settings, style='Large.TButton')
        save_btn.pack(side=tk.LEFT, padx=10)

        cancel_btn = ttk.Button(buttons_frame, text="Cancel", command=self.destroy, style='Large.TButton')
        cancel_btn.pack(side=tk.LEFT, padx=10)

    def browse_logo(self):
        file_path = filedialog.askopenfilename(
            title="Select Logo",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
        )
        if file_path:
            self.controller.settings['logo_path'] = file_path
            resized_logo = self.resize_image(file_path)
            if resized_logo:
                self.logo_image = resized_logo
                self.thumbnail_label.configure(image=self.logo_image)

    def display_thumbnail(self):
        # Display a resized version of the logo
        logo_path = self.logo_path_var.get()
        if logo_path and os.path.exists(logo_path):
            try:
                # Load the image using Tkinter's PhotoImage
                image = self.resize_image(logo_path, 100, 100)
                if image:
                    self.thumbnail_image = image
                    self.thumbnail_label.configure(image=self.thumbnail_image)
            except Exception as e:
                # If image loading fails, remove thumbnail
                self.thumbnail_label.configure(image='')
                messagebox.showerror("Error", f"Failed to load logo thumbnail: {e}")
        else:
            self.thumbnail_label.configure(image='')

    def resize_image(self, image_path, max_width=300, max_height=150):
        try:
            image = Image.open(image_path)
            # Check dimensions
            if image.size != RECOMMENDED_LOGO_SIZE:
                messagebox.showwarning(
                    "Logo Size Warning",
                    f"Logo should be exactly {RECOMMENDED_LOGO_SIZE[0]}x{RECOMMENDED_LOGO_SIZE[1]} pixels.\n"
                    "Please resize before uploading."
                )
                return
            image.thumbnail((max_width, max_height), Image.LANCZOS)
            return ImageTk.PhotoImage(image)
        except Exception as e:
            messagebox.showerror("Image Error", f"Could not resize logo: {e}")
            return None

    def save_settings(self):
        logo_path = self.logo_path_var.get()
        if logo_path and not os.path.exists(logo_path):
            messagebox.showerror("Error", "Selected logo file does not exist.")
            return

        if logo_path:
            # Ensure the image is in a supported format
            _, ext = os.path.splitext(logo_path)
            ext = ext.lower()
            if ext not in ['.png', '.gif']:
                messagebox.showerror("Error", "Unsupported image format. Please select a PNG or GIF file.")
                return
            self.controller.settings['logo_path'] = logo_path
        else:
            # If no logo is selected, remove the logo_path from settings
            self.controller.settings.pop('logo_path', None)

        self.controller.save_settings()
        self.controller.refresh_main_frame()
        self.destroy()
        messagebox.showinfo("Success", "Settings have been saved successfully.")

def main():
    root = tk.Tk()
    app = InvoiceApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()