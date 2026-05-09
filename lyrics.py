import os, subprocess, requests, pandas as pd
from pathlib import Path

csv_name = input("CSV name: ").strip()
csv_path = f"collections/dataframes/{csv_name}"

lyrics_dir = Path("lyrics")
lyrics_dir.mkdir(exist_ok=True)

branch = Path(csv_name).stem

if not (lyrics_dir / ".git").exists():
  subprocess.run(["git", "init"], cwd=lyrics_dir)

current_branch = subprocess.run(
  ["git", "branch", "--show-current"],
  cwd=lyrics_dir,
  capture_output=True,
  text=True
).stdout.strip()

if current_branch != branch:
  branches = subprocess.run(
    ["git", "branch", "--list", branch],
    cwd=lyrics_dir,
    capture_output=True,
    text=True
  ).stdout.strip()

  if branches:
    subprocess.run(["git", "checkout", branch], cwd=lyrics_dir)
  else:
    subprocess.run(["git", "checkout", "-b", branch], cwd=lyrics_dir)

df = pd.read_csv(csv_path)

print()

for i, row in enumerate(df.itertuples(index=False), 1):
  print(f"[{i}] {row.title}")

print("[Enter] All")

option = input("Option: ").strip()

if option:
  try:
    rows = [df.iloc[int(option) - 1].to_dict()]
  except:
    print("Invalid option")
    exit()
else:
  rows = df.to_dict("records")

for row in rows:
  title = str(row["title"]).strip()
  artist = str(row["artist"]).strip()
  mp3 = str(row["file"]).strip()

  lrc = Path(mp3).with_suffix(".lrc").name
  out = lyrics_dir / lrc

  print(f"\nSearching: {artist} - {title}")

  try:
    r = requests.get(
      "https://lrclib.net/api/search",
      params={"track_name": title, "artist_name": artist},
      headers={"User-Agent": "Mozilla/5.0"},
      timeout=10
    )

    results = r.json()

    if not results:
      print("Not found")
      continue

    lyrics = results[0].get("syncedLyrics")

    if not lyrics:
      print("No synced lyrics")
      continue

    with open(out, "w", encoding="utf-8") as f: f.write(lyrics)

    print(f"Saved: {out}")

    subprocess.run(["git", "add", lrc], cwd=lyrics_dir)
    subprocess.run(["git", "commit", "-m", f"Add {title}"], cwd=lyrics_dir)

    print(f'Committed: "Add {title}"')

  except Exception as e:
    print(f"Error: {e}")
