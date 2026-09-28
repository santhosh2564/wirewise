# Prior-art and novelty search record

Searched September 2026 across Google Patents, USPTO full text, arXiv, PubMed Central, Semantic Scholar/ResearchGate, GitHub and hackathon listings. This is a good-faith novelty review for a student challenge, **not** a formal freedom-to-operate opinion.

## Closest prior art found

| # | Reference | What it does | What it does NOT do (gap WireWise fills) |
|---|---|---|---|
| P1 | US 10,528,694 B2 and US 10,915,687 — *Breadboard and electronics experimentation system* | Translucent breadboard laid on a display; screen lights up where parts should go | Needs special hardware; guides placement but does not inspect the as-built board with a camera; no damage prediction |
| P2 | US 2024/0233407 A1 — *PCB netlist extraction from multimodal imagery* | CNNs + OCR extract components and netlist from a printed circuit board | PCB reverse-engineering, not solderless breadboards; no reference-vs-built teaching diff; no pre-power simulation |
| P3 | US 10,592,631 — *Netlist comparison based on pin connection relationship* | Compares two EDA netlists pin by pin | Both netlists are design files; no physical board or camera |
| L1 | SchemaBoard (Kim et al., ACM UIST 2020) | LED matrix under the breadboard highlights rows and nets | Custom hardware; no camera; no damage prediction |
| L2 | Breadboard-Classifier (Sonoma State STEM project, GitHub, MIT) | Rectifies a breadboard photo; deterministic checker against a lab netlist | Photo-to-netlist step not joined (per its README); single photo; no as-built simulation; not NPU/offline-optimised |
| L3 | CIRIS (lablab.ai hackathon, Aug 2026) | Uploads breadboard photos to GPT-4o in the cloud for feedback | Cloud, non-deterministic, no simulation |
| L4 | Sketch2Sim; YOLOv8 hand-drawn power-converter framework; SPICE netlist from image (IEEE, 2026) | Hand-drawn/printed **schematic** image → SPICE netlist → simulation | Works on drawings, not physical breadboards; simulates the intended design, not the mistake the student actually built |
| L5 | AR breadboard building-guide apps (ResearchGate) | AR overlay showing where to place parts; resistor colour reading | Guidance only; no as-built verification or simulation |

## WireWise novelty claims (after this search)

1. **As-built pre-power damage prediction** — the circuit reconstructed from the camera (including the student's mistakes) is solved electrically *before power is applied*, predicting burnt LEDs, overheated resistors and supply shorts. No patent or paper found doing this.
2. **Event-driven incremental verification** — a change gate runs the NPU detector only when a placement has settled, and diffs consecutive states so feedback names the part just inserted. Prior checkers work on a single photo.
3. **Deterministic, explainable fault taxonomy** (open, short, bypass, reversed polarity, wrong value, missing/extra) where AI is limited to perception and wording; the language model cannot add faults.
4. **Fully on-device on a Snapdragon NPU** with a measured eco-ledger (inferences avoided, faults caught before power-on, zero cloud calls).

Claim 3 alone overlaps L2; the novelty is the combination with claims 1, 2 and 4.

## Reproduce the search

Google Patents (patents.google.com):
- `(breadboard) (camera OR image) (netlist OR schematic) (verify OR compare)`
- `(breadboard) (image) (simulat*) (overcurrent OR damage OR "burn")`
- `(breadboard) (augmented reality OR overlay) (component placement)`

Google Scholar (scholar.google.com):
- `"breadboard" netlist image recognition`
- `"breadboard" camera wiring error detection schematic`
- `hand-drawn circuit netlist SPICE YOLO`
- `"breadboard" "before power" simulation`
