import numpy as np
from wirewise.incremental import ChangeGate, placement_delta, EcoLedger
from wirewise.netlist import load_components, build_from_breadboard
from wirewise.precheck import analyse


def _frames():
    rng = np.random.default_rng(0)
    board = rng.integers(0, 255, (120, 160)).astype(np.uint8)
    frames = [board.copy() for _ in range(30)]            # idle board
    hand = board.copy(); hand[20:100, 40:120] = 0
    frames += [hand.copy() for _ in range(5)]              # hand moving in
    placed = board.copy(); placed[50:60, 70:90] = 255      # a part now sits there
    frames += [placed.copy() for _ in range(30)]           # hand gone, settled
    return frames


def test_gate_runs_detector_only_on_settled_changes():
    g = ChangeGate()
    runs = [g.update(f) for f in _frames()]
    assert sum(runs) == 2               # initial scan + one settled placement
    assert g.inference_saving > 0.9     # >90% of frames never reach the NPU


def test_placement_delta_reports_just_moved_part():
    ok = load_components("examples/led_built_ok.json")
    rev = load_components("examples/led_built_reversed.json")
    added, removed, moved = placement_delta(ok, rev)
    assert [c.id for c in moved] == ["LED1"] and not added and not removed


def test_eco_ledger_counts_protected_parts():
    built = build_from_breadboard(load_components("examples/led_built_bypassed.json"))
    safety, _ = analyse(built)
    led = EcoLedger(); led.record(safety, built)
    s = led.summary()
    assert s["faults_caught_before_power_on"] == 1 and s["components_protected"] == {"LED": 1}
    assert s["cloud_calls"] == 0
