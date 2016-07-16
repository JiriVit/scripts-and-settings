""" Combines two images into one wallpaper image. """

# TODO Replace explicit filenames with automatic searching for image files
#      in current folder and checking their dimensions.

from PIL import Image

im1_width = 1366
im1_height = 768
im2_width = 1280
im2_height = 1024

im1 = Image.open('img1366.jpg')
im2 = Image.open('img1280.jpg')

im = Image.new('RGB', (im1_width + im2_width, max(im1_height, im2_height)))

im.paste(im1, (0, 0, im1_width, im1_height))
im.paste(im2, (im1_width, 0, im1_width + im2_width, im2_height))

im.save('img.jpg', 'jpeg', quality = 95)
