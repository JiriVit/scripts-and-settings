import re

# 3rd party libraries
from mutagen.id3 import Encoding, PictureType, ID3, APIC, TALB, TDRC, TIT2, TPE1, TPE2, TRCK


def import_id3_from_filename(mp3_path):
    pattern = r'^(\d+)\s+(.+)\.mp3$'
    match = re.match(pattern, mp3_path)
    if match:
        track_number = match.group(1)
        track_name = match.group(2)
        tags = ID3(mp3_path)
        tags['TRCK'] = TRCK(encoding=Encoding.UTF8, text=track_number)
        tags['TIT2'] = TIT2(encoding=Encoding.UTF8, text=track_name)
        tags.save()
        print(f'{mp3_path}: imported track number {track_number} and title "{track_name}"')
    else:
        print(f'{mp3_path}: could not parse filename')


def process_file(mp3_path):
    tags = ID3(mp3_path)
    track_title = tags['TIT2'].text[0]
    print(track_title)


