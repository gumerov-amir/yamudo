import json
import os
import sys
import time
from typing import Dict, Union
from urllib.parse import urlparse

import requests
import yandex_music

import configurator


if not os.path.isfile("config.json"):
    configurator.main()

with open("config.json", "r", encoding="UTF-8") as f:
    cfg: Dict[str, str] = json.load(f)

if not cfg["token"]:
    sys.exit("Your token is empty")

devnull = open(os.devnull, "w")
normal_stdout = sys.stdout
sys.stdout = devnull

client = yandex_music.Client(token=cfg["token"])
client.init()

sys.stdout = normal_stdout
devnull.close()

if not os.path.isdir(cfg["target_dir"]):
    try:
        os.mkdir(cfg["target_dir"])
    except:
        sys.exit("Invalid target directory")

target_dir = cfg["target_dir"]

downloaded_files = []

for root, dirs, files in os.walk(target_dir):
    downloaded_files += [file for file in files]

if len(sys.argv) > 1:
    targets = sys.argv[1::]
else:
    if not os.path.isfile(cfg["links_file"]):
        sys.exit("Invalid links file path")
    with open(cfg["links_file"], "r", encoding="utf-8") as f:
        targets = [target[0:-1] for target in f.readlines()]

context = ""
sub_context = ""
track_index = 0
tracks_count = 0

downloaded_size = 0
total_size = 0

waiting = False


def update_progress():
    if waiting:
        sys.stdout.write(f"Waiting 5 seconds{' '*100}\r")
    elif tracks_count == 1:
        sys.stdout.write(f"Downloading track \"{sub_context if len(sub_context) <= 79 else sub_context[0:75] + '...'}\" {downloaded_size} of {total_size} MB\r")
    else:
        sys.stdout.write(f"Downloading {context if len(context) <= 36 else context[0:32] + '...'} ({track_index} of {tracks_count}, {sub_context if len(sub_context) <= 35 else sub_context[0:32] + '...'}), {downloaded_size} of {total_size} MB\r")
    sys.stdout.flush()

def get_track_name(track: yandex_music.Track) -> str:
    return "{artists} - {title}".format(artists=", ".join(track.artists_name()), title=track.title)

def get_tracks(link: str):
    tracks = []
    parsed_data = urlparse(link)
    path = parsed_data.path
    if "/album/" in path and "/track/" in path:
        split_path = path.split("/")
        real_id = split_path[4] + ":" + split_path[2]
        track = client.tracks(real_id)[0]
        tracks.append(track)
        context = ""
    elif "/album/" in path:
        album = client.albums_with_tracks(path.split("/")[2])
        for volume in album.volumes:
            for track in volume:
                tracks.append(track)
        context = "album \"" + album.title + "\""
    elif "users" in path and "playlist" in path:
        split_path = path.split("/")
        user_id = split_path[2]
        kind = split_path[4]
        playlist: yandex_music.Playlist = client.users_playlists(kind=kind, user_id=user_id)
        for track in playlist.tracks:
            tracks.append(track)
        context = "playlist \"" + playlist.title + "\""
    return tracks, context

def clean_file_name(file_name: str) -> str:
    for char in ["\\", "/", "%", "*", "?", ":", '"', "|"] + [
        chr(i) for i in range(1, 32)
    ]:
        file_name = file_name.replace(char, "_")
    file_name = file_name.strip()
    return file_name

def download_file(url: str, file_path: str) -> None:
    global downloaded_size, total_size
    with open(file_path, "wb") as f:
        response = requests.get(url, stream=True)
        total_size = round(int(response.headers.get('content-length')) / (1024 * 1024), 2)
        downloaded_size = 0
        for data in response.iter_content(chunk_size=1024 * 1024):
            downloaded_size += round(len(data) / (1024 * 1024), 2)
            f.write(data)
            update_progress()

def download(track: yandex_music.Track) -> None:
    global sub_context, waiting
    if isinstance(track, yandex_music.TrackShort):
        track = track.fetch_track()
    track_name = get_track_name(track)
    sub_context = track_name
    file_name = clean_file_name(track_name + ".mp3")
    if file_name in downloaded_files:
        return
    url = track.get_download_info(get_direct_links=True)[0].direct_link
    download_file(url, os.path.join(target_dir, file_name))
    downloaded_files.append(file_name)
    waiting = True
    update_progress()
    time.sleep(5)
    waiting = False

def main():
    global context, track_index, tracks_count
    print("YaMuDo")
    print(f"{len(targets)} links was given")
    for target in targets:
        tracks, context_name = get_tracks(target)
        context = context_name
        tracks_count = len(tracks)
        update_progress()
        for track in tracks:
            track_index += 1
            download(track)
    print("")
    print("Done")

if __name__ == "__main__":
    main()


