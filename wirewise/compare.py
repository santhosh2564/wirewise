"""Deterministic comparison of the built circuit against the reference.

The comparison is on pin-connectivity partitions, so it does not depend on
where on the breadboard the student placed parts - only on what is
electrically connected to what.
"""
from dataclasses import dataclass
from .netlist import POLARIZED


@dataclass
class Finding:
    severity: str   # "error" | "warning"
    kind: str       # open, short, reversed, value, missing, extra
    message: str
    components: tuple


def _match_components(ref, built):
    """Match by id first, then by (type, value)."""
    mapping, used = {}, set()
    for rc in ref.components:
        for bc in built.components:
            if bc.id == rc.id and bc.type == rc.type and bc.id not in used:
                mapping[rc.id] = bc.id
                used.add(bc.id)
                break
    for rc in ref.components:
        if rc.id in mapping:
            continue
        for bc in built.components:
            if bc.id not in used and bc.type == rc.type and bc.value == rc.value:
                mapping[rc.id] = bc.id
                used.add(bc.id)
                break
    return mapping, used


def _pin_partition(nl, pin_filter):
    groups = {}
    for key, net in nl.pin_net.items():
        if key in pin_filter:
            groups.setdefault(net, set()).add(key)
    return [frozenset(g) for g in groups.values()]


def compare(ref, built):
    findings = []
    mapping, used = _match_components(ref, built)

    for rc in ref.components:
        if rc.id not in mapping:
            findings.append(Finding("error", "missing", f"{rc.type} {rc.id} is not on the board.", (rc.id,)))
    for bc in built.components:
        if bc.id not in used:
            findings.append(Finding("warning", "extra", f"{bc.type} {bc.id} is not in the schematic.", (bc.id,)))

    for rid, bid in mapping.items():
        rv, bv = ref.component(rid).value, built.component(bid).value
        if rv is not None and bv is not None and abs(rv - bv) > 1e-9 * max(1, abs(rv)):
            findings.append(Finding("error", "value", f"{rid}: expected {rv:g}, found {bv:g}.", (rid,)))

    # Translate built pins into reference ids.
    inv = {b: r for r, b in mapping.items()}
    built_pins = {}
    for (cid, pin), net in built.pin_net.items():
        if cid in inv:
            built_pins[(inv[cid], pin)] = net

    # Detect reversed polarized parts and normalise them before topology check.
    for rid in mapping:
        c = ref.component(rid)
        if c.type not in POLARIZED:
            continue
        p1, p2 = POLARIZED[c.type]
        if (rid, p1) not in built_pins or (rid, p2) not in built_pins:
            continue
        if _fits(ref, built_pins, rid, swap=True) and not _fits(ref, built_pins, rid, swap=False):
            findings.append(Finding("error", "reversed", f"{rid} is inserted backwards ({p1}/{p2} swapped).", (rid,)))
            built_pins[(rid, p1)], built_pins[(rid, p2)] = built_pins[(rid, p2)], built_pins[(rid, p1)]

    keys = set(ref.pin_net) & set(built_pins)
    ref_groups = {}
    for k in keys:
        ref_groups.setdefault(ref.pin_net[k], set()).add(k)
    built_groups = {}
    for k in keys:
        built_groups.setdefault(built_pins[k], set()).add(k)

    for net, pins in ref_groups.items():
        split = {}
        for k in pins:
            split.setdefault(built_pins[k], set()).add(k)
        if len(split) > 1:
            parts = [" + ".join(sorted(f"{c}.{p}" for c, p in s)) for s in split.values()]
            findings.append(Finding("error", "open", f"Net '{net}' is broken: [{'] | ['.join(parts)}] should be connected.",
                                    tuple(sorted({c for c, _ in pins}))))
    for rid in mapping:
        pins = [k for k in keys if k[0] == rid]
        if len(pins) == 2 and built_pins[pins[0]] == built_pins[pins[1]] and ref.pin_net[pins[0]] != ref.pin_net[pins[1]]:
            findings.append(Finding("error", "short", f"{rid} is bypassed: both of its legs are on the same connection, "
                                    "so current skips it (check for a stray jumper or both legs in one column).", (rid,)))
    for bnet, pins in built_groups.items():
        rnets = {ref.pin_net[k] for k in pins}
        if len(rnets) > 1:
            findings.append(Finding("error", "short", f"Unintended connection between nets {sorted(rnets)}.",
                                    tuple(sorted({c for c, _ in pins}))))
    return findings


def _fits(ref, built_pins, rid, swap):
    """Does this part's pin pair agree with the reference topology (optionally swapped)?"""
    c = ref.component(rid)
    p1, p2 = POLARIZED[c.type]
    b1, b2 = built_pins[(rid, p1)], built_pins[(rid, p2)]
    if swap:
        b1, b2 = b2, b1
    ok = 0
    for pin, bnet in ((p1, b1), (p2, b2)):
        rnet = ref.pin_net[(rid, pin)]
        peers = [k for k, n in ref.pin_net.items() if n == rnet and k[0] != rid and k in built_pins]
        if not peers or all(built_pins[k] == bnet for k in peers):
            ok += 1
    return ok == 2
