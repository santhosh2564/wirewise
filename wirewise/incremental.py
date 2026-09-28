"""Event-driven, incremental verification with an energy-saving change gate.

Instead of running the neural detector on every camera frame, WireWise uses a
cheap CPU frame-difference gate: the NPU detector runs only once the board has
CHANGED and then SETTLED (the student's hand has left). Each settled change is
then diffed against the previous built netlist, so feedback points at the part
that was just placed ("the LED you just inserted is backwards").
"""
from dataclasses import dataclass, field
import numpy as np


@dataclass
class ChangeGate:
    diff_threshold: float = 0.02   # fraction of pixels moving = hand/motion in view
    change_threshold: float = 0.003  # fraction changed vs last scan = a part was placed
    settle_frames: int = 8         # frames of stillness before inference
    pixel_delta: int = 25          # per-pixel intensity change counted as "changed"
    _prev: np.ndarray | None = None
    _baseline: np.ndarray | None = None
    _still: int = 0
    _dirty: bool = True
    frames_seen: int = 0
    inferences_run: int = 0

    def update(self, gray: np.ndarray) -> bool:
        """Feed a grayscale frame. Returns True when the detector should run."""
        self.frames_seen += 1
        g = gray.astype(np.int16)
        if self._prev is None:
            self._prev, self._baseline = g, g
            return False
        moving = np.mean(np.abs(g - self._prev) > self.pixel_delta) > self.diff_threshold
        self._prev = g
        if moving:
            self._still, self._dirty = 0, True
            return False
        self._still += 1
        if self._dirty and self._still >= self.settle_frames:
            changed = np.mean(np.abs(g - self._baseline) > self.pixel_delta) > self.change_threshold
            self._dirty = False
            if changed or self.inferences_run == 0:
                self._baseline = g
                self.inferences_run += 1
                return True
        return False

    @property
    def inference_saving(self) -> float:
        return 0.0 if self.frames_seen == 0 else 1 - self.inferences_run / self.frames_seen


def placement_delta(prev_components, new_components):
    """Which parts were added, removed or moved between two settled states."""
    key = lambda c: c.id
    prev = {key(c): c for c in prev_components}
    new = {key(c): c for c in new_components}
    added = [new[k] for k in new.keys() - prev.keys()]
    removed = [prev[k] for k in prev.keys() - new.keys()]
    moved = [new[k] for k in new.keys() & prev.keys() if new[k].pins != prev[k].pins]
    return added, removed, moved


@dataclass
class EcoLedger:
    """Transparent, measured sustainability counters for a lab session."""
    checks: int = 0
    faults_caught_pre_power: int = 0
    parts_protected: dict = field(default_factory=dict)
    cloud_calls: int = 0   # always zero: WireWise is offline by design

    def record(self, safety_findings, built):
        self.checks += 1
        for sev, msg in safety_findings:
            if sev == "error":
                self.faults_caught_pre_power += 1
                for c in built.components:
                    if msg.startswith(c.id + " ") or f" {c.id} " in msg:
                        self.parts_protected[c.type] = self.parts_protected.get(c.type, 0) + 1

    def summary(self, gate: ChangeGate | None = None):
        s = {"checks": self.checks, "faults_caught_before_power_on": self.faults_caught_pre_power,
             "components_protected": dict(self.parts_protected), "cloud_calls": self.cloud_calls}
        if gate:
            s["frames_seen"] = gate.frames_seen
            s["npu_inferences_run"] = gate.inferences_run
            s["inferences_avoided_pct"] = round(100 * gate.inference_saving, 1)
        return s
