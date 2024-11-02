from tkinter import *
import speedtest as stest

def speed():
    sp=stest.Speedtest()
    sp.get_servers()
    down=str(round((sp.download()/10**6),3))+" Mbps"
    up=str(round((sp.upload()/10**6),3))+" Mbps"
    lab_down.config(text=down)
    lab_up.config(text=up)

st=Tk()
st.title("Internet Speed Tester")
st.geometry("400x700")
lab=Label(st,text="Internet Speed Test",font=("Arial",20,"bold","underline"),fg="red")
lab.place(x=50,y=50,height=30,width=300)

lab=Label(st,text=">>Download Speed<<",font=("Arial",20,"bold"),fg="green")
lab.place(x=50,y=150,height=30,width=300)

lab_down=Label(st,text="00",font=("Arial",20,"bold"),fg="black")
lab_down.place(x=50,y=200,height=30,width=300)

lab=Label(st,text=">>Upload Speed<<",font=("Arial",20,"bold"),fg="purple")
lab.place(x=50,y=350,height=30,width=300)

lab_up=Label(st,text="00",font=("Arial",20,"bold"),fg="black")
lab_up.place(x=50,y=400,height=30,width=300)

button=Button(st,text="Check speed",font=("Arial",30,"bold"),fg="blue",relief=RAISED,command=speed)
button.place(x=70,y=550,height=50,width=260)

st.mainloop()