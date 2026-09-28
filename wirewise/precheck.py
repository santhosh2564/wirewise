"""Pre-power safety check: DC operating point of the circuit AS BUILT.

A small modified-nodal-analysis solver (no SPICE install needed) predicts
what will happen the moment power is applied, so damage is caught before it
happens rather than debugged afterwards.
Supported parts: V (ideal source), R, LED/D (piecewise-linear), W handled upstream.
"""
import numpy as np
from .netlist import Netlist

LED_VF = 2.0        # V, typical red LED
LED_RS = 15.0       # ohm, dynamic resistance
LED_IMAX = 0.020    # A, continuous rating
LED_IABS = 0.030    # A, likely damage
R_PMAX = 0.25       # W, standard 1/4 W resistor


def analyse(nl: Netlist):
    findings = []
    srcs = [c for c in nl.components if c.type == "V"]
    if not srcs:
        return findings, {}
    for s in srcs:
        if nl.pin_net[(s.id, "+")] == nl.pin_net[(s.id, "-")]:
            findings.append(("error", f"DIRECT SHORT across supply {s.id}: + and - are on the same net. Do not power on."))
            return findings, {}

    gnd = nl.pin_net[(srcs[0].id, "-")]
    nets = sorted({n for n in nl.pin_net.values() if n != gnd})
    idx = {n: i for i, n in enumerate(nets)}
    diodes = [c for c in nl.components if c.type in ("LED", "D")]
    state = {d.id: True for d in diodes}

    for _ in range(20):
        n, m = len(nets), len(srcs)
        A = np.zeros((n + m, n + m))
        b = np.zeros(n + m)
        A[:n, :n] += np.eye(n) * 1e-9   # gmin keeps floating nets solvable

        def stamp_g(a, c, g):
            ia, ic = idx.get(a), idx.get(c)
            if ia is not None: A[ia, ia] += g
            if ic is not None: A[ic, ic] += g
            if ia is not None and ic is not None:
                A[ia, ic] -= g; A[ic, ia] -= g

        for c in nl.components:
            if c.type == "R":
                stamp_g(nl.pin_net[(c.id, "1")], nl.pin_net[(c.id, "2")], 1.0 / c.value)
            elif c.type in ("LED", "D") and state[c.id]:
                a, k = nl.pin_net[(c.id, "A")], nl.pin_net[(c.id, "K")]
                g = 1.0 / LED_RS
                stamp_g(a, k, g)
                if a in idx: b[idx[a]] += g * LED_VF
                if k in idx: b[idx[k]] -= g * LED_VF
        for j, s in enumerate(srcs):
            p, q = nl.pin_net[(s.id, "+")], nl.pin_net[(s.id, "-")]
            if p in idx: A[idx[p], n + j] += 1; A[n + j, idx[p]] += 1
            if q in idx: A[idx[q], n + j] -= 1; A[n + j, idx[q]] -= 1
            b[n + j] = s.value
        x = np.linalg.solve(A, b)
        v = lambda net: 0.0 if net == gnd else x[idx[net]]

        changed = False
        for d in diodes:
            vd = v(nl.pin_net[(d.id, "A")]) - v(nl.pin_net[(d.id, "K")])
            on = vd > LED_VF
            if on != state[d.id]:
                state[d.id], changed = on, True
        if not changed:
            break

    report = {}
    for c in nl.components:
        if c.type == "R":
            i = (v(nl.pin_net[(c.id, "1")]) - v(nl.pin_net[(c.id, "2")])) / c.value
            p = i * i * c.value
            report[c.id] = {"current_mA": abs(i) * 1e3, "power_mW": p * 1e3}
            if p > R_PMAX:
                findings.append(("error", f"{c.id} would dissipate {p:.2f} W (rating {R_PMAX} W) - it will overheat."))
        elif c.type in ("LED", "D"):
            vd = v(nl.pin_net[(c.id, "A")]) - v(nl.pin_net[(c.id, "K")])
            i = max(0.0, (vd - LED_VF) / LED_RS) if state[c.id] else 0.0
            report[c.id] = {"current_mA": i * 1e3, "on": state[c.id]}
            if i > LED_IABS:
                findings.append(("error", f"{c.id} would draw {i*1e3:.0f} mA (max ~{LED_IABS*1e3:.0f} mA) - it will likely burn out. Add or increase a series resistor."))
            elif i > LED_IMAX:
                findings.append(("warning", f"{c.id} would draw {i*1e3:.0f} mA - above the {LED_IMAX*1e3:.0f} mA rating."))
            elif not state[c.id]:
                findings.append(("warning", f"{c.id} will stay OFF with this wiring."))
    return findings, report
