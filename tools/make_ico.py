from PIL import Image
from pathlib import Path

src = Path("assets/appicona.png")
dst = Path("assets/worker_hotkeys.ico")

img = Image.open(src).convert("RGBA")

sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
img.save(dst, format="ICO", sizes=sizes)

print("OK:", dst.resolve())
