from PIL import Image
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
IMG_DIR = BASE / 'static' / 'img'

thumbs = [
    ('Cellinsurance Logo.png', 'cellinsurance_thumb.png'),
    ('Cellmed Logo.png', 'cellmed_thumb.png'),
    ('Nectacare Logo.png', 'nectacare_thumb.png'),
]

IMG_DIR.mkdir(parents=True, exist_ok=True)

for src_name, dst_name in thumbs:
    src = IMG_DIR / src_name
    dst = IMG_DIR / dst_name
    if not src.exists():
        print(f"Source not found: {src}")
        continue
    try:
        with Image.open(src) as im:
            # preserve aspect, set max height 64
            max_h = 64
            w, h = im.size
            if h > max_h:
                new_w = int(w * (max_h / h))
                im = im.resize((new_w, max_h), Image.LANCZOS)
            im.save(dst, format='PNG', optimize=True)
            print(f"Wrote {dst} ({dst.stat().st_size} bytes)")
    except Exception as e:
        print(f"Failed {src}: {e}")
