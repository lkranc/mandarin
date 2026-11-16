#!/usr/bin/env python3
"""
Generate dialogue audio with ElevenLabs — one MP3 per line.

Usage (from the repo root):
    export ELEVENLABS_API_KEY=sk_...
    python3 tools/gen_audio.py            # generates only clips that don't exist yet
    python3 tools/gen_audio.py --force    # regenerates everything

Reads  audio/lines.csv   (id, voice, text) — written by src/build.py
Writes audio/<id>.mp3 and audio/manifest.json (the app only plays clips listed there).
Any failure is printed in red and the script exits with code 1 — nothing fails silently.
No dependencies beyond Python 3.
"""
import csv, json, os, sys, time, urllib.request, urllib.error

# ---- set your three voices (ElevenLabs → Voices → copy Voice ID) ----------------
# Pick native Mandarin voices from the Voice Library (filter: Language = Chinese).
VOICES = {
    "f":  "PASTE_FEMALE_VOICE_ID",   # seller / waitress / receptionist
    "m":  "PASTE_MALE_VOICE_ID",     # vendor / waiter / stranger
    "me": "PASTE_YOUR_ROLE_VOICE_ID" # the traveller (your lines)
}
MODEL = "eleven_multilingual_v2"
SETTINGS = {"stability": 0.5, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": True, "speed": 0.95}
# --------------------------------------------------------------------------------

RED, GREEN, RESET = "\033[31m", "\033[32m", "\033[0m"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO = os.path.join(ROOT, "audio")

def die(msg):
    print(f"{RED}ERROR: {msg}{RESET}"); sys.exit(1)

def tts(text, voice_id, key):
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128",
        data=json.dumps({"text": text, "model_id": MODEL, "voice_settings": SETTINGS}).encode(),
        headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    if len(data) < 1000: raise RuntimeError(f"suspiciously small response ({len(data)} bytes)")
    return data

def main():
    key = os.environ.get("ELEVENLABS_API_KEY") or die("set ELEVENLABS_API_KEY first")
    missing = [k for k, v in VOICES.items() if v.startswith("PASTE_")]
    if missing: die(f"paste voice IDs for: {', '.join(missing)} (top of tools/gen_audio.py)")
    force = "--force" in sys.argv
    rows = list(csv.DictReader(open(os.path.join(AUDIO, "lines.csv"), encoding="utf-8")))
    ok, failed, skipped = 0, [], 0
    for i, r in enumerate(rows, 1):
        path = os.path.join(AUDIO, r["id"] + ".mp3")
        if os.path.exists(path) and not force: skipped += 1; continue
        try:
            data = tts(r["text"], VOICES[r["voice"]], key)
            open(path, "wb").write(data); ok += 1
            print(f"{GREEN}[{i}/{len(rows)}] ok{RESET}  {r['id']}  {r['text']}")
        except urllib.error.HTTPError as e:
            failed.append(r["id"]); print(f"{RED}[{i}/{len(rows)}] HTTP {e.code}: {e.read()[:200]!r}  {r['text']}{RESET}")
            if e.code in (401, 403): die("API key rejected — stopping.")
            if e.code == 429: time.sleep(5)
        except Exception as e:
            failed.append(r["id"]); print(f"{RED}[{i}/{len(rows)}] {e}  {r['text']}{RESET}")
    present = sorted(f[:-4] for f in os.listdir(AUDIO) if f.endswith(".mp3"))
    json.dump(present, open(os.path.join(AUDIO, "manifest.json"), "w"))
    print(f"\nGenerated {ok}, already had {skipped}, failed {len(failed)}. Manifest lists {len(present)} clips.")
    if failed:
        print(f"{RED}FAILED ids: {' '.join(failed)} — run the script again to retry them.{RESET}"); sys.exit(1)

if __name__ == "__main__":
    main()
