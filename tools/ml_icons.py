"""Margin Line icon studies. Run: python3 tools/ml_icons.py -> /tmp/ml/*.png + sheet.

Every option is drawn from the app's own marks: the warm masthead ground, the
pale red (home) and pale blue (visitors), cream ink, the hairline zero rule,
and the margin as a step line. Drawn at 4x and reduced, so edges stay clean."""
import os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
GAR = os.path.join(HERE, "..", "fonts", "EBGaramond[wght].ttf")
SRC = os.path.join(HERE, "..", "fonts", "SourceSerif4[opsz,wght].ttf")
BAND, RED, BLUE, CREAM, GRAY, PAPER, INK = (29, 28, 26), (227, 134, 124), (143, 181, 226), (255, 255, 248), (161, 156, 143), (255, 255, 248), (38, 38, 36)
DRED, DBLUE = (178, 64, 52), (52, 96, 160)
N = 1024; K = 4; S = N * K
OUT = "/tmp/ml"; os.makedirs(OUT, exist_ok=True)

def font(path, px, w=600, opsz=None):
    f = ImageFont.truetype(path, px, layout_engine=ImageFont.Layout.RAQM)
    try:
        axes = f.get_variation_axes(); vals = []
        for a in axes:
            nm = a.get("name", b"")
            nm = nm.decode() if isinstance(nm, bytes) else str(nm)
            vals.append(w if "eight" in nm else (opsz or a.get("default", 12)) if "ptical" in nm else a.get("default", 0))
        f.set_variation_by_axes(vals)
    except Exception: pass
    return f

def canvas(bg): return Image.new("RGB", (S, S), bg)
def done(im): return im.resize((N, N), Image.LANCZOS)
def sub(im, bg_top=1.06, bg_bot=0.94):
    """A whisper of light from above: the only 'dimension' allowed."""
    import numpy as np
    a = np.asarray(im, np.float32); k = np.linspace(bg_top, bg_bot, im.height)[:, None, None]
    return Image.fromarray(np.clip(a * k, 0, 255).astype("uint8"))

def step_points(x0, x1, ymid, amp, series):
    n = len(series) - 1; pts = [(x0, ymid)]; prev = 0
    for i, m in enumerate(series):
        x = x0 + (x1 - x0) * i / n
        pts += [(x, ymid - prev * amp), (x, ymid - m * amp)]; prev = m
    pts.append((x1, ymid - prev * amp)); return pts

def draw_margin(d, pts, ymid, w, home=RED, away=BLUE):
    """The step line in two colours: red above the rule (home leads), blue below."""
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        if ya == yb:
            d.line([(xa, ya), (xb, yb)], fill=home if ya <= ymid else away, width=w)
        else:   # a vertical step: split at the rule
            if (ya - ymid) * (yb - ymid) < 0:
                d.line([(xa, ya), (xa, ymid)], fill=home if ya < ymid else away, width=w)
                d.line([(xa, ymid), (xb, yb)], fill=home if yb < ymid else away, width=w)
            else:
                d.line([(xa, ya), (xb, yb)], fill=home if min(ya, yb) < ymid else away, width=w)
    for (x, y) in pts[1:-1]:   # square the corners
        d.rectangle([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=home if y < ymid else away if y > ymid else home)

def text_mask(txt, f):
    m = Image.new("L", (S * 2, S)); ImageDraw.Draw(m).text((S // 10, S // 2), txt, font=f, fill=255, anchor="ls")
    return m.crop(m.getbbox())

SER = [0, 0.38, 0.38, -0.32, -0.32, 0.12, 0.12, 0.62, 0.62, 1.0]

def opt_line():
    """1 · The line alone: no letters. The zero rule in cream, the margin
    stepping across it, red above and blue below, ending in the live dot."""
    im = canvas(BAND); d = ImageDraw.Draw(im)
    ym = S * 0.56; x0, x1 = S * 0.17, S * 0.80; amp = S * 0.25
    d.line([(S * 0.14, ym), (S * 0.86, ym)], fill=GRAY, width=int(S * 0.008))
    pts = step_points(x0, x1, ym, amp, SER)
    draw_margin(d, pts, ym, int(S * 0.04))
    ex, ey = pts[-1]; r = S * 0.044; d.ellipse([ex - r, ey - r, ex + r, ey + r], fill=CREAM)
    return sub(done(im), 1.08, 0.93)

def opt_m_line():
    """2 · The M is the line: the margin climbs, dips, climbs and dips, and
    the path it takes is the letter M."""
    im = canvas(BAND); d = ImageDraw.Draw(im)
    ym = S * 0.72; w = int(S * 0.055)
    L, R, T, V = S * 0.22, S * 0.78, S * 0.28, S * 0.52
    pts = [(L, ym), (L, T), (S * 0.36, T), (S * 0.36, V), (S * 0.64, V), (S * 0.64, T), (R, T), (R, ym)]
    d.line([(S * 0.13, ym), (S * 0.87, ym)], fill=GRAY, width=int(S * 0.008))
    d.line(pts, fill=RED, width=w, joint=None)
    for (x, y) in pts: d.rectangle([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=RED)
    r = S * 0.045; d.ellipse([R - r, ym - r, R + r, ym + r], fill=CREAM)
    return sub(done(im), 1.08, 0.93)

def opt_ml_rule():
    """3 · ml, set in Garamond italic, sitting on the zero rule, which carries
    on as the margin line once the letters end."""
    im = canvas(BAND); d = ImageDraw.Draw(im)
    f = font(GAR, int(S * 0.56), 500)
    m = Image.new("L", (S, S)); dm = ImageDraw.Draw(m)
    base = S * 0.64
    fi = ImageFont.truetype(GAR, int(S * 0.56));
    try: fi.set_variation_by_axes([520])
    except Exception: pass
    # italic by shear
    tm = Image.new("L", (S, S)); ImageDraw.Draw(tm).text((S * 0.12, base), "ml", font=fi, fill=255, anchor="ls")
    sh = 0.22; tm = tm.transform((S, S), Image.AFFINE, (1, sh, -sh * base, 0, 1, 0), Image.BICUBIC)
    bb = tm.getbbox()
    im.paste(Image.new("RGB", (S, S), CREAM), (0, 0), tm)
    x_end = bb[2] + S * 0.03
    d.line([(S * 0.12, base + S * 0.03), (x_end, base + S * 0.03)], fill=GRAY, width=int(S * 0.008))
    pts = step_points(x_end, S * 0.88, base + S * 0.03, S * 0.2, [0, 0.45, 0.45, -0.4, -0.4, 1.0])
    draw_margin(d, pts, base + S * 0.03, int(S * 0.03))
    ex, ey = pts[-1]; r = S * 0.03; d.ellipse([ex - r, ey - r, ex + r, ey + r], fill=CREAM)
    return sub(done(im), 1.08, 0.93)

def opt_monogram():
    """4 · M and L, the masthead's colours: M in pale red, L in cream, the L's
    foot running out as the margin line."""
    im = canvas(BAND); d = ImageDraw.Draw(im)
    f = font(SRC, int(S * 0.44), 600, 60)
    mm, lm = text_mask("M", f), text_mask("L", f)
    h = mm.height; base = S * 0.64; x = S * 0.1
    im.paste(Image.new("RGB", mm.size, RED), (int(x), int(base - h)), mm)
    lx = int(x + mm.width + S * 0.015)
    im.paste(Image.new("RGB", lm.size, CREAM), (lx, int(base - lm.height)), lm)
    foot_y = base - S * 0.022
    pts = step_points(lx + lm.width - S * 0.01, S * 0.9, foot_y, S * 0.16, [0, 0.55, 0.55, -0.4, -0.4, 1.0])
    draw_margin(d, pts, foot_y, int(S * 0.026))
    ex, ey = pts[-1]; r = S * 0.026; d.ellipse([ex - r, ey - r, ex + r, ey + r], fill=CREAM)
    return sub(done(im), 1.08, 0.93)

def opt_paper():
    """5 · On paper: the light version of 1, the way a line sits in the app's
    pages: ink-dark home red and visitors blue on cream, a fine rule."""
    im = canvas(PAPER); d = ImageDraw.Draw(im)
    ym = S * 0.56; amp = S * 0.25
    d.line([(S * 0.14, ym), (S * 0.86, ym)], fill=(200, 196, 186), width=int(S * 0.008))
    pts = step_points(S * 0.17, S * 0.80, ym, amp, SER)
    draw_margin(d, pts, ym, int(S * 0.04), DRED, DBLUE)
    ex, ey = pts[-1]; r = S * 0.044; d.ellipse([ex - r, ey - r, ex + r, ey + r], fill=INK)
    return sub(done(im), 1.02, 0.95)

def opt_band():
    """6 · Line and band: the margin over Polymarket's grey band of win chance,
    the two marks that are the whole app."""
    im = canvas(BAND); d = ImageDraw.Draw(im, "RGBA")
    ym = S * 0.58; x0, x1 = S * 0.15, S * 0.85; amp = S * 0.26
    band = [(x0 + (x1 - x0) * i / 100, ym - (0.55 * math.sin(i / 100 * 2.6 + 0.2) * (0.5 + 0.5 * i / 100)) * amp) for i in range(101)]
    d.polygon([(x0, ym)] + band + [(x1, ym)], fill=(255, 255, 248, 34))
    d.line(band, fill=(255, 255, 248, 70), width=int(S * 0.006))
    d.line([(S * 0.12, ym), (S * 0.88, ym)], fill=GRAY, width=int(S * 0.007))
    pts = step_points(x0, S * 0.78, ym, amp, SER)
    draw_margin(d, pts, ym, int(S * 0.042))
    ex, ey = pts[-1]; r = S * 0.046; d.ellipse([ex - r, ey - r, ex + r, ey + r], fill=CREAM)
    return sub(done(im), 1.08, 0.93)

def opt_tall():
    """7 · One great step: the simplest possible margin, a lead taken and held:
    the rule, a single rise in red, the dot. Reads at any size."""
    im = canvas(BAND); d = ImageDraw.Draw(im)
    ym = S * 0.64; w = int(S * 0.075)
    d.line([(S * 0.14, ym), (S * 0.86, ym)], fill=GRAY, width=int(S * 0.01))
    pts = [(S * 0.18, ym), (S * 0.42, ym), (S * 0.42, S * 0.34), (S * 0.78, S * 0.34)]
    d.line(pts[:2], fill=CREAM, width=w)
    d.line(pts[1:], fill=RED, width=w)
    for (x, y) in pts[1:3]: d.rectangle([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=RED)
    r = S * 0.06; d.ellipse([S * 0.78 - r, S * 0.34 - r, S * 0.78 + r, S * 0.34 + r], fill=CREAM)
    return sub(done(im), 1.08, 0.93)

def opt_comeback():
    """8 · The comeback: three bold strokes. Even, then behind (blue, below
    the rule), then ahead (red, above), and the dot: a game's whole drama
    in the fewest marks."""
    im = canvas(BAND); d = ImageDraw.Draw(im)
    ym = S * 0.56; w = int(S * 0.07)
    d.line([(S * 0.13, ym), (S * 0.87, ym)], fill=GRAY, width=int(S * 0.01))
    pts = [(S * 0.17, ym), (S * 0.34, ym), (S * 0.34, S * 0.71), (S * 0.53, S * 0.71), (S * 0.53, S * 0.34), (S * 0.79, S * 0.34)]
    d.line(pts[0:2], fill=CREAM, width=w)
    d.line([pts[1], (S * 0.34, ym)], fill=BLUE, width=w)
    d.line([(S * 0.34, ym), pts[2], pts[3], (S * 0.53, ym)], fill=BLUE, width=w)
    d.line([(S * 0.53, ym), pts[4], pts[5]], fill=RED, width=w)
    for (x, y), c in [(pts[2], BLUE), (pts[3], BLUE), (pts[4], RED), ((S * 0.34, ym), BLUE), ((S * 0.53, ym), RED)]:
        d.rectangle([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=c)
    r = S * 0.058; d.ellipse([S * 0.79 - r, S * 0.34 - r, S * 0.79 + r, S * 0.34 + r], fill=CREAM)
    return sub(done(im), 1.08, 0.93)

OPTS = [(opt_line, "1  The line alone"), (opt_band, "2  Line and band"), (opt_paper, "3  The line, on paper"),
        (opt_tall, "4  One great step"), (opt_comeback, "5  The comeback"), (opt_ml_rule, "6  ml on the rule")]

if __name__ == "__main__":
    ims = [(f(), n) for f, n in OPTS]
    for i, (im, n) in enumerate(ims): im.save(os.path.join(OUT, "opt%d.png" % (i + 1)))
    T, pad, cols = 280, 34, 3; rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (T + pad) + pad, rows * (T + 120) + pad), (226, 224, 218)); d = ImageDraw.Draw(sheet)
    lab = font(GAR, 19, 500)
    def rounded(im, s):
        t = im.resize((s, s), Image.LANCZOS); m = Image.new("L", (s, s)); ImageDraw.Draw(m).rounded_rectangle((0, 0, s - 1, s - 1), int(s * 0.225), fill=255); return t, m
    for i, (im, n) in enumerate(ims):
        cx, cy = pad + (i % cols) * (T + pad), pad + (i // cols) * (T + 120)
        t, m = rounded(im, T); sheet.paste(t, (cx, cy), m)
        s1, m1 = rounded(im, 60); sheet.paste(s1, (cx, cy + T + 12), m1)
        s2, m2 = rounded(im, 40); sheet.paste(s2, (cx + 70, cy + T + 22), m2)
        d.text((cx + 120, cy + T + 34), n, font=lab, fill=(40, 40, 38))
    sheet.save(os.path.join(OUT, "sheet.png")); print("ok")
