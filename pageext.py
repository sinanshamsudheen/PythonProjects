import PyPDF2

def extract_pages():
    """Extract pages from a user-provided PDF within a specified range and save to a new file."""
    import os
    input_pdf = input("Enter the input PDF file path: ").strip('"').strip()
    output_pdf = input("Enter the output PDF file path: ").strip('"').strip()
    start_page = int(input("Enter the start page number: "))
    end_page = int(input("Enter the end page number: "))
    
    try:
        with open(input_pdf, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            writer = PyPDF2.PdfWriter()

            # Ensure the page range is valid
            total_pages = len(reader.pages)
            start_page = max(0, start_page - 1)  # Convert to zero-based index
            end_page = min(total_pages, end_page)

            for page_num in range(start_page, end_page):
                writer.add_page(reader.pages[page_num])

            with open(output_pdf, "wb") as output_file:
                writer.write(output_file)
                print(f"Extracted pages {start_page + 1} to {end_page} and saved as {output_pdf}")
    except Exception as e:
        print(f"Error: {e}")

# Run the function
extract_pages()
