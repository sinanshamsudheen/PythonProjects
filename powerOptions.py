import os
from tkinter import *

st=Tk()
st.title("Power Options")
st.config(bg="red")
st.geometry("500x500")

def restart():
    os.system("shutdown /r /t 1")
def restart_time():
    os.system("shutdown /r /t 20")
def logout():
    os.system("shutdown -l")
def shutdown():
    os.system("shutdown /s /t 1")

r_button=Button(st,text="Restart",font=("Times New Roman",12,"bold"),relief=RAISED,cursor="plus",command=restart)
r_button.place(x=200,y=50,height=60,width=120)

rt_button=Button(st,text="Restart time",font=("Times New Roman",8,"bold"),relief=RAISED,cursor="plus",command=restart_time)
rt_button.place(x=200,y=150,height=60,width=120)

l_button=Button(st,text="logout",font=("Times New Roman",12,"bold"),relief=RAISED,cursor="plus",command=logout)
l_button.place(x=200,y=250,height=60,width=120)

s_button=Button(st,text="shutdown",font=("Times New Roman",12,"bold"),relief=RAISED,cursor="plus",command=shutdown)
s_button.place(x=200,y=350,height=60,width=120)


st.mainloop()