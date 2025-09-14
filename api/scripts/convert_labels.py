import os
import json
import numpy as np
from pathlib import Path
from PIL import Image
from ultralytics.utils import TQDM
from ultralytics.data.split import autosplit
from ultralytics.utils.ops import xyxy2xywhn

# Paths
ROOT = Path("datasets/xView")
GEOJSON = ROOT / "xView_train.geojson"
TRAIN_DIR = ROOT / "train_images"
VAL_DIR = ROOT / "val_images"
LABELS_DIR = ROOT / "labels" / "train"

# xView classes 11–94 mapped to 0–59
xview_class2index = [
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 0, 1, 2, -1, 3, -1, 4, 5, 6, 7, 8, -1, 9, 10, 11,
    12, 13, 14, 15, -1, -1, 16, 17, 18, 19, 20, 21, 22, -1, 23, 24, 25, -1, 26, 27, -1, 28, -1,
    29, 30, 31, 32, 33, 34, 35, 36, 37, -1, 38, 39, 40, 41, 42, 43, 44, 45, -1, -1, -1, -1, 46,
    47, 48, 49, -1, 50, 51, -1, 52, -1, -1, -1, 53, 54, -1, 55, -1, -1, 56, -1, 57, -1, 58, 59
]

def convert_labels(geojson_path=GEOJSON):
    """Convert xView geoJSON labels to YOLO format."""
    with open(geojson_path, encoding="utf-8") as f:
        print(f"Loading {geojson_path}...")
        data = json.load(f)

    # Clean and recreate labels directory
    os.system(f"rm -rf {LABELS_DIR}")
    LABELS_DIR.mkdir(parents=True, exist_ok=True)

    shapes = {}
    for feature in TQDM(data["features"], desc="Converting labels"):
        p = feature["properties"]
        if not p["bounds_imcoords"]:
            continue

        image_id = p["image_id"]
        img_path = TRAIN_DIR / image_id
        if not img_path.exists():
            continue  # some .tif files are missing in xView dataset

        try:
            # Parse box and class
            box = np.array([int(num) for num in p["bounds_imcoords"].split(",")])
            cls = xview_class2index[int(p["type_id"])]
            if cls < 0:
                continue

            # Get image size once
            if image_id not in shapes:
                shapes[image_id] = Image.open(img_path).size
            w, h = shapes[image_id]

            # Convert to YOLO format
            box = xyxy2xywhn(box[None].astype(float), w=w, h=h, clip=True)

            # Save label
            with open((LABELS_DIR / image_id).with_suffix(".txt"), "a", encoding="utf-8") as f:
                f.write(f"{cls} {' '.join(f'{x:.6f}' for x in box[0])}\n")

        except Exception as e:
            print(f"WARNING: skipping {image_id}: {e}")


if __name__ == "__main__":
    convert_labels()

    # Reorganize images into 'images/train' and 'images/val'
    IMAGES_DIR = ROOT / "images"
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    (TRAIN_DIR).rename(IMAGES_DIR / "train")
    (VAL_DIR).rename(IMAGES_DIR / "val")

    # Autosplit (90% train / 10% val)
    autosplit(IMAGES_DIR / "train")

    print("\n✅ Conversion complete!")
    print(f"Images in: {IMAGES_DIR}")
    print(f"Labels in: {LABELS_DIR}")
