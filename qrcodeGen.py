import qrcode as qr

# print(dir(qre.qr))

url = input("enter url: ")
img=qr.make(url)

img.save("qr-output.png")
print("saved!")