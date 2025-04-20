
#This program will remove all hyperlinks from a pdf
import fitz
import os
def remove_hyperlinks(input_pdf):
    doc = fitz.open(input_pdf)
    for page in doc:
        links = page.get_links()
        for link in links:
            page.delete_link(link)
    output_path = os.path.join(os.path.expanduser("~"), "Downloads", "Hyper")
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    list1 = os.path.split(input_pdf)
    final_output_path = os.path.join(output_path, list1[-1])
    doc.save(final_output_path)
    doc.close()
    print(f"Hyperlinks removed. Saved as: {final_output_path}")

# input_pdf = input("enter pdf path: ")
# remove_hyperlinks(input_pdf)
input_path=os.path.join(os.path.expanduser("~"), "Downloads")
for entry in os.scandir(input_path):
    if(entry.path.endswith(".pdf")):
        remove_hyperlinks(entry.path)
        os.remove(entry)
