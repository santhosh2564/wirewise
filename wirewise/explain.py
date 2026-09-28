"""Turn findings into plain-language guidance with a local LLM on the NPU.

The LLM never decides WHAT is wrong - the deterministic checker does. The LLM
only rephrases verified findings for a student (English or Tamil), so it
cannot invent a fault. If no local model is installed, a template is used.
"""

def _template(findings, lang="en"):
    if not findings:
        return "Wiring matches the schematic and the pre-power check passed. Safe to power on."
    lines = ["Stop - fix these before powering on:"] + [f"{i}. {m}" for i, m in enumerate(findings, 1)]
    return "\n".join(lines)


def explain(findings, lang="en", model_dir=None):
    msgs = [f if isinstance(f, str) else getattr(f, "message", str(f)) for f in findings]
    if model_dir:
        try:
            import onnxruntime_genai as og
            model = og.Model(model_dir)
            tok = og.Tokenizer(model)
            prompt = ("You are a lab assistant. Explain these verified breadboard faults to a first-year "
                      f"student in {'Tamil' if lang == 'ta' else 'English'}, one short fix per fault. "
                      "Do not add faults.\n" + "\n".join(msgs))
            params = og.GeneratorParams(model)
            params.set_search_options(max_length=400)
            gen = og.Generator(model, params)
            gen.append_tokens(tok.encode(prompt))
            while not gen.is_done():
                gen.generate_next_token()
            return tok.decode(gen.get_sequence(0))
        except Exception:
            pass
    return _template(msgs, lang)
