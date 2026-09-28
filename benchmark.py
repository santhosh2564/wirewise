"""CPU vs NPU latency for any ONNX model (e.g. the AI Hub YOLOv8 detector).

python benchmark.py models/breadboard_yolov8.onnx --runs 50
"""
import sys, time, argparse
import numpy as np
import onnxruntime as ort


def bench(path, providers, runs):
    s = ort.InferenceSession(path, providers=providers)
    inp = s.get_inputs()[0]
    shape = [d if isinstance(d, int) else 1 for d in inp.shape]
    x = np.random.rand(*shape).astype(np.float32)
    for _ in range(5):
        s.run(None, {inp.name: x})
    t = []
    for _ in range(runs):
        t0 = time.perf_counter(); s.run(None, {inp.name: x}); t.append((time.perf_counter() - t0) * 1e3)
    return np.median(t), np.percentile(t, 95)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("model"); ap.add_argument("--runs", type=int, default=50)
    a = ap.parse_args()
    print(f"CPU  median/p95 ms: %.1f / %.1f" % bench(a.model, ["CPUExecutionProvider"], a.runs))
    if "QNNExecutionProvider" in ort.get_available_providers():
        npu = [("QNNExecutionProvider", {"backend_path": "QnnHtp.dll"}), "CPUExecutionProvider"]
        print(f"NPU  median/p95 ms: %.1f / %.1f" % bench(a.model, npu, a.runs))
    else:
        print("QNN execution provider not available - run on a Snapdragon X PC with onnxruntime-qnn.")
