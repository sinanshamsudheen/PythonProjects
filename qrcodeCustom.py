import qrcode
from PIL import Image

url=input("Enter ur url: ")
ver=int(input("enter version: "))
qr=qrcode.QRCode(version=ver,error_correction=qrcode.constants.ERROR_CORRECT_H,box_size=10,border=3)
qr.add_data(url)
qr.make(fit=True)
img=qr.make_image(fill_color="blue",back_color="black")
filename=input("input filename: ")
img.save(filename)
print("Saved as "+filename)