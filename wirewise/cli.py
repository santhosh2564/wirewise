"""wirewise check --ref examples/led_reference.json --built examples/led_built_reversed.json"""
import argparse
from .netlist import load_components, build_from_breadboard, build_reference
from .compare import compare
from .precheck import analyse
from .explain import explain
from .incremental import EcoLedger


def run(ref_path, built_path, lang="en", llm_dir=None):
    ref = build_reference(load_components(ref_path))
    built = build_from_breadboard(load_components(built_path))
    topo = compare(ref, built)
    safety, report = analyse(built)
    msgs = [f.message for f in topo] + [m for _, m in safety]
    ledger = EcoLedger(); ledger.record(safety, built)
    run.last_ledger = ledger.summary()
    return topo, safety, report, explain(msgs, lang, llm_dir)


def main():
    ap = argparse.ArgumentParser(prog="wirewise")
    ap.add_argument("command", choices=["check"])
    ap.add_argument("--ref", required=True)
    ap.add_argument("--built", required=True)
    ap.add_argument("--lang", default="en", choices=["en", "ta"])
    ap.add_argument("--llm", default=None, help="path to onnxruntime-genai model folder")
    a = ap.parse_args()
    topo, safety, report, text = run(a.ref, a.built, a.lang, a.llm)
    print("== Topology vs schematic ==")
    for f in topo or ["OK - matches schematic"]:
        print(" ", f if isinstance(f, str) else f"[{f.severity}] {f.message}")
    print("== Pre-power prediction ==")
    for cid, r in report.items():
        print(f"  {cid}: " + ", ".join(f"{k}={v:.1f}" if isinstance(v, float) else f"{k}={v}" for k, v in r.items()))
    for sev, m in safety:
        print(f"  [{sev}] {m}")
    print("== Guidance ==")
    print(text)
    print("== Eco ledger ==")
    for k, v in run.last_ledger.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
