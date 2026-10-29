# Mascot animation source

- `original-4-frame-mascot.gif` and `original-frames/` — the original four-pose mascot.
- `build_mascot.py` — builds the 100-frame, 20 fps loop from those poses: the hand and forearm rotate about the wrist (wave), eye patches from the closed-eye pose are blended in (blink), and a small vertical warp anchored at the laptop gives idle breathing.
- Encode: `ffmpeg -framerate 20 -i m%03d.png -vf "split[a][b];[a]palettegen=max_colors=128:stats_mode=full[p];[b][p]paletteuse=dither=none:diff_mode=rectangle" -loop 0 developer-mascot.gif`
