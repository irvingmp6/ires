import os
from PyQt6.QtGui import QPixmap
from PIL import Image
from appdirs import user_data_dir

APP_NAME = "IReS"
APP_AUTHOR = "Opulatec"

# Cross-platform app data directory
APP_DATA_DIR = user_data_dir(APP_NAME, APP_AUTHOR)
os.makedirs(APP_DATA_DIR, exist_ok=True)

# Key paths
DB_PATH = os.path.join(APP_DATA_DIR, "invoices.db")
PDF_DIR = os.path.join(APP_DATA_DIR, "pdf")
JSON_DIR = os.path.join(APP_DATA_DIR, "json")
SETTINGS_FILE = os.path.join(APP_DATA_DIR, "settings.json")
RECOMMENDED_LOGO_SIZE = (300, 150)
SUPPORTED_IMAGE_FORMATS = [("PNG files", "*.png"), ("GIF files", "*.gif")]

# Ensure subfolders exist
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)

def resize_image(path, width, height):
    """Resize an image and return a QPixmap."""
    if not os.path.exists(path):
        raise FileNotFoundError("Image path does not exist")

    image = Image.open(path)
    image.thumbnail((width, height), Image.LANCZOS)
    temp_path = os.path.join(APP_DATA_DIR, "_temp_resized_logo.png")
    image.save(temp_path)
    return QPixmap(temp_path)
