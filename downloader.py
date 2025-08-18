from pytube import YouTube
from pytube.cli import on_progress
import sys

def main():
    print("==== YouTube Downloader ====")
    link = input("Enter the YouTube video URL: ").strip()
    try:
        yt = YouTube(link, on_progress_callback=on_progress)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Title: {yt.title}")
    print(f"Author: {yt.author}")
    print("Length:", yt.length // 60, "minutes,", yt.length % 60, "seconds")
    print("\nWhat would you like to download?")
    print("1. Highest resolution video")
    print("2. Lowest resolution video")
    print("3. Audio only")
    choice = input("Enter your choice (1/2/3): ").strip()

    if choice == '1':
        stream = yt.streams.get_highest_resolution()
        file_type = "video"
    elif choice == '2':
        stream = yt.streams.get_lowest_resolution()
        file_type = "video"
    elif choice == '3':
        stream = yt.streams.filter(only_audio=True).first()
        file_type = "audio"
    else:
        print("Invalid choice. Exiting.")
        sys.exit(1)

    save_path = input("Enter download path (leave blank for current directory): ").strip() or "."

    print(f"\nDownloading {file_type}...")
    try:
        out_file = stream.download(output_path=save_path)
        if file_type == "audio":
            import os
            base, ext = os.path.splitext(out_file)
            new_file = base + '.mp3'
            os.rename(out_file, new_file)
            print(f"Downloaded audio saved as: {new_file}")
        else:
            print("Download completed!")
    except Exception as e:
        print(f"Download failed: {e}")

if __name__ == "__main__":
    main()