"""On-device perception: breadboard localisation, part detection, leg-to-hole mapping.

Models run through ONNX Runtime with the Qualcomm QNN execution provider so
inference lands on the Snapdragon Hexagon NPU; CPU is the automatic fallback.
Detector: YOLOv8-Det from Qualcomm AI Hub, fine-tuned on breadboard parts.
Resistor colour bands: a small classifier on each detected resistor crop.
"""
import numpy as np
from .breadboard import all_holes, BreadboardSpec


def make_session(model_path: str, prefer_npu: bool = True):
    import onnxruntime as ort
    providers = []
    if prefer_npu and "QNNExecutionProvider" in ort.get_available_providers():
        providers.append(("QNNExecutionProvider", {"backend_path": "QnnHtp.dll",
                                                   "htp_performance_mode": "burst"}))
    providers.append("CPUExecutionProvider")
    return ort.InferenceSession(model_path, providers=providers)


def homography(src_pts, dst_pts):
    """Direct linear transform from 4+ image points to board-grid points."""
    rows = []
    for (x, y), (u, v) in zip(src_pts, dst_pts):
        rows.append([-x, -y, -1, 0, 0, 0, u * x, u * y, u])
        rows.append([0, 0, 0, -x, -y, -1, v * x, v * y, v])
    _, _, vt = np.linalg.svd(np.asarray(rows, float))
    H = vt[-1].reshape(3, 3)
    return H / H[2, 2]


def to_grid(H, pt):
    p = H @ np.array([pt[0], pt[1], 1.0])
    return p[:2] / p[2]


def nearest_hole(grid_xy, spec: BreadboardSpec = BreadboardSpec(), max_dist=0.5):
    """Snap a leg endpoint (in grid units) to the closest hole, or None if too far."""
    best, best_d = None, 1e9
    for name, (cx, cy) in all_holes(spec):
        d = np.hypot(grid_xy[0] - cx, grid_xy[1] - cy)
        if d < best_d:
            best, best_d = name, d
    return best if best_d <= max_dist else None


def letterbox(img, size=640):
    h, w = img.shape[:2]
    s = size / max(h, w)
    nh, nw = int(round(h * s)), int(round(w * s))
    import cv2
    resized = cv2.resize(img, (nw, nh))
    canvas = np.full((size, size, 3), 114, np.uint8)
    canvas[:nh, :nw] = resized
    x = canvas[:, :, ::-1].transpose(2, 0, 1)[None].astype(np.float32) / 255.0
    return x, s


def detect_parts(session, img, conf=0.4, class_names=("R", "LED", "W", "C", "D", "IC")):
    """Run the YOLO detector; returns list of (class, score, box_xyxy in image px)."""
    x, s = letterbox(img)
    out = session.run(None, {session.get_inputs()[0].name: x})
    boxes, scores, classes = out[0][0], out[1][0], out[2][0]   # AI Hub YOLOv8 export layout
    dets = []
    for bx, sc, cl in zip(boxes, scores, classes):
        if sc >= conf:
            dets.append((class_names[int(cl)], float(sc), (np.asarray(bx) / s).tolist()))
    return dets
