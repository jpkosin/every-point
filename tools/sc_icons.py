"""Score Card icon options: an SC monogram and a margin line, in ink and red."""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageChops
HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "fonts", "EBGaramond[wght].ttf")
BG, INK, RED = (255, 255, 248), (38, 38, 36), (155, 45, 38)
S = 2048

def font(px, w=800, italic=False):
    f = ImageFont.truetype(FONT, px, layout_engine=ImageFont.Layout.RAQM); f.set_variation_by_axes([w]); return f

def glyph(ch, px, w=800):
    """A glyph as an L-mask cropped to its ink, plus its baseline offset."""
    f = font(px, w); m = Image.new("L", (px * 2, px * 2)); d = ImageDraw.Draw(m)
    d.text((px // 2, int(px * 1.4)), ch, font=f, fill=255, anchor="ls")
    box = m.getbbox(); return m.crop(box), int(px * 1.4) - box[1]

def pair(px, gap_em, w=800):
    """S and C side by side, kerned by ink: gap measured between the ink, in em."""
    s, sb = glyph("S", px, w); c, cb = glyph("C", px, w)
    gap = int(gap_em * px); W = s.width + gap + c.width; Hh = max(sb, cb) + 4
    hgt = max(s.height + (Hh - sb), c.height + (Hh - cb))
    ms, mc = Image.new("L", (W, hgt)), Image.new("L", (W, hgt))
    ms.paste(s, (0, Hh - sb)); mc.paste(c, (s.width + gap, Hh - cb))
    return ms, mc

def step(d, x0, x1, ymid, amp, series, color, width):
    n = len(series) - 1; pts = [(x0, ymid)]; prev = 0
    for i, m in enumerate(series):
        x = x0 + (x1 - x0) * i / n
        pts += [(x, ymid - prev * amp), (x, ymid - m * amp)]; prev = m
    pts.append((x1, ymid - prev * amp))
    d.line(pts, fill=color, width=width, joint="curve")
    return pts[-1]

SERIES = [0, 0.5, 0.5, -0.45, -0.45, 0.25, 0.25, 0.9]
from PIL import ImageFilter

def canvas(): im = Image.new("RGB", (S, S), BG); return im, ImageDraw.Draw(im)

def place(ms, mc, cx, cy, scale_w):
    k = scale_w / ms.width
    ms = ms.resize((int(ms.width * k), int(ms.height * k)), Image.LANCZOS); mc = mc.resize(ms.size, Image.LANCZOS)
    return ms, mc, int(cx - ms.width / 2), int(cy - ms.height / 2)
PALE = (196, 92, 82)   # the red, lifted for large fills

def letters(gap_em=0.025, width=0.76, cy=0.5, w=800):
    ms, mc = pair(1000, gap_em, w)
    ms, mc, x, y = place(ms, mc, S / 2, S * cy, S * width)
    a = Image.new("L", (S, S)); a.paste(ms, (x, y)); b = Image.new("L", (S, S)); b.paste(mc, (x, y))
    return a, b, x, y, ms.width, ms.height

def fill(im, mask, color): im.paste(Image.new("RGB", im.size, color), (0, 0), mask)

def line_mask(x0, x1, ymid, amp, series, width):
    m = Image.new("L", (S, S)); d = ImageDraw.Draw(m)
    end = step(d, x0, x1, ymid, amp, series, 255, width); return m, end

def opt_a():
    """Behind the line. SC in pale red, set back; the game's margin drawn over it in ink, ending on the last score."""
    im, d = canvas(); a, b, x, y, w, hgt = letters(0.03, 0.78)
    fill(im, ImageChops.lighter(a, b), PALE)
    lm, (ex, ey) = line_mask(S * 0.08, S * 0.86, y + hgt * 0.56, hgt * 0.30, SERIES, int(S * 0.024))
    halo = lm.filter(ImageFilter.MaxFilter(31)); fill(im, halo, BG); fill(im, lm, INK)
    r = S * 0.034; d.ellipse((ex - r, ey - r, ex + r, ey + r), fill=INK)
    return im

def opt_b():
    """Through-line. SC in ink; one red margin line threads both letters, the paper opening around it where they cross."""
    im, d = canvas(); a, b, x, y, w, hgt = letters(0.03, 0.78)
    fill(im, ImageChops.lighter(a, b), INK)
    lm, (ex, ey) = line_mask(S * 0.08, S * 0.86, y + hgt * 0.54, hgt * 0.26, SERIES, int(S * 0.026))
    fill(im, lm.filter(ImageFilter.MaxFilter(35)), BG); fill(im, lm, RED)
    r = S * 0.034; d.ellipse((ex - r, ey - r, ex + r, ey + r), fill=RED)
    return im

def opt_c():
    """Home and away. S in red, C in ink: the two sides of every game, nothing else. The plainest mark, and the strongest at the size of a fingertip."""
    im, d = canvas(); a, b, x, y, w, hgt = letters(0.02, 0.80)
    fill(im, a, RED); fill(im, b, INK)
    return im

def opt_d():
    """The chart in the C. The C's open bowl becomes the plot: a red margin line runs out of its mouth to the last score."""
    im, d = canvas(); a, b, x, y, w, hgt = letters(0.03, 0.80)
    fill(im, ImageChops.lighter(a, b), INK)
    bb = b.getbbox(); cw = bb[2] - bb[0]; ch = bb[3] - bb[1]
    lm, (ex, ey) = line_mask(bb[0] + cw * 0.34, bb[2] + cw * 0.06, bb[1] + ch * 0.5, ch * 0.12, [0, 0.5, 0.5, -0.6, -0.6, 1.0], int(S * 0.022))
    fill(im, lm, RED); r = S * 0.032; d.ellipse((ex - r, ey - r, ex + r, ey + r), fill=RED)
    return im

def opt_e():
    """Signed with a sparkline. Red S, ink C, standing on a fine ink rule that is itself a game's margin, ending in the red dot Tufte gives every sparkline."""
    im, d = canvas(); a, b, x, y, w, hgt = letters(0.02, 0.72, cy=0.44)
    fill(im, a, RED); fill(im, b, INK)
    base = y + hgt + S * 0.085
    ex, ey = step(d, x, x + w, base, S * 0.04, SERIES, INK, int(S * 0.011))
    r = S * 0.024; d.ellipse((ex - r, ey - r, ex + r, ey + r), fill=RED)
    return im

OPTS = [opt_a, opt_b, opt_c, opt_d, opt_e]
if __name__ == "__main__":
    # The chosen icon is C (home and away). `python3 tools/sc_icons.py all DIR` redraws every option.
    if len(sys.argv) > 2 and sys.argv[1] == "all":
        for f in OPTS: f().resize((1024, 1024), Image.LANCZOS).save(os.path.join(sys.argv[2], f.__name__ + ".png"))
    else:
        root = os.path.join(HERE, ".."); im = opt_c()
        for n in (180, 192, 512): im.resize((n, n), Image.LANCZOS).save(os.path.join(root, "sc-%d.png" % n))
        im.resize((64, 64), Image.LANCZOS).save(os.path.join(root, "sc-favicon.png"))
