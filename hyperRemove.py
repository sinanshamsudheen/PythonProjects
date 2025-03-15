#This program will remove all hyperlinks from a pdf
import fitz

def remove_hyperlinks(input_pdf):
    doc = fitz.open(input_pdf)
    for page in doc:
        links = page.get_links()
        for link in links:
            page.delete_link(link)
    output_path = "D:\IDM\Hyper"
    list1=input_pdf.split('\\')
    final_output_path=output_path+"\\"+list1[-1]
    doc.save(final_output_path)
    doc.close()
    print(f"Hyperlinks removed. Saved as: {final_output_path}")

input_pdf = input("enter pdf path: ")
remove_hyperlinks(input_pdf)
