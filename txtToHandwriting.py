import pywhatkit as pw 
# txt = input("enter the text to convert: ")
txt="""hello there!"""

pw.text_to_handwriting(txt,"resulthere.png",[0,0,138])
# pw.text_to_handwriting(txt, rgb=(196, 213, 0))

print("DONE!")
