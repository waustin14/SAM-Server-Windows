from flask import Flask, request, jsonify
import numpy as np, io, base64
from PIL import Image
from segment_anything import sam_model_registry, SamPredictor
import os, time, threading, torch


# Define the model path and load the model, based on whether the system is Windows or Mac
if os.name == "nt": # Windows
    app_data_dir = os.path.join('C:\\ProgramData', 'SAMService')
else: # Mac
    app_data_dir = os.path.join('/Library/Application Support', 'SAMService')
if not os.path.exists(app_data_dir):
    os.makedirs(app_data_dir)
SAM_CHECKPOINT = os.path.join(app_data_dir, 'sam_vit_h.pth')

IDLE_TIMEOUT = 15 * 60          # seconds   ← set to 0 to keep resident always

app = Flask(__name__)
_lock = threading.Lock()
_predictor = None               # instantiated lazily
_last_used = 0.0

def _get_predictor():
    global _predictor, _last_used
    with _lock:
        if _predictor is None:
            print("[SAM] Loading model …")
            sam = sam_model_registry["vit_h"](checkpoint=SAM_CHECKPOINT).to("cuda" if torch.cuda.is_available() else "cpu")
            _predictor = SamPredictor(sam)
        _last_used = time.time()
        return _predictor

def _maybe_unload():
    global _predictor
    if _predictor and time.time() - _last_used > IDLE_TIMEOUT:
        print("[SAM] Idle timeout reached; unloading model.")
        del _predictor
        _predictor = None
        torch.cuda.empty_cache()

def _idle_watchdog():
    while True:
        time.sleep(IDLE_TIMEOUT // 3)
        _maybe_unload()

if IDLE_TIMEOUT:
    threading.Thread(target=_idle_watchdog, daemon=True).start()

def b64_to_img(b64):
    return Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")

@app.post("/segment")
def segment():
    body = request.get_json()
    img = np.array(b64_to_img(body["image"]))

    predictor = _get_predictor()
    predictor.set_image(img)
    mask, _, _ = predictor.predict(
        point_coords=np.array(body.get("point_coords")),
        point_labels=np.array(body.get("point_labels")),
        multimask_output=False,
    )

    return jsonify(
        width=img.shape[1],
        height=img.shape[0],
        alpha=base64.b64encode((mask[0] * 255).astype("uint8")).decode()
    )