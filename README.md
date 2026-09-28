# WireWise — offline AI lab partner that catches breadboard faults *before* power-on

WireWise looks at a student's physical breadboard through the laptop webcam, reconstructs the circuit that was **actually built**, compares it against the **intended schematic**, and predicts what will happen when power is applied — a burnt LED, an overheating resistor, a shorted supply — **before** it happens. Everything runs on-device on the Snapdragon® X NPU. No internet, no cloud fees, no student data leaving the lab.

> Built for the Snapdragon® AI Lab Build & Present Challenge (Snapdragon-powered HP AI PCs).

## Why

In first-year electronics labs a large share of "my circuit doesn't work" moments are wiring slips: a reversed LED, a resistor bypassed by a stray jumper, a leg one row off. Teaching assistants can't reach every bench, components burn, and lab time is lost. Existing aids either need special hardware (instrumented breadboards) or send photos to a cloud vision-LLM that *guesses* the fault.

## What is new (see [docs/PRIOR_ART.md](docs/PRIOR_ART.md))

1. **As-built pre-power damage prediction.** The circuit reconstructed from the camera — mistakes included — is solved electrically before power-on, predicting burnt LEDs, overheated resistors and supply shorts. No patent or paper found doing this.
2. **Event-driven incremental verification.** A change gate wakes the NPU detector only when a placement has settled, and feedback names the part just inserted.
3. **Deterministic, explainable fault taxonomy.** Open, short, bypass, reversed polarity, wrong value, missing/extra. AI does perception and wording only; it cannot invent a fault.
4. **Offline on the Snapdragon NPU with a measured eco-ledger** (faults caught before power-on, inferences avoided, zero cloud calls). See [docs/SUSTAINABILITY.md](docs/SUSTAINABILITY.md).

## Pipeline

```
webcam frame ─► board localisation + homography ─► YOLOv8 part detector (NPU)
            ─► leg endpoints snapped to holes ─► resistor colour-band classifier (NPU)
            ─► breadboard connectivity model ─► BUILT netlist
reference schematic (lab sheet) ─► REFERENCE netlist
BUILT vs REFERENCE ─► topology diff (open / short / reversed / wrong value / missing)
BUILT ─► DC operating-point solver ─► pre-power safety verdict
findings ─► local LLM (NPU) ─► student guidance + on-screen overlay of the exact hole
```

## Models (Qualcomm AI Hub / open source)

| Stage | Model | Runtime |
|---|---|---|
| Part detection | YOLOv8-Det (AI Hub), fine-tuned on breadboard parts | ONNX Runtime + QNN EP (NPU) |
| Value text on caps/ICs | EasyOCR (AI Hub) | QNN EP (NPU) |
| Guidance | Llama 3.2 3B / Phi-3.5-mini (quantized) | onnxruntime-genai |
| Voice questions (optional) | Whisper-Base (AI Hub) | QNN EP (NPU) |

## Repository status

| Module | Status |
|---|---|
| `breadboard.py` connectivity model | ✅ working |
| `netlist.py` built/reference netlists | ✅ working |
| `compare.py` topology diff (open, short, bypass, reversed, value, missing) | ✅ working + tests |
| `precheck.py` DC solver, LED/resistor safety | ✅ working + tests |
| `vision.py` homography + hole snapping | ✅ working + tests |
| `vision.py` detector on QNN EP | 🔧 integration in progress (model training) |
| `explain.py` local LLM guidance | 🔧 template fallback working; LLM wiring in progress |
| `incremental.py` change gate, placement delta, eco-ledger | ✅ working + tests |
| `live.py` webcam lab mode | 🔧 runs with a detector model; model training in progress |
| `benchmark.py` CPU vs NPU latency | ✅ ready to run on device |

## Quick start

```bash
pip install -r requirements.txt
python -m pytest -q tests
python -m wirewise.cli check --ref examples/led_reference.json --built examples/led_built_bypassed.json
```

7 tests pass. Example output:

```
== Topology vs schematic ==
  [error] R1 is bypassed: both of its legs are on the same connection ...
== Pre-power prediction ==
  LED1: current_mA=200.0, on=True
  [error] LED1 would draw 200 mA (max ~30 mA) - it will likely burn out.
== Eco ledger ==
  faults_caught_before_power_on: 1
  components_protected: {'LED': 1}
  cloud_calls: 0
```

## Roadmap

1. Collect & label ~500 breadboard photos (Roboflow free tier), fine-tune YOLOv8 on Colab/Kaggle, compile with Qualcomm AI Hub.
2. Live overlay UI highlighting the faulty hole on the camera feed.
3. Lab-sheet library: instructors publish reference circuits as JSON.
4. Extend solver to transistors, op-amps and ICs.

## Cost

Models, AI Hub compilation/profiling, datasets tooling and training (Colab/Kaggle) are free. Runtime cost per check: **₹0**.

## License

MIT
