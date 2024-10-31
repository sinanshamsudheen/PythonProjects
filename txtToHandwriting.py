import pywhatkit as pw

# Uncomment the next line to enable user input
# txt = input("Enter the text to convert: ")

txt = """Hello there!"""
output_path = "resulthand.png"
text_color = [0, 0, 138]  # Dark blue

# Convert text to handwriting image
pw.text_to_handwriting(txt, output_path, text_color)

print("Conversion done! Check the result at", output_path)
