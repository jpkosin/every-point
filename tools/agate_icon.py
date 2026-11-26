import sys, random
from PIL import Image, ImageDraw, ImageFont
import os
FONT = os.path.join(os.path.dirname(__file__), "..", "fonts", "EBGaramond[wght].ttf")
BG, INK, RED, BLUE = (255, 255, 248), (17, 17, 17), (155, 45, 38), (46, 90, 135)
WORD = "Agate"
# Extra pair adjustments on top of the font's own kerning, in em units.
TWEAK = {"Ag": -0.028, "ga": -0.008, "at": -0.012, "te": -0.004}
def font(px, wght=800):
    f = ImageFont.truetype(FONT, px, layout_engine=ImageFont.Layout.RAQM)
    f.set_variation_by_axes([wght]); return f
def draw(n=1024, out=None, wght=800):
    S = 2048
    im = Image.new("RGB", (S, S), BG); d = ImageDraw.Draw(im)
    px = 1000; f = font(px, wght)
    def layout(f, px):
        xs, x = [], 0.0
        for i, ch in enumerate(WORD):
            # position from the font's kerned advance of the preceding text
            base = f.getlength(WORD[:i], features=["kern"]) if i else 0
            adj = sum(TWEAK.get(WORD[j - 1:j + 1], 0) for j in range(1, i + 1)) * px
            xs.append(base + adj)
        total = f.getlength(WORD, features=["kern"]) + sum(TWEAK.get(WORD[j - 1:j + 1], 0) for j in range(1, len(WORD))) * px
        return xs, total
    xs, total = layout(f, px)
    # ink extent, not advance: measure the drawn box
    tmp = Image.new("L", (S * 2, S)); td = ImageDraw.Draw(tmp)
    for ch, x in zip(WORD, xs): td.text((200 + x, 800), ch, font=f, fill=255, anchor="ls")
    l, t, r, b = tmp.getbbox()
    ink_w = r - l
    scale = S * 0.80 / ink_w
    px = int(px * scale); f = font(px, wght); xs, total = layout(f, px)
    tmp = Image.new("L", (S * 2, S * 2)); td = ImageDraw.Draw(tmp)
    for ch, x in zip(WORD, xs): td.text((400 + x, 1200), ch, font=f, fill=255, anchor="ls")
    l, t, r, b = tmp.getbbox()
    cap_top = 1200 - t   # distance from baseline to top of ink
    desc = b - 1200      # descender of g
    # compose: word block + gap + rug block, centred vertically on cap height & rug, ignoring the descender a bit
    rug_h = S * 0.11; gap = S * 0.075
    block = cap_top + desc + gap + rug_h
    top = (S - block) / 2 - S * 0.01
    base_y = top + cap_top
    x0 = (S - (r - l)) / 2 - (l - 400)
    for ch, x in zip(WORD, xs): d.text((x0 + x, base_y), ch, font=f, fill=INK, anchor="ls")
    # rug of score ticks
    ry = base_y + desc + gap + rug_h
    left, right = (S - (r - l)) / 2, (S + (r - l)) / 2
    lw = max(2, int(S * 0.009))
    d.line([(left, ry), (right, ry)], fill=INK, width=lw)
    rnd = random.Random(5)
    N = 15
    heights = [0.55, 1.0, 0.35, 0.75, 1.0, 0.45, 0.85, 0.35, 1.0, 0.6, 0.4, 0.9, 0.5, 1.0, 0.7]
    cols = [RED, BLUE, RED, RED, BLUE, BLUE, RED, BLUE, RED, BLUE, RED, RED, BLUE, RED, BLUE]
    for i in range(N):
        u = (i + 0.5 + rnd.uniform(-0.28, 0.28)) / N
        x = left + u * (right - left)
        d.line([(x, ry - lw / 2), (x, ry - rug_h * heights[i])], fill=cols[i], width=int(lw * 0.95))
    im = im.resize((n, n), Image.LANCZOS)
    if out: im.save(out)
    return im
if __name__ == "__main__":
    for n in (180, 192, 512): draw(n, "agate-%d.png" % n)
    draw(64, "agate-favicon.png")
