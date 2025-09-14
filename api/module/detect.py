# --- Detection implementation -------------------------------------------------
import os
import uuid
import shutil
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, File, HTTPException, UploadFile, FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

try:
    from ultralytics import YOLO 
    import cv2 
    import numpy as np 
except Exception: 
    YOLO = None 
    cv2 = None
    np = None

try:
    from PIL import Image
except Exception:
    Image = None


# Paths and configuration
BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"
UPLOADS_DIR = PUBLIC_DIR / "uploads"
ANNOTATED_DIR = PUBLIC_DIR / "annotated"
SUPPORTED_EXTS = {".tif", ".tiff", ".jp2", ".jpg", ".jpeg", ".hdf", ".png"}
MODEL_PATH = os.getenv("DETECT_MODEL_PATH", str(BASE_DIR / "../model/xView-Yolo11n/weights/best.pt"))

# Globals
yolo_model = None

# Router to be included by the main FastAPI app under /api
router = APIRouter()


def _ensure_dirs() -> None:
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    ANNOTATED_DIR.mkdir(parents=True, exist_ok=True)


def _ext_ok(filename: str) -> bool:
    return Path(filename).suffix.lower() in SUPPORTED_EXTS


def _random_name(suffix: str = ".png") -> str:
    return f"{uuid.uuid4().hex}{suffix}"


def _save_upload(file: UploadFile, dest_path: Path) -> None:
    with dest_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)


def _prepare_work_image(src_path: Path) -> Path:
    # If it's already a common format, we can pass directly. To keep things robust, convert to PNG.
    work_path = src_path.with_suffix(".png") if src_path.suffix.lower() != ".png" else src_path
    if work_path.exists() and work_path == src_path:
        return work_path
    if Image is None:
        raise HTTPException(status_code=500, detail="Pillow not available to convert image to PNG")
    try:
        with Image.open(src_path) as im:
            im = im.convert("RGB")
            im.save(work_path, format="PNG")
        return work_path
    except Exception as e:
        raise HTTPException(status_code=415, detail=f"Failed to convert image: {e}")


def _serialize_detections(result) -> List[Dict[str, Any]]:
    """Convert ultralytics result.boxes to JSONable list with xyxy, conf, cls name."""
    dets: List[Dict[str, Any]] = []
    try:
        names = getattr(result, "names", {}) or getattr(getattr(result, "model", None), "names", {}) or {}
        boxes = result.boxes  # type: ignore[attr-defined]
        if boxes is None:
            return dets
        for i in range(len(boxes)):
            b = boxes[i]
            # xyxy tensor -> list
            xyxy = b.xyxy[0].tolist() if hasattr(b, "xyxy") else []
            conf = float(b.conf[0]) if hasattr(b, "conf") else None
            cls_id = int(b.cls[0]) if hasattr(b, "cls") else None
            cls_name = names.get(cls_id, str(cls_id)) if cls_id is not None else None
            dets.append({
                "id": f"d{i}",
                "cls": cls_name,
                "cls_id": cls_id,
                "conf": conf,
                "bbox": xyxy,
            })
    except Exception:
        # In case the internal structure changes
        try:
            for i, b in enumerate(getattr(result, "boxes", []) or []):
                dets.append({"id": f"d{i}", "bbox": getattr(b, "xyxy", None)})
        except Exception:
            pass
    return dets


def _build_summary(dets: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    for d in dets:
        name = d.get("cls") or "Unknown"
        counts[name] = counts.get(name, 0) + 1
    total = sum(counts.values())
    if total == 0:
        text = "No objects detected."
    else:
        # Create a short human-readable sentence
        parts = [f"{v} {k}" for k, v in sorted(counts.items(), key=lambda x: -x[1])]
        text = "Detected " + ", ".join(parts) + "."
    return {"counts": counts, "total": total, "summary": text}


def _save_annotated(result, out_path: Path) -> None:
    if cv2 is None:
        raise HTTPException(status_code=500, detail="OpenCV not available to save annotated image")
    plotted = result.plot()  # BGR numpy array
    cv2.imwrite(str(out_path), plotted)


def init_detect(app: FastAPI) -> None:
    """Initialize detection module: ensure dirs, mount static, and lazy-load the model."""
    _ensure_dirs()
    # Mount static serving the public dir if not already mounted
    if not any(getattr(r, "path", None) == "/static" for r in getattr(app, "routes", [])):
        app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")
    # Lazy-load model
    global yolo_model
    if YOLO is None:
        return
    try:
        if os.path.exists(MODEL_PATH):
            yolo_model = YOLO(MODEL_PATH)
        else:
            yolo_model = None
    except Exception:  # pragma: no cover
        yolo_model = None


@router.post("/detect")
async def detect_upload(file: UploadFile = File(...)):
    if not _ext_ok(file.filename):
        raise HTTPException(status_code=415, detail=f"Unsupported file type. Allowed: {sorted(SUPPORTED_EXTS)}")

    if YOLO is None or Image is None:
        raise HTTPException(status_code=500, detail="Detection dependencies not installed (ultralytics/Pillow)")
    if yolo_model is None:
        raise HTTPException(status_code=500, detail=f"Model not loaded. Check DETECT_MODEL_PATH or place model at {MODEL_PATH}")

    # Save upload
    upload_name = _random_name(suffix=Path(file.filename).suffix.lower())
    upload_path = UPLOADS_DIR / upload_name
    try:
        _save_upload(file, upload_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {e}")

    # Normalize to PNG for robust inference
    try:
        work_path = _prepare_work_image(upload_path)
    except HTTPException:
        # Re-raise cleanly
        raise
    except Exception as e:
        raise HTTPException(status_code=415, detail=f"Could not prepare image: {e}")

    # Run detection (sync; ultralytics is blocking)
    try:
        results = yolo_model.predict(source=str(work_path))
        result = results[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {e}")

    # Serialize detections and build summary
    dets = _serialize_detections(result)
    summary = _build_summary(dets)

    # Save annotated image
    annotated_name = _random_name(suffix=".png")
    annotated_path = ANNOTATED_DIR / annotated_name
    try:
        _save_annotated(result, annotated_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save annotated image: {e}")

    annotated_url = f"/static/annotated/{annotated_name}"
    original_url = f"/static/uploads/{upload_name}"
    payload = {
        "imageUrl": annotated_url,
        "originalImageUrl": original_url,
        "summary": summary["summary"],
        "counts": summary["counts"],
        "total": summary["total"],
        "detections": dets,
        "upload": {
            "filename": file.filename,
            "stored": str(upload_path.relative_to(PUBLIC_DIR)) if upload_path.is_relative_to(PUBLIC_DIR) else upload_path.name,
        },
    }
    return JSONResponse(payload)