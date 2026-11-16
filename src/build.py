import json, hashlib, csv, sys, re, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, '.')
from content import CATEGORIES
from core import CORE
from gloss import G, P
from seg import seg, PUNCT
from pypinyin import pinyin, Style
from pycccedict.cccedict import CcCedict
cc = CcCedict()

def py_word(w):
    if w in P: return P[w]
    if re.fullmatch(r'[A-Za-z0-9]+', w): return w
    s = [x[0] for x in pinyin(w, style=Style.TONE, heteronym=False)]
    # 一 / 不 tone sandhi inside a word
    out = []
    for i, syl in enumerate(s):
        ch = w[i] if i < len(w) else ''
        nxt = s[i+1] if i+1 < len(s) else None
        if ch in '一不' and nxt:
            t4 = any(c in nxt for c in 'àèìòùǜ')
            if ch == '一': syl = 'yí' if t4 else 'yì'
            if ch == '不': syl = 'bú' if t4 else 'bù'
        out.append(syl)
    return ' '.join(out)

missing = set()
def gloss(w):
    if w in G: return G[w]
    d = cc.get_definitions(w)
    if d: missing.add(w); return d[0]
    missing.add(w); return ''

def tokens(text):
    out = []
    for w in seg(text):
        if w in PUNCT or not w.strip():
            out.append({"w": w, "punct": True})
        else:
            out.append({"w": w, "p": py_word(w), "g": gloss(w)})
    return out

def lid(voice, text): return hashlib.sha1((voice + "|" + text).encode()).hexdigest()[:10]

audio_rows = {}
data = {"categories": [], "core": []}
for c in CATEGORIES:
    cat = {k: c[k] for k in ("id", "title", "zh", "icon")}; cat["dialogues"] = []
    for d in c["dialogues"]:
        dd = {k: d[k] for k in ("id", "title", "zh")}; dd["versions"] = []
        for vi, v in enumerate(d["versions"]):
            lines = []
            for spk, text in v:
                voice = d["voiceA"] if spk == "A" else "me"
                i = lid(voice, text)
                audio_rows[i] = (i, voice, text)
                lines.append({"id": i, "s": spk, "v": voice, "t": text, "tok": tokens(text)})
            dd["versions"].append(lines)
        cat["dialogues"].append(dd)
    data["categories"].append(cat)
for w, g, ex, en in CORE:
    data["core"].append({"w": w, "p": py_word(w.replace('…', '')) if '…' not in w else ' … '.join(py_word(x) for x in w.split('…')),
                         "g": g, "ex": tokens(ex), "exT": ex, "exEn": en})

tpl = open('app_template.html').read()
open('../index.html','w').write(tpl.replace('__DATA__', json.dumps(data, ensure_ascii=False)))
with open('../audio/lines.csv', 'w', newline='') as f:
    wr = csv.writer(f); wr.writerow(["id", "voice", "text"])
    for r in audio_rows.values(): wr.writerow(r)
print("lines:", len(audio_rows), "missing glosses:", sorted(missing))
