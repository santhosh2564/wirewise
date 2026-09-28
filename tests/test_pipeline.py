from wirewise.cli import run
from wirewise.vision import homography, to_grid, nearest_hole

REF = "examples/led_reference.json"


def test_correct_build_passes():
    topo, safety, report, _ = run(REF, "examples/led_built_ok.json")
    assert topo == []
    assert not [s for s in safety if s[0] == "error"]
    assert 5 < report["LED1"]["current_mA"] < 15


def test_reversed_led_detected():
    topo, safety, _, _ = run(REF, "examples/led_built_reversed.json")
    assert any(f.kind == "reversed" and "LED1" in f.components for f in topo)
    assert any("OFF" in m for _, m in safety)


def test_bypassed_resistor_predicts_burnout():
    topo, safety, report, _ = run(REF, "examples/led_built_bypassed.json")
    assert any(f.kind == "short" for f in topo)
    assert report["LED1"]["current_mA"] > 30
    assert any(sev == "error" and "burn" in m for sev, m in safety)


def test_leg_snaps_to_hole():
    img = [(100, 100), (1000, 100), (1000, 400), (100, 400)]
    grid = [(0, 0), (29, 0), (29, 10), (0, 10)]
    H = homography(img, grid)
    g = to_grid(H, (100 + 9 * 900 / 29, 100 + 2 * 300 / 10))
    assert nearest_hole(g) == "c10"
