import os
from sys import argv
from PIL import Image

filename_webp = argv[1]
filename_jpg = os.path.splitext(filename_webp)[0] + '.jpg'

im = Image.open(filename_webp).convert('RGB')
im.save(filename_jpg, 'jpeg')
