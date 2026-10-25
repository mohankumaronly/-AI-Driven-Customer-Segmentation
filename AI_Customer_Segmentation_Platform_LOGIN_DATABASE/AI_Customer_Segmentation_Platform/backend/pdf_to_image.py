import fitz
import os

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

PDF_FILE = os.path.join(
    BASE_DIR,
    "powerbi",
    "AI_Customer_Segmentation_Dashboard.pdf"
)

OUTPUT_FILE = os.path.join(
    BASE_DIR,
    "frontend",
    "static",
    "powerbi_dashboard.png"
)

pdf = fitz.open(PDF_FILE)

page = pdf[0]

pix = page.get_pixmap(
    matrix=fitz.Matrix(2, 2)
)

pix.save(OUTPUT_FILE)

pdf.close()

print("Power BI dashboard image created successfully.")
print(OUTPUT_FILE)