import webbrowser
import pyjokes
import datetime
import speech_recognition as sr
import pyttsx3
import sys
import time
import os

def sptext():
    recognizer=sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source);
        audio=recognizer.listen(source)
        try:
            print("Recognizing..")
            data=recognizer.recognize_google(audio)
            print(data)
            return data
        except sr.UnknownValueError:
            print("sorry! couldn't recognize!")
            return ""
def speech(x):
    engine=pyttsx3.init()
    voices=engine.getProperty('voices')
    engine.setProperty('voice',voices[1].id)
    rate=engine.getProperty('rate')
    engine.setProperty('rate',150)
    engine.say(x)
    engine.runAndWait()

if __name__=='__main__':
    while(True):

        command=sptext().lower()

        if command=="hey google":
            speech("   hello sinan! how can i help you today?")
        elif "time" in command:
            time=datetime.datetime.now().strftime("%I%M%p")
            speech(f"the time is {time}")
        elif "joke" in command or "jokes" in command:
            joke=pyjokes.get_joke(language="en",category="neutral")
            speech(f"here's a joke for you, {joke} ")

        elif "what is" in command or "what are" in command:
            query=command.replace("what is","").replace("what are","").strip()
            webbrowser.open(f"https://www.google.com/search?q={query}")

        elif "youtube" in command and "search" in command:
            query=command.replace("youtube","").replace("search","").replace("for","").replace("open","").replace("and","").strip()
            speech(f"opening youtube and searching for {query}")
            webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
        elif "youtube" in command:
            print("opening youtube")
            webbrowser.open("https://www.youtube.com/")
        elif "thanks" in command or "thankyou" in command or "thank you" in command:
            speech("it's been a pleasure talking to you.")
            sys.exit()
        elif "internet" in command and "speed" in command:
            speech("opening fast.com")
            webbrowser.open("https://fast.com")
            # speech("speed test app")
            # path="D:/VsCode/PythonProjects/internetSpeedCalc.py"
            os.system(f"python {path}")
        elif "open" in command and ("map" in command or "maps" in command):
            speech("opening google maps")
            webbrowser.open("https://maps.google.com")
        elif "open" in command and ("downloads" in command or "download" in command):
            path="D:/IDM"
            speech("opening downloads folder")
            os.startfile(path)
        elif "organised" in command and ("downloads" in command or "download" in command):
            speech("Organizing your downloads")
            path="D:\VsCode\PythonProjects\AutoFileSorter.py"
            os.system(f"python {path}")
            speech("your downloads have been organized")
        elif "open" in command and ("evernote" in command):
            speech("opening evernote")
            os.startfile("C:/Users/zero/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Evernote.lnk")
        elif "open" in command and ("github" in command):
            speech("opening github")
            webbrowser.open("https://github.com/sinanshamsudheen")
        else:
            speech("no commands were captured, do you want to exit?")
            ans=sptext()
            choice=ans.lower()
            if "exit" in choice and "yes" in choice:
                speech("thankyou, have a great day!")
                sys.exit()
            else:
                speech("please repeat your command")
        time.sleep(5)

    


