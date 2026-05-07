import os, re, csv, shutil, requests
from yt_dlp import YoutubeDL
from pydub import AudioSegment
from unidecode import unidecode

TRACK_COLUMNS = ['title', 'artist', 'album', 'cover', 'file', 'collection_id']
COLLECTION_COLUMNS = ['id', 'name', 'description', 'image']


def main():
  while True:
    print('1 - Add Track')
    print('2 - Add Artist')
    print('3 - Exit')

    try:
      match int(input('>>> ')):
        case 1: add_track()
        case 2: add_artist(input('Artist:\n>>> '))
        case 3: exit(0)

    except KeyboardInterrupt:
      exit(0)

    except Exception as error:
      print(error)


def add_track():
  name, mp3 = youtube_mp3(input('YouTube URL:\n>>> '))
  artist, album = track_image(name)

  collection_id = snake_case(artist)

  save_csv(
    f'collections/dataframes/{collection_id}.csv',
    TRACK_COLUMNS,
    [name, artist, album, jpeg(album), mp3, collection_id]
  )

  print('Track added.')


def add_artist(query):
  name = artist_image(query)

  save_csv(
    'settings/collections.csv',
    COLLECTION_COLUMNS,
    [snake_case(name), name, 'Artist', jpeg(name)]
  )

  sort_csv('settings/collections.csv')

  print('Artist added.')


def youtube_mp3(url):
  os.makedirs('temp', exist_ok=True)
  os.makedirs('tracks', exist_ok=True)

  with YoutubeDL({'format': 'mp4/bestaudio/best', 'outtmpl': 'temp/%(title)s.%(ext)s', 'quiet': True}) as ydl:
    info = ydl.extract_info(url, download=True)
    mp4 = ydl.prepare_filename(info)

  name = input(f'Name (or {info["title"]}):\n>>> ') or info['title']
  mp3 = mp3_ext(name)

  AudioSegment.from_file(mp4).export(f'tracks/{mp3}', format='mp3', bitrate='320k')

  shutil.rmtree('temp', ignore_errors=True)

  return name, mp3


def track_image(name):
  data = requests.get(f'https://api.deezer.com/search?q={name}').json()['data'][0]

  artist = data['artist']['name']
  album = data['album']['title']

  image(data['album']['cover_xl'], f'images/{jpeg(album)}')

  return artist, album


def artist_image(query):
  data = requests.get(f'https://api.deezer.com/search/artist?q={query}').json()['data'][0]

  name = data['name']

  image(data['picture_xl'], f'images/{jpeg(name)}')

  return name


def image(url, path):
  os.makedirs(os.path.dirname(path), exist_ok=True)

  if os.path.exists(path):
    return

  response = requests.get(url)

  if response.status_code != 200:
    raise Exception(f'Failed to download {url}')

  with open(path, 'wb') as file:
    file.write(response.content)


def save_csv(path, headers, data):
  os.makedirs(os.path.dirname(path), exist_ok=True)

  exists = os.path.isfile(path)

  with open(path, 'a', newline='') as file:
    writer = csv.writer(file)

    if not exists:
      writer.writerow(headers)

    writer.writerow(data)


def sort_csv(path):
  with open(path, newline='') as file:
    rows = list(csv.reader(file))

  header, data = rows[0], rows[1:]

  data.sort(key=lambda row: row[0].lower())

  with open(path, 'w', newline='') as file:
    writer = csv.writer(file)

    writer.writerow(header)
    writer.writerows(data)


def snake_case(text):
  return re.sub(r'[^\w_]', '', re.sub(r'\s+', '_', unidecode(text.strip().lower())))


def mp3_ext(name):
  return f'{snake_case(name)}.mp3'


def jpeg(name):
  return f'{snake_case(name)}.jpeg'


if __name__ == '__main__':
  main()
