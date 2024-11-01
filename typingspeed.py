import time
import random as r
import tkinter as tk

st=tk.Tk()
st.geometry("1000x500")

words = [
    "cat", "dog", "jumped", "gracefully", "sunny", "backyard",
    "sudden", "gust", "wind", "scattered", "papers", "park",
    "Sarah", "laughed", "dipped", "toes", "cool", "water",
    "coffee", "shop", "buzzed", "chatter", "rainy", "Tuesday",
    "afternoon", "rainbow", "appeared", "mountain", "sun",
    "began", "set", "clock", "struck", "midnight", "silence",
    "room", "grew", "heavier", "James", "found", "small",
    "colorful", "pebble", "beach", "morning", "walk",
    "curious", "squirrel", "watched", "tree", "children",
    "played", "below", "aroma", "fresh", "bread",
    "filled", "air", "bakery", "opened","the","in","on","as","will"
]
def mistake(test,user_input):
    error=0
    for i in range(len(test)):
        try:
            if test[i]!=user_input[i]:
                error=error+1
        except:
                error=error+1
    return error
def speed_check(time_s,time_e,user_input):
     time_delay=time_e-time_s
     num_chars=len(user_input)
     num_words=num_chars/5
     speed=(num_words/time_delay)*60
     return round(speed)
     

test_list=[ ' '.join(r.choice(words) for _ in range(10))]

test=r.choice(test_list)
st.title("Typing speed Test")

time1=time.time()
label=tk.Label(st,text=f"Type this: {test}",font=("Arial",15))
label.pack()

user_input=tk.Text(st,height=5,width=30)
user_input.pack()

time2=time.time()
def calculate_results(event=None):
     time2=time.time()
     text_input=user_input.get("1.0","end-1c")
     results_label.config(text=f"speed:{speed_check(time1,time2,text_input)} WPM \nError:{mistake(test,text_input)}",font=("Arial",30))


submit_button=tk.Button(st,text="Submit",cursor="plus",command=calculate_results)
submit_button.pack(pady=20)

results_label=tk.Label(st,text="")
results_label.pack()
st.bind('<Return>',calculate_results)
st.mainloop()