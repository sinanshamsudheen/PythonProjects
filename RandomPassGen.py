import random
import string

strr=string.ascii_letters + string.digits + string.punctuation
password=""
pass_list=[]
i=0
while(len(password)!=12):
    password=password+random.choice(strr)
    pass_list.append(random.choice(strr))
    i+=1

print("your random password is:",password)
print("your random password(list) is:",pass_list)