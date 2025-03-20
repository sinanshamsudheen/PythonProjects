import fitz
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os
import io

def ocr_and_make_text_selectable(input_pdf, output_pdf_folder):
    doc = fitz.open(input_pdf)
    pages = convert_from_path(input_pdf)  # Convert PDF pages to images
    new_pdf = fitz.open()

    # Extract filename from path
    pdf_filename = os.path.basename(input_pdf)
    final_output_path = os.path.join(output_pdf_folder, pdf_filename)

    for i, image in enumerate(pages):
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format="PNG")  # Convert PIL Image to byte stream
        img_bytes = img_byte_arr.getvalue()
        
        # Perform OCR
        text = pytesseract.image_to_string(image)

        # Create new PDF page and insert OCR text
        pdf_page = new_pdf.new_page(width=doc[i].rect.width, height=doc[i].rect.height)

        # Overlay extracted text on the page
        y_position = 20  # Start text from 20px margin from top
        for line in text.split("\n"):
            pdf_page.insert_text((20, y_position), line, fontsize=12, overlay=True)
            y_position += 15  # Adjust line spacing

        # Insert original image as background
        img_pixmap = fitz.Pixmap(img_bytes)  # Convert image bytes to Pixmap
        pdf_page.insert_image(pdf_page.rect, pixmap=img_pixmap)

    new_pdf.save(final_output_path)
    new_pdf.close()
    print(f"Selectable text PDF saved at: {final_output_path}")

# Example usage
input_pdf = input("Enter PDF path: ").strip('"')  # Remove extra quotes if user pastes path
output_pdf_folder = "D:\\IDM\\Hyper\\"
ocr_and_make_text_selectable(input_pdf, output_pdf_folder)
