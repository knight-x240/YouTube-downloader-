from pytube import YouTube
link = input("enter your URL")
video = YouTube(link)
stream = video.streams.get_highest_resolution()
stream = download()
