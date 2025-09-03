import os

import id3lib.id3 as id3


def main():
    mp3_files = [f for f in os.listdir('.') if f.endswith('.mp3')]
    for mp3_file in mp3_files:
        id3.import_id3_from_filename(mp3_file)


if __name__ == "__main__":
	main()
