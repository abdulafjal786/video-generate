"""Small drawing layer over Pillow.

All coordinates are in *design pixels* (the output resolution). Everything is
drawn on a supersampled image (SS x larger) and scaled down per frame, which
gives smooth anti-aliased lines.
"""
import math
import os
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

SS = 2  # supersampling factor
ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


@lru_cache(maxsize=64)
def font(name, size):
    """Load a font by file name (bundled or system) at a design-pixel size."""
    candidates = [name, os.path.join(ASSETS, "fonts", name),
                  os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", name)]
    for c in candidates:
        if c and os.path.exists(c):
            try:
                return ImageFont.truetype(c, max(1, int(size * SS)))
            except OSError:
                pass
    return ImageFont.truetype(os.path.join(ASSETS, "fonts", "NotoSans.ttf"), max(1, int(size * SS)))


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out_back(t, s=1.70158):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def mix(c1, c2, t):
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


class Canvas:
    def __init__(self, img):
        self.img = img
        self.d = ImageDraw.Draw(img, "RGBA")

    # --- primitives (design coordinates) -----------------------------------
    @staticmethod
    def _p(pt):
        return (pt[0] * SS, pt[1] * SS)

    def line(self, pts, color, width, joint=True):
        pts = [self._p(p) for p in pts]
        w = max(1, int(width * SS))
        self.d.line(pts, fill=color, width=w, joint="curve" if joint else None)
        r = w / 2.0
        for x, y in (pts[0], pts[-1]):  # round caps
            self.d.ellipse((x - r, y - r, x + r, y + r), fill=color)

    def poly(self, pts, fill=None, outline=None, width=1):
        pts = [self._p(p) for p in pts]
        self.d.polygon(pts, fill=fill)
        if outline is not None:
            self.d.line(pts + [pts[0]], fill=outline, width=max(1, int(width * SS)), joint="curve")

    def circle(self, c, r, fill=None, outline=None, width=1):
        x, y = c[0] * SS, c[1] * SS
        r *= SS
        self.d.ellipse((x - r, y - r, x + r, y + r), fill=fill, outline=outline,
                       width=max(1, int(width * SS)) if outline else 0)

    def ellipse(self, box, fill=None, outline=None, width=1):
        x0, y0, x1, y1 = [v * SS for v in box]
        if x1 < x0:
            x0, x1 = x1, x0
        if y1 < y0:
            y0, y1 = y1, y0
        self.d.ellipse((x0, y0, x1, y1), fill=fill, outline=outline,
                       width=max(1, int(width * SS)) if outline else 0)

    def rect(self, box, fill=None, outline=None, width=1, radius=0):
        x0, y0, x1, y1 = [v * SS for v in box]
        self.d.rounded_rectangle((min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)),
                                 radius=radius * SS, fill=fill, outline=outline,
                                 width=max(1, int(width * SS)) if outline else 0)

    def arc(self, c, r, start, end, color, width):
        x, y = c[0] * SS, c[1] * SS
        r *= SS
        self.d.arc((x - r, y - r, x + r, y + r), start, end, fill=color, width=max(1, int(width * SS)))

    def text_size(self, text, fnt):
        b = self.d.textbbox((0, 0), text, font=fnt)
        return (b[2] - b[0]) / SS, (b[3] - b[1]) / SS

    def text(self, xy, text, fnt, fill, anchor="la", stroke=0, stroke_fill=None):
        self.d.text(self._p(xy), text, font=fnt, fill=fill, anchor=anchor,
                    stroke_width=int(stroke * SS), stroke_fill=stroke_fill)

    def paste(self, im, xy):
        self.img.paste(im, (int(xy[0] * SS), int(xy[1] * SS)), im if im.mode == "RGBA" else None)


def polar(cx, cy, r, deg):
    a = math.radians(deg)
    return (cx + r * math.cos(a), cy + r * math.sin(a))


def new_image(w, h, color):
    return Image.new("RGB", (int(w * SS), int(h * SS)), color)
