"""
Script for fixing of photos from Jiri's travels.
Performs two operations:
1. Renames the photo files to format originally assigned by the Samsung smartphone,
   based on datetime in their EXIF.
2. TODO Renames the directories per the same pattern.
"""

import os
from PIL import Image


def rename_photo_to_samsung_original(path):
    """Renames photo to original name assigned by Samsung smartphone.

    Args:
    path: Path to the image file.
    """
    # get datetime from image EXIF
    with Image.open(path) as img:
        img_exif = img.getexif()
        datetime = img_exif[306] # '2016:10:10 11:29:05'
    
    # build new filename to resemble the original assigned by the Samsung smartphone
    new_filename = datetime.replace(':', '').replace(' ', '_') + '.jpg'
    new_path = os.path.join(os.path.dirname(path), new_filename)

    # prevent renaming photos which still have the original name
    old_filename = os.path.basename(path)
    photo_needs_rename = (old_filename[0:4] != new_filename[0:4])

    # rename the file and print report
    if photo_needs_rename:
        os.rename(path, new_path)
        print(f'{path};renamed;{new_path}')
    else:
        print(f'{path};preserved')


for root, dirs, files in os.walk('.'):
    # process only directories starting with a year
    if root.startswith(r'.\20'):
        files = [f for f in files if f.lower().endswith('.jpg')]
        for filename in files:
            path = os.path.join(root, filename)
            rename_photo_to_samsung_original(path)