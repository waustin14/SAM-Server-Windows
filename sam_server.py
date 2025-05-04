from flask import Flask, request, jsonify
import numpy as np, io, base64
from PIL import Image
from segment_anything import sam_model_registry, SamPredictor
import os

# ─── Load model once ───────────────────────────────────────────────────────────
# Define the model path and load the model, based on whether the system is Windows or Mac
if os.name == "nt": # Windows
    app_data_dir = os.path.join(os.environ.get('PROGRAMDATA', ''), 'SegmentAnything')
else: # Mac
    app_data_dir = os.path.join('/Library/Application Support', 'SegmentAnything')
if not os.path.exists(app_data_dir):
    os.makedirs(app_data_dir)
SAM_CHECKPOINT = os.path.join(app_data_dir, 'sam_vit_h_4b8939.pth')

sam = sam_model_registry["vit_h"](checkpoint=SAM_CHECKPOINT)
sam = sam.cuda() if sam.device.type != "cpu" else sam          # CPU fallback
predictor = SamPredictor(sam)

app = Flask(__name__)

# ─── Utility ──────────────────────────────────────────────────────────────────
def b64_to_img(b64):
    return Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")

def img_to_b64(arr):
    return base64.b64encode(arr.tobytes()).decode()

# ─── Endpoint ─────────────────────────────────────────────────────────────────
@app.post("/segment")
def segment():
    body = request.get_json()
    img = np.array(b64_to_img(body["image"]))
    predictor.set_image(img)

    # Optionally parse point prompts in body["point"]  (x, y)
    m, _, _ = predictor.predict(
        point_coords=None,
        point_labels=None,
        multimask_output=False
    )

    return jsonify({
        "width": img.shape[1],
        "height": img.shape[0],
        "alpha": img_to_b64((m[0] * 255).astype("uint8"))
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001)