"""Margin Line icon: "the comeback", ground variations. Run -> /tmp/ml/cb*.png + cb_sheet.png"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ml_icons import S, N, BAND, RED, BLUE, CREAM, GRAY, PAPER, INK, DRED, DBLUE, GAR, OUT, font

yy, xx = np.mgrid[0:N, 0:N].astype(np.float32) / N

def mix(c0, c1, t):
    t = t[..., None]; return np.array(c0, np.float32) * (1 - t) + np.array(c1, np.float32) * t

def ground(kind):
    if kind == "flat": a = mix(BAND, BAND, yy)
    elif kind == "vertical": a = mix((50, 47, 43), (17, 16, 15), yy)                       # light from above
    elif kind == "glow":                                                               # warmth around the lead
        r = np.sqrt((xx - 0.79) ** 2 + (yy - 0.34) ** 2); a = mix((58, 50, 45), (16, 15, 14), np.clip(r / 0.95, 0, 1))
    elif kind == "split":                                                              # the two sides, barely
        top = mix((52, 38, 36), (30, 28, 26), np.clip(yy / 0.56, 0, 1)); bot = mix((28, 28, 28), (24, 30, 40), np.clip((yy - 0.56) / 0.44, 0, 1))
        a = np.where((yy < 0.56)[..., None], top, bot)
    elif kind == "diagonal": a = mix((48, 45, 40), (14, 14, 15), np.clip((xx * 0.4 + yy * 0.8) / 1.2, 0, 1))
    elif kind == "paper": a = mix((255, 255, 250), (236, 232, 220), yy)
    elif kind == "paperglow":
        r = np.sqrt((xx - 0.79) ** 2 + (yy - 0.34) ** 2); a = mix((255, 252, 244), (228, 224, 212), np.clip(r / 1.0, 0, 1))
    return Image.fromarray(np.clip(a + np.random.default_rng(1).normal(0, 0.6, a.shape), 0, 255).astype("uint8"))

def marks(light=False):
    """The comeback strokes on a transparent layer, drawn at 4x."""
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    red, blue, even, rule = (DRED, DBLUE, INK, (190, 184, 170)) if light else (RED, BLUE, CREAM, GRAY)
    ym = S * 0.56; w = int(S * 0.07)
    d.line([(S * 0.13, ym), (S * 0.87, ym)], fill=rule, width=int(S * 0.01))
    p = [(S * 0.17, ym), (S * 0.34, ym), (S * 0.34, S * 0.71), (S * 0.53, S * 0.71), (S * 0.53, S * 0.34), (S * 0.79, S * 0.34)]
    d.line(p[0:2], fill=even, width=w)
    d.line([(S * 0.34, ym), p[2], p[3], (S * 0.53, ym)], fill=blue, width=w)
    d.line([(S * 0.53, ym), p[4], p[5]], fill=red, width=w)
    for (x, y), c in [(p[2], blue), (p[3], blue), (p[4], red), ((S * 0.34, ym), blue), ((S * 0.53, ym), red)]:
        d.rectangle([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=c)
    r = S * 0.058; d.ellipse([S * 0.79 - r, S * 0.34 - r, S * 0.79 + r, S * 0.34 + r], fill=even)
    return im.resize((N, N), Image.LANCZOS)

def icon(kind, light=False):
    g = ground(kind).convert("RGBA"); g.alpha_composite(marks(light)); return g.convert("RGB")

OPTS = [("flat", False, "A  As it is (flat)"), ("vertical", False, "B  Light from above"), ("glow", False, "C  Glow at the lead"),
        ("split", False, "D  Two sides, barely"), ("diagonal", False, "E  Corner light"), ("paper", True, "F  Paper"), ("paperglow", True, "G  Paper, glow")]

if __name__ == "__main__":
    ims = []
    for k, light, n in OPTS:
        im = icon(k, light); im.save(os.path.join(OUT, "cb_%s.png" % k)); ims.append((im, n))
    T, pad, cols = 280, 34, 4; rows = (len(ims) + cols - 1) // cols
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
    sheet.save(os.path.join(OUT, "cb_sheet.png")); print("ok")
