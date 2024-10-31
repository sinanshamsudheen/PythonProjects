import re
email_condition="^[a-z]+[\._]?+[a-z 0-9]+[@]\w+[.]\w{3,4}$"
# here '^' is used to start at the begin, '+' joins the strings, 
# '\w' is used to search,'\w{3,4}$' is used to search from behind.
user_email=input("Enter your email : ")

if re.search(email_condition,user_email):
    print("Right email!")
else:
    print("Wrong email!")
