# Sustainability: low cost, low water, low e-waste

## Why it matters
- **E-waste:** the UN Global E-waste Monitor 2024 reports a record 62 million tonnes of e-waste generated in 2022, with only 22.3% documented as properly collected and recycled.
- **Water used by cloud AI:** Li, Yang, Islam & Ren (*Making AI Less "Thirsty"*, UC Riverside) estimate GPT-3 consumes roughly a 500 ml bottle of water for about 10–50 medium-length responses, and project global AI water withdrawal of 4.2–6.6 billion m³ in 2027.

## How WireWise responds
| Principle | Mechanism | Measured by |
|---|---|---|
| Prevent e-waste | Pre-power prediction stops LEDs/resistors burning out | `faults_caught_before_power_on`, `components_protected` |
| No data-centre water or cloud energy | All inference on the laptop's NPU; no API calls | `cloud_calls` (always 0) |
| Compute only when needed | Change gate skips the detector when nothing on the board has changed | `inferences_avoided_pct` |
| No new hardware | Uses the lab's existing laptop and built-in/USB webcam; standard breadboards | — |
| Small models | INT8/INT4 quantised models from Qualcomm AI Hub | Model size in README |
| Zero running cost | Free models, free AI Hub profiling, free Colab/Kaggle training | ₹0 per check |

The ledger prints at the end of every session so the environmental claim is evidence, not a slogan.
