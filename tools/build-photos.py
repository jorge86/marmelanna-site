#!/usr/bin/env python3
"""
Χτίζει ΟΛΕΣ τις φωτογραφίες του site από τις πηγές, με ενιαία επεξεργασία.

    python3 tools/build-photos.py

Γιατί script και όχι χειροκίνητα: όταν κάθε φωτογραφία περνάει από δικές της
ρυθμίσεις, το σύνολο δεν δένει — άλλη θερμοκρασία, άλλη φωτεινότητα, άλλο
βάθος πεδίου. Εδώ όλες περνούν από τα ίδια τρία στάδια:

  1. Κοπή στο ratio της θέσης
  2. Βάθος πεδίου (εκτός από το hero, που είναι τοπίο)
  3. Εξισορρόπηση προς τον μέσο όρο του συνόλου, και μετά ΜΙΑ κοινή διόρθωση

Το στάδιο 3 είναι αυτό που δίνει τη συνοχή: μετριέται το μέσο χρώμα και η μέση
φωτεινότητα κάθε λήψης στο κέντρο του κάδρου, και κάθε μία τραβιέται μερικώς
προς τον μέσο όρο όλων. Μερικώς (BALANCE_STRENGTH) — με πλήρη διόρθωση τα
λεμόνια θα έχαναν το κίτρινό τους και οι λωτοί το πορτοκαλί τους.

Απαιτεί Pillow:  python3 -m pip install --user Pillow
Το vazo.heic μετατρέπεται πρώτα με sips (το Pillow δεν διαβάζει HEIC).
"""
import io, pathlib, subprocess, sys
from PIL import Image, ImageEnhance, ImageFilter, ImageChops, ImageStat

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC  = ROOT.parent / "Frouta Photos"
OUT  = ROOT / "images"

# Η εξισορρόπηση αφορά ΧΡΩΜΑ, όχι φωτεινότητα. Ένα κοντινό σε σκούρα
# δαμάσκηνα είναι νόμιμα πιο σκοτεινό από έναν ηλιόλουστο οπωρώνα· αν τραβήξεις
# και τη φωτεινότητα προς τον μέσο όρο, καίγονται τα φωτεινά μέρη.
CHROMA_STRENGTH = 0.35    # πόσο διορθώνεται η απόχρωση προς τον μέσο όρο
CHROMA_CLAMP    = (0.93, 1.08)
LUMA_STRENGTH   = 0.12    # πολύ ήπια εξομάλυνση φωτεινότητας
LUMA_CLAMP      = (0.94, 1.08)
GRADE = dict(warm=1.035, bright=1.02, contrast=1.10, saturation=1.06)

# source, crop στην πηγή, ratio, πλάτος(η), όνομα, εστίαση(cx,cy,rx,ry), blur, budget
PHOTOS = [
  ("esperidoeidi.jpg",   (0,0,1800,1350),   3/2, [800,1300], "orchard-{w}.jpg",             None,                    0,  270_000),
  ("vanilies.jpg",       (0,150,1197,1048), 4/3, [900],      "step-1-branch.jpg",           (0.55,0.50,0.55,0.58),   9,  150_000),
  ("sygkomidh 3.png",    (0,560,852,1199),  4/3, [900],      "step-2-harvesting.jpg",       (0.35,0.45,0.55,0.60),   9,  190_000),
  ("damaskina4.jpg",     (45,40,639,486),   4/3, [900],      "step-3-washed.jpg",           (0.48,0.50,0.58,0.58),   8,  150_000),
  ("vazo.jpg",           (0,180,2317,1918), 4/3, [1000],     "step-4-jar.jpg",              (0.32,0.50,0.62,0.62),   5,  150_000),
  ("λεμονι τελικο.png",  None,              3/2, [1000],     "season-spring-lemon.jpg",     (0.63,0.50,0.50,0.55),   8,  150_000),
  ("krystalia.jpg",      (0,371,1197,1169), 3/2, [1000],     "season-summer-pears.jpg",     (0.55,0.52,0.56,0.58),   9,  160_000),
  ("damaskina3.jpg",     None,              3/2, [1000],     "season-autumn-branch.jpg",    (0.46,0.50,0.55,0.58),   9,  150_000),
  ("esperidoeidi.jpg",   (0,0,930,620),     3/2, [1000],     "season-winter-oranges.jpg",   (0.42,0.40,0.56,0.60),   7,  200_000),
]

# ── βάθος πεδίου ──────────────────────────────────────────────────────────
def radial_mask(w, h, cx, cy, rx, ry, feather=0.8):
    gw = 180; gh = max(1, int(180 * h / w)); px = []
    for y in range(gh):
        ny = (y + 0.5) / gh
        for x in range(gw):
            nx = (x + 0.5) / gw
            d = (((nx-cx)/rx)**2 + ((ny-cy)/ry)**2) ** 0.5
            t = min(1.0, max(0.0, (d - 1.0) / feather))
            px.append(int(255 * (1 - t*t*(3 - 2*t))))
    m = Image.new("L", (gw, gh)); m.putdata(px)
    return m.resize((w, h), Image.BICUBIC)

def depth_of_field(im, cx, cy, rx, ry, blur, vignette=0.10):
    """Δύο στρώσεις θολώματος· μία μόνο αφήνει ορατό περίγραμμα."""
    w, h = im.size
    soft = im.filter(ImageFilter.GaussianBlur(blur * 0.45))
    deep = im.filter(ImageFilter.GaussianBlur(blur))
    out = Image.composite(soft, deep, radial_mask(w, h, cx, cy, rx*1.55, ry*1.55, 0.8))
    out = Image.composite(im, out, radial_mask(w, h, cx, cy, rx, ry, 0.56))
    v = radial_mask(w, h, cx, cy, 0.82, 0.82, 1.0).point(
        lambda p: int(255 - (255 - p) * vignette))
    return ImageChops.multiply(out, Image.merge("RGB", (v, v, v)))

# ── βοηθητικά ─────────────────────────────────────────────────────────────
def fit(im, ratio):
    cw, ch = im.size; th = int(round(cw / ratio))
    if th <= ch: return im.crop((0, 0, cw, th))
    tw = int(round(ch * ratio)); return im.crop(((cw-tw)//2, 0, (cw-tw)//2+tw, ch))

def core_mean(im):
    """Μέσο RGB στο κέντρο — οι άκρες είναι θολές και σκοτεινές από το vignette."""
    w, h = im.size
    return ImageStat.Stat(im.crop((int(w*.2), int(h*.2), int(w*.8), int(h*.8)))).mean

def apply_gain(im, gains):
    return Image.merge("RGB", [
        ch.point(lambda v, g=g: min(255, max(0, int(v * g))))
        for ch, g in zip(im.split(), gains)])

def grade(im):
    r, g, b = im.split()
    r = r.point(lambda v: min(255, int(v * GRADE["warm"])))
    b = b.point(lambda v: int(v * (2 - GRADE["warm"])))
    im = Image.merge("RGB", (r, g, b))
    im = ImageEnhance.Brightness(im).enhance(GRADE["bright"])
    im = ImageEnhance.Contrast(im).enhance(GRADE["contrast"])
    return ImageEnhance.Color(im).enhance(GRADE["saturation"])

def save_within(im, path, budget):
    for q in (86, 84, 82, 80, 78, 76, 74):
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
        if buf.tell() <= budget: break
    path.write_bytes(buf.getvalue())
    return q, buf.tell()

# ── κυρίως ────────────────────────────────────────────────────────────────
def main():
    heic = SRC / "vazo.heic"
    if heic.exists() and not (SRC / "vazo.jpg").exists():
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "best",
                        str(heic), "--out", str(SRC / "vazo.jpg")],
                       check=True, capture_output=True)
        print("vazo.heic → vazo.jpg (sips)")

    # Στάδιο 1-2: κοπή, μέγεθος, βάθος πεδίου
    built = []
    for name, box, ratio, widths, tmpl, focus, blur, budget in PHOTOS:
        base = Image.open(SRC / name).convert("RGB")
        if box: base = base.crop(box)
        base = fit(base, ratio)
        for w in widths:
            im = base.resize((w, int(round(w / ratio))), Image.LANCZOS)
            if focus: im = depth_of_field(im, *focus, blur)
            built.append([tmpl.format(w=w) if "{w}" in tmpl else tmpl, im, budget])

    # Στάδιο 3: εξισορρόπηση προς τον μέσο όρο του συνόλου, μετά κοινή διόρθωση
    def luma(m): return 0.299*m[0] + 0.587*m[1] + 0.114*m[2]
    means  = [core_mean(im) for _, im, _ in built]
    ratios = [[m[c] / luma(m) for c in range(3)] for m in means]          # απόχρωση
    t_ratio = [sum(r[c] for r in ratios) / len(ratios) for c in range(3)]
    t_luma  = sum(luma(m) for m in means) / len(means)
    print(f"\nαπόχρωση στόχος  {t_ratio[0]:.3f}/{t_ratio[1]:.3f}/{t_ratio[2]:.3f}"
          f"   φωτεινότητα στόχος {t_luma:.0f}\n")

    def clamp(v, lo, hi): return lo if v < lo else (hi if v > hi else v)

    for (dst, im, budget), m, r in zip(built, means, ratios):
        lg = clamp(1 + (t_luma/luma(m) - 1) * LUMA_STRENGTH, *LUMA_CLAMP)
        gains = [clamp(1 + (t_ratio[c]/r[c] - 1) * CHROMA_STRENGTH, *CHROMA_CLAMP) * lg
                 for c in range(3)]
        im = grade(apply_gain(im, gains))
        q, size = save_within(im, OUT / dst, budget)
        print(f"{dst:32} {im.size[0]:>4}x{im.size[1]:<4} q{q}  {size//1024:>3} KB"
              f"   gain {gains[0]:.3f}/{gains[1]:.3f}/{gains[2]:.3f}")

if __name__ == "__main__":
    sys.exit(main())
