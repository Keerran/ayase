import io
from PIL import Image


def merge(im1: Image, im2: Image):
    w = im1.size[0] + im2.size[0]
    h = max(im1.size[1], im2.size[1])
    im = Image.new("RGBA", (w, h))

    im.paste(im1)
    im.paste(im2, (im1.size[0], 0))

    return im


def img_to_buf(img: Image, format="PNG"):
    buf = io.BytesIO()
    img.save(buf, format=format)
    buf.seek(0)
    return buf
