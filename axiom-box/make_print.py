"""Shrink the AXIOM BOX caption (reusing its own lettering) and export a
transparent, print-ready PNG for a t-shirt front."""
import sys
import numpy as np
from PIL import Image

SRC = sys.argv[1] if len(sys.argv) > 1 else "source.webp"
CAPTION_SCALE = 0.6           # caption size relative to the original
GAP = 50                      # px between rebus row and caption (source scale)
CANVAS = (4500, 5400)         # standard DTG front print area @ 300 DPI
ART_WIDTH = 4200              # artwork width on the canvas

img = np.array(Image.open(SRC).convert("RGB")).astype(np.float32)

# Alpha from brightness: the background is flat black.
lum = img.max(axis=2)
alpha = np.clip((lum - 18) / (70 - 18), 0, 1)
rgb = np.clip(img / np.maximum(alpha, 1e-3)[..., None], 0, 255)  # un-premultiply off black
rgba = np.dstack([rgb, alpha * 255]).astype(np.uint8)

def bands(mask_1d):
    out, start = [], None
    for i, v in enumerate(mask_1d):
        if v and start is None:
            start = i
        elif not v and start is not None:
            out.append((start, i)); start = None
    if start is not None:
        out.append((start, len(mask_1d)))
    return out

solid = alpha > 0.5
(r0, r1), (c0, c1) = bands(solid.any(axis=1))[:2]   # rebus row, caption row
def xspan(a, b):
    cols = np.where(solid[a:b].any(axis=0))[0]
    return cols[0], cols[-1] + 1

rx0, rx1 = xspan(r0, r1)
cx0, cx1 = xspan(c0, c1)
pad = 6
rebus = Image.fromarray(rgba[r0 - pad:r1 + pad, rx0 - pad:rx1 + pad])
caption = Image.fromarray(rgba[c0 - pad:c1 + pad, cx0 - pad:cx1 + pad])
caption = caption.resize((round(caption.width * CAPTION_SCALE),
                          round(caption.height * CAPTION_SCALE)), Image.LANCZOS)

# Recompose: rebus on top, smaller caption centered under it.
w = rebus.width
h = rebus.height + GAP + caption.height
art = Image.new("RGBA", (w, h), (0, 0, 0, 0))
art.alpha_composite(rebus, (0, 0))
art.alpha_composite(caption, ((w - caption.width) // 2, rebus.height + GAP))

# Scale to print width and place near the top of the print area.
scale = ART_WIDTH / art.width
art = art.resize((ART_WIDTH, round(art.height * scale)), Image.LANCZOS)
canvas = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
canvas.alpha_composite(art, ((CANVAS[0] - art.width) // 2, 300))
canvas.save("axiom-box-print.png", dpi=(300, 300))

# Previews on dark and light shirts for proofing.
for name, color in [("preview-black.png", (17, 17, 17)), ("preview-white.png", (240, 240, 240))]:
    bg = Image.new("RGBA", CANVAS, color + (255,))
    bg.alpha_composite(canvas)
    bg.convert("RGB").resize((900, 1080), Image.LANCZOS).save(name)
print("art", art.size, "upscale x%.2f" % scale)
