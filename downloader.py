import os
import re
import csv
import shutil
import requests
from pytubefix import YouTube
from pydub import AudioSegment
from unidecode import unidecode
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

spotify = Spotify(
    client_credentials_manager=SpotifyClientCredentials(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )
)

TRACK_COLUMS = ['title', 'artist', 'album', 'cover', 'file']
COLLECTION_COLUMNS = ['username', 'filename', 'name', 'description', 'image']
USERNAME = 'xmp3'


def main():
    while True:
        try:
            menu()
        except KeyboardInterrupt:
            exit(0)


def menu():
    print('1 - Add Track')
    print('2 - Add Artist')
    print('3 - Exit')

    try:
        option = int(input('Option:\n>>> '))
    except ValueError:
        print('Please enter a valid option')
        return

    match option:
        case 1:
            add_track('tracks', 'images', 'collections')
        case 2:
            add_artist(input('Artist Name:\n>>> '), 'images', 'settings')
        case 3:
            exit(0)


def add_track(audio_dir, image_dir, csv_dir):
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(csv_dir, exist_ok=True)

    print('Downloading MP3 from YouTube...')
    try:
        mp3 = download_youtube_mp3(input('YouTube URL:\n>>> '), audio_dir)
        name, mp3_filename = mp3
    except Exception as exception_info:
        print(exception_info)
        exit(1)
    print(f'{mp3_filename} downloaded successfully.')

    print('Downloading track image from Spotify...')
    search = name
    while True:
        try:
            track_image = download_track_image(search, image_dir)
            artist_name, album_name, image_path = track_image
        except Exception as exception_info:
            print(exception_info)
            exit(1)
        print('Track image downloaded successfully.')
        new_artist_name = input(f'Artist Name (or {artist_name}):\n>>> ')
        if new_artist_name:
            option = input('Download again? (Y/n):\n>>> ')
            option = option.lower()
            if option != 'n' or option != 'N':
                search = f'{name} {new_artist_name}'
                os.remove(image_path)
                print('Downloading track image from Spotify again...')
                continue
            else:
                break
        else:
            break

    cover = jpeg_extension(album_name)
    data = [name, artist_name, album_name, cover, mp3_filename]
    csv_filename = csv_extension(new_artist_name or artist_name)
    csv_path = join(csv_dir, csv_filename)
    save_as_csv(csv_path, TRACK_COLUMS, data)
    print(f'Successfully saved to {csv_path}')


def add_artist(artist_name, image_dir, csv_dir):
    os.makedirs(image_dir, exist_ok=True)
    os.makedirs(csv_dir, exist_ok=True)

    print('Downloading artist image from Spotify...')
    try:
        download_artist_image(artist_name, image_dir)
    except Exception as exception_info:
        print(exception_info)
        exit(1)
    print('Image downloaded successfully.')

    filename = snake_case(artist_name)
    cover = jpeg_extension(artist_name)
    data = [USERNAME, filename, artist_name, 'Artist', cover]
    csv_path = join(csv_dir, 'collections.csv')
    save_as_csv(csv_path, COLLECTION_COLUMNS, data)
    print(f'Successfully saved to {csv_path}')


def download_youtube_mp3(youtube_url, output_dir):
    name, mp4_path = download_youtube_mp4(youtube_url, 'temp')
    name = input(f'Name (or {name}):\n>>> ') or name
    mp3_filename = mp3_extension(name)
    mp3_path = join(output_dir, mp3_filename)

    print('Converting to MP3...')
    try:
        convert_mp4_to_mp3(mp4_path, mp3_path)
    except IndexError:
        raise Exception('No audio stream found in the video file.')
    print('Conversion completed.')

    try:
        shutil.rmtree('temp')
    except OSError as e:
        print(e.strerror)

    return name, mp3_filename


def download_youtube_mp4(youtube_url, output_dir):
    print('Loading...')
    video = YouTube(youtube_url).streams
    video = video.filter(progressive=True, file_extension='mp4')
    video = video.first()

    if not video:
        raise Exception('No video stream available.')

    print('Downloading MP4...')
    mp4_path = video.download(output_path=output_dir)
    print(f'MP4 downloaded successfully.')

    mp4_filename = os.path.basename(mp4_path)
    mp4_name, _ = os.path.splitext(mp4_filename)
    return mp4_name, mp4_path


def convert_mp4_to_mp3(mp4_path, mp3_path):
    audio = AudioSegment.from_file(mp4_path)
    audio.export(mp3_path, format='mp3', bitrate='320k')


def download_track_image(track_name, output_dir):
    results = spotify.search(q=track_name, type='track', limit=1)
    try:
        track = results['tracks']['items'][0]
        album = track['album']
        image_url = album['images'][0]['url']
        album_name = album['name']
        filename = jpeg_extension(album_name)
        save_path = os.path.join(output_dir, filename)
        if not os.path.exists(save_path):
            download_image(image_url, save_path)
        else:
            print(f'{filename} already exists.')
        artists = track['artists']
        artist_names = ', '.join([artist['name'] for artist in artists])
        return artist_names, album_name, save_path
    except (KeyError, IndexError):
        raise Exception(f'No album image found for track: {track_name}')


def download_artist_image(artist_name, output_dir):
    results = spotify.search(q=artist_name, type='artist', limit=1)
    try:
        artist = results['artists']['items'][0]
        image_url = artist['images'][0]['url']
        filename = jpeg_extension(artist['name'])
        save_path = os.path.join(output_dir, filename)
        if not os.path.exists(save_path):
            download_image(image_url, save_path)
        else:
            print(f'{filename} already exists.')
    except (KeyError, IndexError):
        raise Exception(f'No image found for artist: {artist_name}')


def download_image(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as file:
            file.write(response.content)
        print(f'{save_path} download completed.')
    else:
        raise Exception(f'Failed to download image from {url}')


def save_as_csv(path, headers, data):
    file_exists = os.path.isfile(path)
    with open(path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(headers)
        writer.writerow(data)


def join(directory, filename):
    return os.path.join(directory, filename)


def mp3_extension(name):
    return f'{snake_case(name)}.mp3'


def jpeg_extension(name):
    return f'{snake_case(name)}.jpeg'


def csv_extension(name):
    return f'{snake_case(name)}.csv'


def snake_case(string):
    string = unidecode(string.strip().lower())
    string = re.sub(r'\s+', '_', string)
    return re.sub(r'[^\w_]', '', string)


if __name__ == '__main__':
    main()
