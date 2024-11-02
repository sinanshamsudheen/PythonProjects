from pytube import YouTube

link=input("Enter link: ")

youtube1=YouTube(link)
videos=youtube1.streams.filter(progressive=True).order_by("resolution").desc()

vid=list(enumerate(videos))
for i in vid:
    print(i)
print()
key=int(input("enter choice: "))
videos[key].download()
print("Download success!")
