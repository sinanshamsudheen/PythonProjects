#This program will remove all hyperlinks from a pdf
import fitz

def remove_hyperlinks(input_pdf, output_pdf):
    doc = fitz.open(input_pdf)
    
    for page in doc:
        links = page.get_links()
        for link in links:
            page.delete_link(link)  # Remove each hyperlink

    doc.save(output_pdf)
    doc.close()
    print(f"Hyperlinks removed. Saved as: {output_pdf}")

# Example usage
input_pdf = input("enter pdf path: ")
output_pdf = r"D:\IDM\Hyper\output.pdf"
remove_hyperlinks(input_pdf, output_pdf)
