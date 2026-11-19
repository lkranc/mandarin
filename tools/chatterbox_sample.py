#!/usr/bin/env python3
"""
Preview one dialogue with Chatterbox Multilingual (local, free) — to hear how it sounds.

    python3 tools/chatterbox_sample.py                       # fruit stall, version 1, built-in voice
    python3 tools/chatterbox_sample.py --ref-a seller.wav --ref-b me.wav
    python3 tools/chatterbox_sample.py --dialogue order --version 2

--ref-a / --ref-b: ~10 s WAV of a native Mandarin speaker to clone (one per role).
Without them both roles use Chatterbox's single built-in voice (it has no voice library).
Writes chatterbox_preview/<dialogue>_v<N>.wav (whole dialogue) + one WAV per line.
Errors are printed and exit with code 1 — nothing fails silently.
"""
import argparse, os, sys, json, re

def die(msg):
    print(f"\033[31mERROR: {msg}\033[0m"); sys.exit(1)

ap = argparse.ArgumentParser()
ap.add_argument("--dialogue", default="fruit")
ap.add_argument("--version", type=int, default=1)
ap.add_argument("--ref-a"); ap.add_argument("--ref-b")
ap.add_argument("--cfg", type=float, default=0.5, help="lower (0–0.3) if the reference voice isn't Mandarin, to reduce accent")
a = ap.parse_args()

try:
    import torch, torchaudio
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
except ImportError as e:
    die(f"{e} — install with: pip install chatterbox-tts")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
m = re.search(r"const DATA = (\{.*?\});\n", html, re.S) or die("could not read dialogue data from index.html")
data = json.loads(m.group(1))
dlg = next((d for c in data["categories"] for d in c["dialogues"] if d["id"] == a.dialogue), None) or \
      die(f"no dialogue '{a.dialogue}'. Options: " + ", ".join(d["id"] for c in data["categories"] for d in c["dialogues"]))
if not 1 <= a.version <= len(dlg["versions"]): die(f"'{a.dialogue}' has {len(dlg['versions'])} versions")
lines = dlg["versions"][a.version - 1]
for p in (a.ref_a, a.ref_b):
    if p and not os.path.isfile(p): die(f"reference file not found: {p}")

device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"Loading model on {device} (first run downloads ~3 GB)…")
model = ChatterboxMultilingualTTS.from_pretrained(device=device)

out = os.path.join(ROOT, "chatterbox_preview"); os.makedirs(out, exist_ok=True)
parts, gap = [], torch.zeros(1, int(model.sr * 0.45))
for i, l in enumerate(lines, 1):
    ref = a.ref_a if l["s"] == "A" else a.ref_b
    print(f"[{i}/{len(lines)}] {'Them' if l['s']=='A' else 'You '}: {l['t']}")
    try:
        wav = model.generate(l["t"], language_id="zh", audio_prompt_path=ref, cfg_weight=a.cfg).cpu()
    except Exception as e:
        die(f"line {i} failed: {e}")
    torchaudio.save(os.path.join(out, f"{l['id']}.wav"), wav, model.sr)
    parts += [wav, gap]
full = os.path.join(out, f"{a.dialogue}_v{a.version}.wav")
torchaudio.save(full, torch.cat(parts, dim=1), model.sr)
print(f"\nDone → {full}")
