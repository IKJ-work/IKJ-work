"""Procedural mascot animation built from the 4 original frames (f0-f3 PNGs).
Layers: flat bg plate + rotating hand/forearm (wave) + eye patch from closed-eye frame (blink)
+ sleeve overlay + vertical breathing warp (anchored at laptop). Run: python3 -I build_mascot.py FRAMES_DIR OUT_DIR"""
import sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
src, out = sys.argv[1], sys.argv[2]
BG = (13, 17, 23)
f1 = Image.open(f'{src}/f1.png').convert('RGB')
f2 = Image.open(f'{src}/f2.png').convert('RGB')
W, H = f1.size

def flatten(im):
    a = np.asarray(im).astype(int)
    near = (np.abs(a - np.array(BG)).sum(2) < 40)
    m = Image.fromarray((near * 255).astype('uint8'))
    seeds = [(0, 0), (W-1, 0), (0, H-1), (W-1, H-1), (110, 60)]
    ff = Image.fromarray(np.where(near, 255, 0).astype('uint8'))
    for s in seeds:
        if ff.getpixel(s) == 255: ImageDraw.floodfill(ff, s, 128)
    bgm = np.asarray(ff) == 128
    a2 = np.asarray(im).copy(); a2[bgm] = BG
    return Image.fromarray(a2), bgm
f1, _ = flatten(f1); f2, _ = flatten(f2)

a1 = np.asarray(f1).astype(int)
yy, xx = np.mgrid[0:H, 0:W]
skin = (a1[..., 0] > 150) & (a1[..., 0] - a1[..., 2] > 25)
box = (xx > 105) & (xx < 180) & (yy > 70) & (yy < 184)
hand = skin & box
# plate: hand removed
hd = np.asarray(Image.fromarray((hand*255).astype('uint8')).filter(ImageFilter.MaxFilter(7))) > 0
hd &= (xx < 178) & (yy < 178) & ((a1[..., 0] - a1[..., 2]) > 6)
plate = np.asarray(f1).copy(); plate[hand | hd] = BG
# hand layer, extended 8px below the cuff so it tucks under the sleeve
la = np.zeros((H, W, 4), 'uint8'); la[..., :3] = a1; la[hand | hd, 3] = 255
for x in range(105, 180):
    if hand[181, x]:
        for y in range(182, 190): la[y, x] = la[181, x]
hand_layer = Image.fromarray(la, 'RGBA').filter(ImageFilter.GaussianBlur(0))
# sleeve overlay (drawn above hand): sleeve pixels = lit, non-skin, below wrist
lum = a1.sum(2)
sleeve = (~skin) & (yy >= 172) & (xx > 100) & (xx < 180) & (lum > 85)
ov = np.zeros((H, W, 4), 'uint8'); ov[..., :3] = a1; ov[sleeve, 3] = 255
overlay = Image.fromarray(ov, 'RGBA').filter(ImageFilter.GaussianBlur(0.6))
PIV = (145, 182)

# eye patches (frames are aligned at the face: measured offset 0,0)
def eye_mask(boxes):
    m = Image.new('L', (W, H), 0); d = ImageDraw.Draw(m)
    for b in boxes: d.ellipse(b, fill=255)
    return m.filter(ImageFilter.GaussianBlur(2.2))
emask = eye_mask([(204, 85, 240, 116), (251, 79, 291, 109)])

def smooth(x): return x * x * (3 - 2 * x)
FPS, N = 20, 100
frames = []
for i in range(N):
    t = i / FPS
    # wave: 3 cycles 0.4s-2.6s, envelope ramps in/out; angle in 0..16 deg CCW (matches original frame 0 tilt)
    u = (t - 0.4) / 2.2
    ang = 0.0
    if 0 <= u <= 1:
        env = math.sin(math.pi * u) ** 0.6
        ang = env * 8 * (1 - math.cos(2 * math.pi * 3 * u))
    img = Image.fromarray(plate, 'RGB').convert('RGBA')
    rot = hand_layer.rotate(ang, resample=Image.BICUBIC, center=PIV)
    img.alpha_composite(rot); img.alpha_composite(overlay)
    img = img.convert('RGB')
    # blink: closed amount at t=1.5s and 3.9s, 4 steps
    c = 0.0
    for t0 in (1.5, 3.9):
        k = round((t - t0) * FPS)
        if 0 <= k < 4: c = (0.5, 1.0, 1.0, 0.5)[k] if False else (0.3, 1.0, 1.0, 0.3)[k]
    if c > 0:
        closed = Image.composite(f2, img, emask)
        img = Image.blend(img, closed, c)
    # breathing: rows above laptop (y<238) shift up to 1.4px, loop-seamless
    arr = np.asarray(img).astype(float)
    amp = 1.4 * (0.5 - 0.5 * math.cos(2 * math.pi * i / N))
    ys = np.arange(H, dtype=float)
    wgt = np.clip((238 - ys) / 200, 0, 1); wgt = wgt * wgt * (3 - 2 * wgt)
    src_y = np.clip(ys + amp * wgt, 0, H - 1)
    y0 = np.floor(src_y).astype(int); y1 = np.minimum(y0 + 1, H - 1); fr = (src_y - y0)[:, None, None]
    arr = arr[y0] * (1 - fr) + arr[y1] * fr
    img = Image.fromarray(arr.round().astype('uint8')).crop((80, 0, 400, 320))
    img.save(f'{out}/m{i:03d}.png')
