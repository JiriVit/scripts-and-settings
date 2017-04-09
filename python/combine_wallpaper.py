"""Combines two images into one wallpaper image.

This script requires PIL module. Nowadays it is distributed as part of Pillow package. You install
it just by entering:
  python -m pip install Pillow

Warning: At the time of creating this script, Pillow 4.1.0 didn't work well with Python 3.6. So if
you use Python 3.6, it is recommended to install Pillow 4.0.0 instead, it works well.
"""

import os
import sys
from PIL import Image

# size of first image (= resolution of left display)
IMG1_WIDTH = 1366
IMG1_HEIGHT = 768
# size of second image (= resolution of right display)
IMG2_WIDTH = 1280
IMG2_HEIGHT = 1024

def combine(input_dir='.', output_dir='.'):
    """Combines two images of required sizes and saves it as new image."""
    img1 = None
    img2 = None

    # browse through files and look for images with required size
    files_list = os.listdir(input_dir)
    for filename in files_list:
        ext = os.path.splitext(filename)
        if len(ext) > 0 and (ext[1] == '.jpg' or ext[1] == '.jpeg'):
            img = Image.open(os.path.join(input_dir, filename))
            if img.size[0] == IMG1_WIDTH and img.size[1] == IMG1_HEIGHT:
                img1 = img
                img1_filename = filename
            if img.size[0] == IMG2_WIDTH and img.size[1] == IMG2_HEIGHT:
                img2 = img
                img2_filename = filename
            if img1 is not None and img2 is not None:
                break
    if img1 is None or img2 is None:
        print("ERROR: Couldn't find images of required sizes.")
        sys.exit(1)

    # create new image by combining the original ones
    output_img = Image.new('RGB', (IMG1_WIDTH + IMG2_WIDTH, max(IMG1_HEIGHT, IMG2_HEIGHT)))
    output_img.paste(img1, (0, 0, IMG1_WIDTH, IMG1_HEIGHT))
    output_img.paste(img2, (IMG1_WIDTH, 0, IMG1_WIDTH + IMG2_WIDTH, IMG2_HEIGHT))

    # save new image to a file
    output_img_filename = str.format('{0}_{1}.jpg', os.path.splitext(img1_filename)[0],
                                     os.path.splitext(img2_filename)[0])
    output_img_filename = os.path.join(output_dir, output_img_filename)
    output_img.save(output_img_filename, 'jpeg', quality=95)

def main():
    """Do the script's main job."""
    combine()

if __name__ == '__main__':
    main()
