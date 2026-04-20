# 🧾 IReS — Invoice and Reconciliation System

IReS is a modern desktop application that allows small businesses to:
- Create and manage invoices
- Automatically generate printable PDFs
- Track clients and invoice history
- Void existing invoices
- Export data for accounting and reporting

Designed with usability in mind, IReS uses a clean, professional UI built with **PyQt6** and stores all business data safely in the system’s local cache directory.

---

## 🚀 Features

- ✅ Create invoices with dynamic line items
- ✅ Save invoices to both PDF and SQLite
- ✅ Automatically cache invoice data
- ✅ Reopen, view, and void previous invoices
- ✅ View non-editable invoice data with a Find tool
- ✅ Save client contact information
- ✅ Save user preferences and logo via settings
- ✅ Cross-platform support: Windows, macOS, Linux

---

## 🛠 Installation

### 1. Clone the repository
```bash
git clone https://github.com/irvingmp6/ires.git
cd ires
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv iresEnv
source iresEnv/bin/activate  # On Windows: iresEnv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## 📂 Directory Structure

```
ires/
├── assets/              # Icons, logo, etc.
├── data/                # (Optional fallback for dev data)
├── src/                 # PyQt UI and logic modules
│   ├── ui_main_window.py
│   ├── ui_create_invoice.py
│   ├── ui_find_invoice.py
│   ├── ui_settings.py
│   ├── database.py
│   └── utils.py
├── main.py              # Application entry point
├── requirements.txt
└── README.md
```

---

## 📍 Runtime Data Location

All user-generated data is stored in your **system-specific cache folder**:

| OS      | Path |
|---------|------|
| Windows | `C:\Users\<User>\AppData\Local\Opulatec\IReS` |
| macOS   | `/Users/<User>/Library/Application Support/Opulatec/IReS` |
| Linux   | `/home/<user>/.local/share/Opulatec/IReS` |

This includes:
- SQLite database (`invoices.db`)
- PDF invoices
- Cached settings and JSON backups

---

## 🖥 Packaging

You can turn IReS into a standalone app using **PyInstaller**:
```bash
pyinstaller main.py --windowed --noconsole --icon=assets/app_icon.ico --name="IReS"
```

This will generate an executable you can distribute or add to the desktop with a shortcut.

---

## 🤝 License

MIT License. 
