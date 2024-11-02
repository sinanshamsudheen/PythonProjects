from pytube import Playlist

# link=input("enter playlist link: ")
play=Playlist("https://www.youtube.com/playlist?list=PLLdoPuHMV59B529tFzeCSEn0o_lPCdEnV")

print(f"Downloading videos from playlist: {play.title}")

for video in play.videos:
    stream = video.streams.filter(res="720p", progressive=True).first()  # Filter for 720p, progressive streams
    if stream:
        stream.download()
        print(f"Downloaded: {video.title} in 720p")
    else:
        print(f"720p not available for: {video.title}")

print("All available videos in 720p downloaded successfully!")