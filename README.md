# 对话 · Mandarin dialogues

Phone app for listening to and speaking everyday Mandarin dialogues (simplified, pinyin on every word).

- `index.html` — the whole app (generated; don't edit by hand)
- `src/content.py` — dialogues (categories → dialogues → versions → lines)
- `src/core.py` — core high-frequency words & patterns (flashcards)
- `src/gloss.py` — English glosses + pinyin fixes
- `src/build.py` — rebuilds `index.html` and `audio/lines.csv` (`pip install jieba pypinyin pycccedict`)
- `tools/gen_audio.py` — generates `audio/<id>.mp3` with ElevenLabs + `audio/manifest.json`

Lines without a recorded clip fall back to the phone's built-in Chinese voice (marked "PHONE VOICE").
