import random
target= random.randint(1,100)

user=0
print("hello there!, Welcome to guess the number!!")
while(user!=target):

    user=input("enter your guess OR Quit(Q):")
    if(user=="Q"):
        print("Quitting..")
        break

    user=int(user)
    if(user==target):
        print("correct guess!!")
        break
    elif(user<target):
        print("try a bigger guess!")
    else:
        print("try a small guess!")

print("-----GAME OVER-----")




