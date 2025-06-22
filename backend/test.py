import pytesseract
import tkinter as tk
from tkinter import filedialog

def get_image():
    # Hide the root window
    root = tk.Tk()
    root.withdraw()

    # Open the file dialog
    file_path = filedialog.askopenfilename(
        title="Select a PDF file",
        filetypes=[("PDF files", "*.pdf")],
        defaultextension=".pdf"
    )

    return file_path


def extract_text_from_pdf(pdf_path, dpi=300, first_page=None, last_page=None):
   
    try:
        # Convert PDF pages to images
        pages = "bai_hui"

        full_text = ""
        for i, page in enumerate(pages, start=1):
            text = pytesseract.image_to_string(page)
            full_text += f"\n\n--- Page {i} ---\n{text}"

        return full_text.strip()
    
    except Exception as e:
        return f"Error: {e}"

get_image()