import concurrent.futures
import os
import pytube
import subprocess
import random
import string
from pathlib import Path
import re


def download_youtube_video():
    # create a YouTube object
    url = input("Enter the URL of the Youtube video you want to download: ")
    video = pytube.YouTube(url)

    # display the available video streams and ask the user to choose one
    video_streams = video.streams.filter(
        progressive=False, file_extension='mp4', type='video'
    ).order_by("resolution").desc()

    # group the video streams by resolution
    grouped_streams = {}
    for stream in video_streams:
        if stream.resolution in grouped_streams:
            grouped_streams[stream.resolution].append(stream)
        else:
            grouped_streams[stream.resolution] = [stream]

    # get the highest resolution video stream from each group
    highest_res_streams = [
        max(group, key=lambda stream: int(stream.resolution[:-1]))
        for group in grouped_streams.values()
    ]

    # print the details of the highest resolution streams in each category
    print("Available Video Qualities:")
    for i, stream in enumerate(highest_res_streams):
        print(f"{i+1}.{stream.resolution}")

    choice = int(input("Enter the number corresponding to the video quality you want to download: "))

    # filter the audio streams to get the one with the highest bitrate
    audio_streams = video.streams.filter(
        only_audio=True, file_extension='webm'
    ).order_by('bitrate').desc()
    if not audio_streams:
        raise Exception("No audio streams found.")

    audio_stream = audio_streams[0]

    # download the selected video and audio streams in parallel
    video_stream = highest_res_streams[choice-1]
    print(f"Downloading '{video.title}'")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        video_future = executor.submit(
            video_stream.download,
            output_path=Path.cwd(),
            filename=''.join(random.sample(string.ascii_letters, k=20))+'.mp4',
        )
        audio_future = executor.submit(
            audio_stream.download,
            output_path=Path.cwd(),
            filename=''.join(random.sample(string.ascii_letters, k=20))+'.webm',
        )
        video_file = video_future.result()
        audio_file = audio_future.result()

    # merge the audio and video files using ffmpeg
    output_filename = re.sub(r'\W+', '_', video.title) + '.mp4'
    output_path = Path.cwd() / output_filename
    cmd = f'ffmpeg -i "{video_file}" -i "{audio_file}" -c:v copy -c:a aac -loglevel quiet "{output_path}"'
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error merging audio and video files: {e}")
    else:
        # delete the separate audio and video files
        os.remove(video_file)
        os.remove(audio_file)

        print(f"Successfully downloaded '{video.title}'.")


if __name__ == '__main__':
    download_youtube_video()
