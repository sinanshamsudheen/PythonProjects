from instabot import Bot
bot=Bot()
user=input("Enter username:")
pw=input("enter password:")
bot.login(username=user,password=pw)

n=1
while n!=0:
    print("choose,\n1-follow\n2-unfollow\n3-block\n4-unblock\n5-upload\n0-exit")
    n=int(input("Enter choice: "))
    if n==1:
        u=input("enter username to follow: ")
        bot.follow(u)
    elif n==2:
        u=input("enter username to unfollow: ")
        bot.unfollow(u)
    elif n==3:
        u=input("enter username to block: ")
        bot.block(u)
    elif n==4:
        u=input("enter username to unblock: ")
        bot.unblock(u)
    elif n==5:
        path=input("enter image path to upload: ")
        cap=input("enter caption: ")
        bot.upload_photo(path,caption=cap)
print("Thankyou! Youre logged out!")
bot.logout()
        
