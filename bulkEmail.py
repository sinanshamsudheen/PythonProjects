import smtplib as s
ob=s.SMTP('smtp.gmail.com',587)
ob.ehlo()
ob.starttls()
ob.login('<email id>',"<password>")

subject="Testing Python"
body="python is fun"
message="subject:{}\n\n{}".format(subject,body)

MailList=["sinanshamsudeen7@gmail.com",
          "carreersins@gmail.com"]
ob.sendmail('ilostzero@gmail.com',MailList,message)
print("mail sent!")
ob.quit()