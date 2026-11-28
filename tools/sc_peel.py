"""Score Card icon studies: the page peels back to show the data underneath.

Each option is a top sheet (the SC monogram) over a data sheet (the margin
line, Polymarket's grey band, the score ticks). Dimension comes only from the
fold itself: a soft gradient across the turned-back flap and the shadow it
casts. No bevels, no gloss, nothing that isn't the paper or the data.
Run: python3 tools/sc_peel.py  ->  /tmp/peel/*.png and a contact sheet.
"""
import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import sc_icons as sc

S = sc.S = 1024
BAND, BRED, BINK, BBLUE, BGRAY = (29, 28, 26), (227, 134, 124), (255, 255, 248), (143, 181, 226), (161, 156, 143)
CREAM, INK, RED, BLUE = (255, 255, 248), (38, 38, 36), (178, 64, 52), (52, 96, 160)
OUT = "/tmp/peel"; os.makedirs(OUT, exist_ok=True)

# ---- data sheet --------------------------------------------------------
SER = [0, 0.35, 0.35, -0.3, -0.3, 0.1, 0.1, 0.55, 0.55, 0.85]
WIN = lambda t: 0.62 * math.sin(t * 2.6 + 0.3) * (0.4 + 0.6 * t)  # Polymarket band, -1..1

def data_sheet(bg, ink, home, away, band_rgb, ymid=0.5, amp=0.26, x0=0.1, x1=0.92, ticks=True, lw=0.018, band_a=0.55):
    im = Image.new("RGB", (S, S), bg); d = ImageDraw.Draw(im, "RGBA")
    X0, X1, YM, A = x0 * S, x1 * S, ymid * S, amp * S
    # the grey band: win chance, home above the rule
    pts = [(X0 + (X1 - X0) * i / 120, YM - WIN(i / 120) * A * 0.9) for i in range(121)]
    d.polygon([(X0, YM)] + pts + [(X1, YM)], fill=band_rgb + (int(255 * band_a),))
    # the rule and quarter ticks
    d.line([(X0, YM), (X1, YM)], fill=ink + (90,), width=max(2, int(S * 0.004)))
    if ticks:
        for q in range(1, 4):
            x = X0 + (X1 - X0) * q / 4; d.line([(x, YM - S * 0.018), (x, YM + S * 0.018)], fill=ink + (90,), width=max(2, int(S * 0.004)))
    # the margin: a step line, red where home leads, blue where visitors do
    n = len(SER) - 1; prev = 0; w = int(S * lw)
    for i, m in enumerate(SER):
        xa = X0 + (X1 - X0) * max(0, i - 1) / n; xb = X0 + (X1 - X0) * i / n
        col = home if prev >= 0 else away
        d.line([(xa, YM - prev * A), (xb, YM - prev * A)], fill=col, width=w)
        col2 = home if m >= 0 else away
        d.line([(xb, YM - prev * A), (xb, YM - m * A)], fill=col2, width=w); prev = m
    ex, ey = X1, YM - prev * A
    d.line([(X0 + (X1 - X0) * (n - 1) / n, ey), (ex, ey)], fill=home, width=w)
    r = S * 0.026; d.ellipse([ex - r, ey - r, ex + r, ey + r], fill=ink)
    return im

def rug_sheet(bg, base, red, blue, y=0.62):
    im = Image.new("RGB", (S, S), bg); d = ImageDraw.Draw(im)
    Y = y * S; x0, x1 = 0.1 * S, 0.9 * S
    d.line([(x0, Y), (x1, Y)], fill=base, width=int(S * 0.006))
    import random; random.seed(7)
    xs = sorted(random.uniform(0.45, 1) ** 0.6 for _ in range(26))
    for i, t in enumerate(xs):
        x = x0 + (x1 - x0) * t; hgt = S * (0.07 + 0.11 * random.random() * t)
        d.line([(x, Y), (x, Y - hgt)], fill=red if i % 3 else blue, width=int(S * 0.009))
    return im

# ---- top sheet ---------------------------------------------------------
def mono(bg, s_col, c_col, width=0.66, cy=0.47, w=800):
    im = Image.new("RGB", (S, S), bg); a, b, *_ = sc.letters(0.02, width, cy, w)
    sc.fill(im, a, s_col); sc.fill(im, b, c_col); return im

# ---- the fold ----------------------------------------------------------
def peel(top, under, K, back_hi, back_lo, shadow=0.42, axis=(1, 1)):
    """Fold the corner beyond the line ax*x + ay*y = K back over the page.
    axis (1,1) peels the bottom-right corner; (0,1) the bottom edge."""
    ax, ay = axis
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    nrm = math.hypot(ax, ay); dist = (ax * xx + ay * yy - K) / nrm          # >0 beyond the fold
    beyond = dist > 0
    # flap: the reflection of the beyond-region across the fold line
    rx = xx - 2 * dist * ax / nrm; ry = yy - 2 * dist * ay / nrm
    # a point p is on the flap if its mirror lies inside the square and beyond the fold
    mx = xx + 2 * (-dist) * ax / nrm; my = yy + 2 * (-dist) * ay / nrm
    flap = (~beyond) & (mx >= 0) & (mx < S) & (my >= 0) & (my < S)
    t = np.where(flap, -dist, 0); tmax = max(1.0, float(t.max()))
    u = t / tmax                                                              # 0 at the fold, 1 at the tip
    # paper curling: bright just off the fold, settling toward the tip
    shade = 0.15 + 0.85 * (1 - np.exp(-u * 5)) * (1 - 0.35 * u)
    hi, lo = np.array(back_hi, np.float32), np.array(back_lo, np.float32)
    back = lo[None, None, :] * (1 - shade[..., None]) + hi[None, None, :] * shade[..., None]
    T, U = np.asarray(top, np.float32), np.asarray(under, np.float32)
    out = np.where(beyond[..., None], U, T)
    # the flap's shadow falls on the revealed sheet and a little onto the page
    sm = Image.fromarray((flap * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(S * 0.03))
    sm = np.asarray(sm, np.float32) / 255
    sm = np.roll(sm, (int(S * 0.012), int(S * 0.012)), (0, 1))
    out = out * (1 - shadow * sm[..., None])
    out = np.where(flap[..., None], back, out)
    # a hairline at the fold edge of the flap
    edge = flap & (np.abs(dist) < S * 0.0025)
    out = np.where(edge[..., None], out * 0.86, out)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

def peel_mask(top, under, mask, K, back_hi, back_lo, shadow=0.4, axis=(1, 1)):
    """Peel only what's inside mask (a letter): the part past the fold lifts
    like a sticker, the data printed under it shows, and the lifted piece
    lies folded back, shaded, casting a soft shadow."""
    ax, ay = axis; nrm = math.hypot(ax, ay)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    M = np.asarray(mask, np.float32) / 255 > 0.5
    dist = (ax * xx + ay * yy - K) / nrm
    beyond = dist > 0
    mx = np.round(xx - 2 * dist * ax / nrm).astype(int); my = np.round(yy - 2 * dist * ay / nrm).astype(int)
    inb = (mx >= 0) & (mx < S) & (my >= 0) & (my < S)
    flap = (~beyond) & inb & M[np.clip(my, 0, S - 1), np.clip(mx, 0, S - 1)]
    lifted = beyond & M
    t = np.where(flap, -dist, 0); u = t / max(1.0, float(t.max()))
    shade = 0.15 + 0.85 * (1 - np.exp(-u * 5)) * (1 - 0.35 * u)
    hi, lo = np.array(back_hi, np.float32), np.array(back_lo, np.float32)
    back = lo * (1 - shade[..., None]) + hi * shade[..., None]
    T, U = np.asarray(top, np.float32), np.asarray(under, np.float32)
    out = np.where(lifted[..., None], U, T)
    sm = Image.fromarray((flap * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(S * 0.018))
    sm = np.roll(np.asarray(sm, np.float32) / 255, (int(S * 0.008), int(S * 0.008)), (0, 1))
    out = out * (1 - shadow * sm[..., None])
    out = np.where(flap[..., None], back, out)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))

def vgrad(im, top_k=1.04, bot_k=0.94):
    """A whisper of light from above: the sheet is a little brighter at the top."""
    a = np.asarray(im, np.float32); k = np.linspace(top_k, bot_k, S)[:, None, None]
    return Image.fromarray(np.clip(a * k, 0, 255).astype(np.uint8))

# ---- the options -------------------------------------------------------
def opt1():
    """Dark sheet, corner turned: the app's masthead peels to show a game on paper."""
    top = vgrad(mono(BAND, BRED, BINK), 1.08, 0.92)
    under = data_sheet(CREAM, INK, RED, BLUE, (200, 196, 186), ymid=0.86, amp=0.06, x0=0.6, x1=0.93, ticks=False, lw=0.014)
    return peel(top, under, K=1.56 * S, back_hi=(128, 123, 114), back_lo=(48, 46, 42), shadow=0.35)

def opt2():
    """Paper sheet, corner turned: the cream page lifts to show the night's scores in the dark."""
    top = vgrad(mono(CREAM, RED, INK), 1.0, 0.95)
    under = rug_sheet(BAND, BINK, BRED, BBLUE, y=0.93)
    return peel(top, under, K=1.4 * S, back_hi=(255, 255, 250), back_lo=(214, 211, 200), shadow=0.45)

def opt3():
    """The big turn: half the page lifts away and the whole game runs underneath."""
    top = vgrad(mono(BAND, BRED, BINK, width=0.56, cy=0.36), 1.08, 0.94)
    under = data_sheet(CREAM, INK, RED, BLUE, (205, 201, 190), ymid=0.70, amp=0.14, x0=0.08, x1=0.94)
    return peel(top, under, K=1.3 * S, back_hi=(128, 123, 114), back_lo=(48, 46, 42), shadow=0.32)

def opt4():
    """Bottom edge lifts: the masthead rolls up off the score ticks, like the app on scroll."""
    top = vgrad(mono(BAND, BRED, BINK, width=0.62, cy=0.42), 1.08, 0.94)
    under = data_sheet(CREAM, INK, RED, BLUE, (205, 201, 190), ymid=0.86, amp=0.07, x0=0.08, x1=0.94, ticks=False, lw=0.014)
    return peel(top, under, K=0.76 * S, back_hi=(128, 123, 114), back_lo=(48, 46, 42), shadow=0.3, axis=(0, 1))

def opt5():
    """No fold, just the data as the light: the grey band glows behind SC like a horizon."""
    im = Image.new("RGB", (S, S), CREAM)
    a = np.asarray(im, np.float32); yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    # a soft field: Polymarket's band, blurred into a warm horizon
    curve = np.array([0.5 * S - WIN(x / S) * S * 0.22 for x in range(S)], np.float32)[None, :]
    above = np.clip((yy - curve) / (0.5 * S - curve + 1e-3), 0, 1)
    glow = np.exp(-((yy - 0.62 * S) / (0.22 * S)) ** 2)
    tint = np.array([235, 205, 196], np.float32)
    a = a * (1 - 0.55 * glow[..., None]) + tint * 0.55 * glow[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im); a2, b2, *_ = sc.letters(0.02, 0.62, 0.42, 800); sc.fill(im, a2, RED); sc.fill(im, b2, INK)
    dl = data_sheet(CREAM, INK, RED, BLUE, (205, 201, 190), ymid=0.8, amp=0.07, x0=0.14, x1=0.86, ticks=False, lw=0.014, band_a=0.45)
    dm = np.zeros((S, S), bool); dm[int(0.68 * S):int(0.9 * S), :] = True
    im = Image.fromarray(np.where(dm[..., None], np.minimum(np.asarray(im), np.asarray(dl)), np.asarray(im)))
    return im

def opt6():
    """Folded page: the S sits on the page, the C is printed on the paper underneath."""
    top = vgrad(mono(BAND, BRED, BAND), 1.08, 0.94)   # C invisible on top
    under = mono(CREAM, CREAM, INK)
    dl = data_sheet(CREAM, INK, RED, BLUE, (205, 201, 190), ymid=0.84, amp=0.06, x0=0.52, x1=0.95, ticks=False, lw=0.012)
    under = Image.fromarray(np.minimum(np.asarray(under), np.asarray(dl)))
    return peel(top, under, K=1.02 * S, back_hi=(70, 67, 62), back_lo=(18, 17, 16), shadow=0.32)

def letter_peel(bg, scol, ccol, data_under, which, K, hi, lo, axis=(1, 1), shadow=0.4, cy=0.47, q=None):
    a, b, *_ = sc.letters(0.02, 0.66, cy, 800)
    top = Image.new("RGB", (S, S), bg); sc.fill(top, a, scol); sc.fill(top, b, ccol)
    under = top.copy()
    m = {"S": a, "C": b, "SC": Image.fromarray(np.maximum(np.asarray(a), np.asarray(b)))}[which]
    # under each lifted letter: the page, with the game printed on it
    under = Image.fromarray(np.where((np.asarray(m)[..., None] > 127), np.asarray(data_under), np.asarray(top)).astype(np.uint8))
    if q is not None:
        yy, xx = np.nonzero(np.asarray(m) > 127); K = float(np.quantile(axis[0] * xx + axis[1] * yy, q))
    return peel_mask(top, under, m, K, hi, lo, shadow, axis)

def opt7():
    """The C lifts at its tail like a sticker; the game is printed on the paper beneath it."""
    dl = data_sheet(CREAM, INK, RED, BLUE, (205, 201, 190), ymid=0.585, amp=0.025, x0=0.08, x1=0.95, ticks=False, lw=0.024, band_a=0.8)
    return vgrad(letter_peel(CREAM, RED, INK, dl, "C", K=0, q=0.72, hi=(252, 250, 244), lo=(168, 164, 154)), 1.02, 0.96)

def opt8():
    """On the masthead: the C's corner curls up, showing red and blue score ticks underneath."""
    dl = data_sheet(BAND, BINK, BRED, BBLUE, (90, 88, 82), ymid=0.585, amp=0.025, x0=0.08, x1=0.95, ticks=False, lw=0.024, band_a=0.8)
    return vgrad(letter_peel(BAND, BRED, BINK, dl, "C", K=0, q=0.72, hi=(232, 228, 216), lo=(120, 116, 108)), 1.08, 0.94)

def opt9():
    """The S lifts at its foot; the game shows through where it was."""
    dl = data_sheet(BAND, BINK, BRED, BBLUE, (90, 88, 82), ymid=0.55, amp=0.16, x0=0.04, x1=0.97, ticks=False, lw=0.016)
    return vgrad(letter_peel(BAND, BRED, BINK, dl, "S", K=0.82 * S, hi=(240, 178, 168), lo=(140, 80, 72), axis=(1, 1.4)), 1.08, 0.94)

OPTS = [opt1, opt2, opt4, opt5, opt7, opt8]
NAMES = ["1  Corner turned", "2  Paper lifts off the night", "3  Masthead rolls up",
         "4  The band as horizon", "5  The C lifts, on paper", "6  The C lifts, on the masthead"]

def rounded(im, size):
    t = im.resize((size, size), Image.LANCZOS); m = Image.new("L", (size, size))
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size - 1, size - 1), int(size * 0.225), fill=255); return t, m

if __name__ == "__main__":
    from PIL import ImageFont
    ims = [f() for f in OPTS]
    for i, im in enumerate(ims): im.save(os.path.join(OUT, "opt%d.png" % (i + 1)))
    T, pad, cols = 4, 0, 0
    T, pad, cols = 300, 36, 3; rows = 2
    sheet = Image.new("RGB", (cols * (T + pad) + pad, rows * (T + 130) + pad), (226, 224, 218)); d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype(sc.FONT, 17); f.set_variation_by_axes([500])
    for i, im in enumerate(ims):
        cx, cy = pad + (i % cols) * (T + pad), pad + (i // cols) * (T + 130)
        t, m = rounded(im, T); sheet.paste(t, (cx, cy), m)
        s1, m1 = rounded(im, 60); sheet.paste(s1, (cx, cy + T + 14), m1)
        s2, m2 = rounded(im, 40); sheet.paste(s2, (cx + 72, cy + T + 24), m2)
        d.text((cx + 124, cy + T + 34), NAMES[i], font=f, fill=(40, 40, 38))
    sheet.save(os.path.join(OUT, "sheet.png")); print("ok")
