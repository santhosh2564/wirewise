"""Live lab mode: webcam -> change gate -> NPU detector -> netlist -> check -> overlay.

python -m wirewise.live --ref examples/led_reference.json --detector models/breadboard_yolov8.onnx
Corner calibration: click the 4 corners of the breadboard terminal area once.
"""
import argparse
import numpy as np
from .incremental import ChangeGate, EcoLedger, placement_delta
from .vision import make_session, detect_parts, homography, to_grid, nearest_hole
from .netlist import Component, build_from_breadboard, build_reference, load_components
from .compare import compare
from .precheck import analyse
from .explain import explain


def dets_to_components(dets, H, legs_fn):
    """Convert detections to Components by snapping each detected leg endpoint to a hole."""
    comps, counts = [], {}
    for cls, score, box in dets:
        legs = legs_fn(cls, box)                        # leg endpoints in image px
        holes = [nearest_hole(to_grid(H, p)) for p in legs]
        if None in holes:
            continue
        counts[cls] = counts.get(cls, 0) + 1
        pins = {"R": ("1", "2"), "W": ("1", "2"), "LED": ("A", "K"), "D": ("A", "K")}.get(cls, ("1", "2"))
        comps.append(Component(f"{cls}{counts[cls]}", cls, None, dict(zip(pins, holes))))
    return comps


def main():
    import cv2
    ap = argparse.ArgumentParser()
    ap.add_argument("--ref", required=True); ap.add_argument("--detector", required=True)
    ap.add_argument("--camera", type=int, default=0); ap.add_argument("--columns", type=int, default=30)
    a = ap.parse_args()
    ref = build_reference(load_components(a.ref))
    sess = make_session(a.detector)
    cap = cv2.VideoCapture(a.camera)
    corners = []
    cv2.namedWindow("WireWise")
    cv2.setMouseCallback("WireWise", lambda e, x, y, *_: corners.append((x, y)) if e == cv2.EVENT_LBUTTONDOWN and len(corners) < 4 else None)
    gate, ledger, prev = ChangeGate(), EcoLedger(), []
    grid = [(0, 0), (a.columns - 1, 0), (a.columns - 1, 10), (0, 10)]
    message = "Click the 4 board corners (TL, TR, BR, BL)"
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if len(corners) == 4 and gate.update(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)):
            H = homography(corners, grid)
            dets = detect_parts(sess, frame)
            # Leg endpoints: ends of the box's long axis (replace with keypoint head when trained).
            legs_fn = lambda cls, b: [(b[0], (b[1] + b[3]) / 2), (b[2], (b[1] + b[3]) / 2)] if (b[2] - b[0]) > (b[3] - b[1]) else [((b[0] + b[2]) / 2, b[1]), ((b[0] + b[2]) / 2, b[3])]
            comps = dets_to_components(dets, H, legs_fn)
            added, removed, moved = placement_delta(prev, comps); prev = comps
            built = build_from_breadboard(comps)
            safety, _ = analyse(built); ledger.record(safety, built)
            message = explain([f.message for f in compare(ref, built)] + [m for _, m in safety])
        for p in corners:
            cv2.circle(frame, p, 5, (0, 200, 255), -1)
        for i, line in enumerate(message.splitlines()[:6]):
            cv2.putText(frame, line[:90], (10, 25 + 22 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255) if "Stop" in message else (0, 160, 0), 2)
        cv2.imshow("WireWise", frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break
    print(ledger.summary(gate))


if __name__ == "__main__":
    main()
