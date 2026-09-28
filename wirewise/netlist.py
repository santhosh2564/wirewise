"""Build an electrical netlist from components placed on a breadboard."""
import json
from dataclasses import dataclass, field
from .breadboard import hole_to_net

POLARIZED = {"LED": ("A", "K"), "D": ("A", "K"), "CE": ("+", "-"), "V": ("+", "-")}


@dataclass
class Component:
    id: str
    type: str          # R, LED, D, C, CE, V, W (wire)
    value: float | None
    pins: dict         # pin name -> hole (built) or net name (reference)


@dataclass
class Netlist:
    components: list = field(default_factory=list)
    pin_net: dict = field(default_factory=dict)   # (comp_id, pin) -> net id

    def nets(self):
        out = {}
        for key, net in self.pin_net.items():
            out.setdefault(net, set()).add(key)
        return out

    def component(self, cid):
        return next(c for c in self.components if c.id == cid)


class _UnionFind:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


def load_components(path):
    with open(path) as f:
        data = json.load(f)
    return [Component(**c) for c in data["components"]]


def build_from_breadboard(components):
    """Holes -> internal nets, jumper wires merge nets, return a Netlist."""
    uf = _UnionFind()
    parts = []
    for c in components:
        nets = {pin: hole_to_net(h) for pin, h in c.pins.items()}
        if c.type == "W":
            a, b = list(nets.values())
            uf.union(a, b)
        else:
            parts.append((c, nets))
    nl = Netlist()
    for c, nets in parts:
        nl.components.append(c)
        for pin, net in nets.items():
            nl.pin_net[(c.id, pin)] = uf.find(net)
    return nl


def build_reference(components):
    """Reference schematic: pins already carry logical net names."""
    nl = Netlist()
    for c in components:
        if c.type == "W":
            continue
        nl.components.append(c)
        for pin, net in c.pins.items():
            nl.pin_net[(c.id, pin)] = net
    return nl
