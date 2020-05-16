import sys
from PIL import Image

MAX_W = 316
MAX_H = 142


MAGIC_SCALE = 1.482718894

img = Image.open(sys.argv[1])
w, h = img.size

scale = min(MAX_W / w, MAX_H / h)
img = img.resize((int(w * scale), int(h * scale * MAGIC_SCALE)), Image.ANTIALIAS)

w, h = img.size
pix = img.load()

with open(sys.argv[2], "w") as f:
    f.write("<font size='3' face='fake'>")
    for y in range(h):
        for x in range(w):
            r, g, b = pix[x, y][:3]
            f.write(f"<font color='#{r:02X}{g:02X}{b:02X}'>a</font>")
        f.write("\n")
    f.write("</font>")
