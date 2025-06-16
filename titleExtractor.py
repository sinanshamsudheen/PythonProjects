from pytube import Playlist

playlist_url = "https://www.youtube.com/playlist?list=PLeo1K3hjS3uu7CxAacxVndI4bE_o3BDtO"
playlist = Playlist(playlist_url)

print("extracting titles: ")
for video in playlist.videos:
    print(video.title)
