"""Kids Shorts renderer (1080x1920): animated stories / lessons drawn in HTML+SVG, or real toy clips (Pixabay),
with an Arabic narrator (edge-tts), word-by-word highlighted captions and a generated cheerful background tune.

usage: python3 kids_video.py '<spec json>' <outdir>
spec: {"type":"story|lesson|toys","title":"...","voice":"ar-SA-ZariyahNeural","rate":"-8%","pitch":"+6Hz",
       "scenes":[{"say":"...","bg":"day|sunset|night|room|sky","items":[{"p":"chick","x":270,"y":720,"s":1,"a":"bob"}, ...]},
                 {"say":"...","clip":"https://cdn.pixabay.com/...mp4","label":"سيارة"}]}
env KIDS_LOCAL=1 → no network TTS (silent placeholder audio), for local testing.
Outputs: video.mp4, cover.jpg, info.json
"""
import asyncio
import json
import math
import os
import random
import subprocess
import sys
import time
import urllib.error
import urllib.request
import wave

import numpy as np

spec = json.loads(sys.argv[1])
out = os.path.abspath(sys.argv[2])
work = os.path.join(out, 'work')
os.makedirs(work, exist_ok=True)
LOCAL = os.environ.get('KIDS_LOCAL') == '1'
FONTS = os.environ.get('AIB_FONTS', os.path.join(os.getcwd(), 'fonts'))
HERE = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, int(os.environ.get('KIDS_FPS', '24'))
T0 = time.time()
KIND = spec.get('type', 'story')


def log(*a):
    print('[%5.0fs]' % (time.time() - T0), *a, flush=True)


def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)


def dur(path):
    return float(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path]).stdout.strip())


def get(url, dest, tries=4):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (kids-videos)'})
            with urllib.request.urlopen(req, timeout=180) as r, open(dest, 'wb') as f:
                f.write(r.read())
            if os.path.getsize(dest) > 0:
                return dest
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3 * (i + 1))
    raise RuntimeError('download failed: %s (%s)' % (url, last))


# ---------------------------------------------------------------- 1) narration
# tts = "gemini" (expressive storyteller voice, Gemini TTS, keys in env GEMINI_KEYS) with automatic fallback to "edge" (Microsoft neural voice)
TTS = spec.get('tts') or 'gemini'
VOICE = spec.get('voice') or 'Sulafat'
KID_VOICE = spec.get('kidVoice') or 'Leda'
EDGE_VOICE = spec.get('edgeVoice') or (VOICE if '-' in VOICE else 'ar-SA-ZariyahNeural')
RATE, PITCH = spec.get('rate') or '-6%', spec.get('pitch') or '+8Hz'
STYLE = spec.get('style') or {
    'story': 'a warm, gentle and expressive storyteller reading a bedtime picture-book to little children (ages 3-7): smiling voice, playful wonder, soft surprise, clear and slightly slow',
    'lesson': 'a cheerful, energetic kindergarten teacher: bright, encouraging, rhythmic and clear, with excitement on each new number or word, slightly slow so children can repeat',
    'toys': 'an excited, friendly kids show host discovering toys with the children: joyful, playful, lots of wonder, clear and not too fast',
}.get(KIND, 'a warm, cheerful voice for young children')
TTS_MODELS = spec.get('ttsModels') or ['gemini-3.8-flash-tts', 'gemini-2.5-flash-preview-tts', 'gemini-3.1-flash-tts-preview', 'gemini-3.8-flash-lite-tts']


async def edge_tts_line(text, mp3, voice):
    import edge_tts
    try:
        c = edge_tts.Communicate(text, voice, rate=RATE, pitch=PITCH, boundary='WordBoundary')
    except TypeError:
        c = edge_tts.Communicate(text, voice, rate=RATE, pitch=PITCH)
    marks = []
    with open(mp3, 'wb') as f:
        async for ch in c.stream():
            if ch['type'] == 'audio':
                f.write(ch['data'])
            elif ch['type'] == 'WordBoundary':
                marks.append([ch['offset'] / 1e7, (ch['offset'] + ch['duration']) / 1e7, ch['text']])
    return marks


def gemini_tts(lines):
    """One request for the whole script → one PCM track, then split per scene on the long pauses."""
    keys = [k.strip() for k in os.environ.get('GEMINI_KEYS', '').split(',') if k.strip()]
    if not keys:
        raise RuntimeError('no GEMINI_KEYS')
    multi = any(w == 'kid' for w, _ in lines)
    script = '\n\n'.join(('Kid: ' if w == 'kid' else 'Narrator: ') + s if multi else s for w, s in lines)
    direction = ('Read the following Arabic script aloud for young children. Narrator: ' + STYLE + '. '
                 + ('Kid: a cute, happy, curious little cartoon character with a small bright voice. ' if multi else '')
                 + 'Pronounce Arabic correctly following the diacritics. Leave a clear pause of about one and a half seconds between paragraphs. '
                 'Do not read these instructions.\n\n')
    if multi:
        sc = {'multiSpeakerVoiceConfig': {'speakerVoiceConfigs': [
            {'speaker': 'Narrator', 'voiceConfig': {'prebuiltVoiceConfig': {'voiceName': VOICE}}},
            {'speaker': 'Kid', 'voiceConfig': {'prebuiltVoiceConfig': {'voiceName': KID_VOICE}}}]}}
    else:
        sc = {'voiceConfig': {'prebuiltVoiceConfig': {'voiceName': VOICE}}}
    body = json.dumps({'contents': [{'parts': [{'text': direction + script}]}],
                       'generationConfig': {'responseModalities': ['AUDIO'], 'speechConfig': sc}}).encode()
    last = None
    for model in TTS_MODELS:
        for k in keys:
            try:
                req = urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent' % model, data=body,
                                             headers={'Content-Type': 'application/json', 'x-goog-api-key': k})
                with urllib.request.urlopen(req, timeout=300) as r:
                    j = json.load(r)
                part = j['candidates'][0]['content']['parts'][0]['inlineData']
                pcm = __import__('base64').b64decode(part['data'])
                rate = 24000
                mt = part.get('mimeType', '')
                if 'rate=' in mt:
                    rate = int(mt.split('rate=')[1].split(';')[0])
                log('gemini tts ok', model, len(pcm) // 2 / rate, 's')
                return pcm, rate, model
            except urllib.error.HTTPError as e:
                last = '%s %s %s' % (model, e.code, e.read()[:160])
            except Exception as e:  # noqa: BLE001
                last = '%s %s' % (model, e)
            log('gemini tts fail:', last)
    raise RuntimeError(last)


def split_on_pauses(wav, n, weights):
    total = dur(wav)
    if n == 1:
        return [(0.0, total)]
    for d in (0.6, 0.45, 0.32):
        r = subprocess.run(['ffmpeg', '-i', wav, '-af', 'silencedetect=noise=-36dB:d=%s' % d, '-f', 'null', '-'], capture_output=True, text=True).stderr
        sil, st = [], None
        for line in r.splitlines():
            if 'silence_start:' in line:
                st = float(line.split('silence_start:')[1].split()[0])
            elif 'silence_end:' in line and st is not None:
                en = float(line.split('silence_end:')[1].split()[0])
                if st > 0.3 and en < total - 0.3:
                    sil.append((st, en))
                st = None
        if len(sil) < n - 1:
            continue
        # pick the n-1 gaps that best match the expected paragraph boundaries (long pauses near expected positions)
        exp, acc, sw = [], 0.0, sum(weights)
        for w in weights[:-1]:
            acc += w
            exp.append(acc / sw * total)
        chosen = []
        pool = sorted(sil, key=lambda s: -(s[1] - s[0]))[:max(n - 1, int((n - 1) * 1.8))]
        pool = sorted(pool)
        for e in exp:
            cand = [s for s in pool if s not in chosen and all(s[0] > c[1] for c in chosen)]
            if not cand:
                break
            best = min(cand, key=lambda s: abs((s[0] + s[1]) / 2 - e) / total * 3 - (s[1] - s[0]))
            chosen.append(best)
        if len(chosen) != n - 1:
            continue
        cuts = [0.0] + [(a + b) / 2 for a, b in chosen] + [total]
        segs = list(zip(cuts, cuts[1:]))
        ok = all(b - a > 0.5 for a, b in segs)
        ratio = [((b - a) / total) / (w / sw) for (a, b), w in zip(segs, weights)]
        if ok and min(ratio) > 0.3 and max(ratio) < 3.2:
            return segs
        log('split check failed d=%s ratios=%s' % (d, [round(x, 2) for x in ratio]))
    raise RuntimeError('could not split narration into %d parts' % n)


scenes = spec['scenes']
PAD_IN, PAD_OUT = 0.45, 0.75
lines = [(sc.get('who') or 'narrator', (sc.get('say') or '').strip()) for sc in scenes]
VOICE_USED = 'silent'
if not LOCAL and TTS == 'gemini' and all(s for _, s in lines):
    try:
        pcm, rate, model = gemini_tts(lines)
        full = os.path.join(work, 'gem.wav')
        with wave.open(full, 'wb') as wv:
            wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(rate); wv.writeframes(pcm)
        segs = split_on_pauses(full, len(scenes), [max(4, len(s)) for _, s in lines])
        for i, (a, b) in enumerate(segs):
            mp3 = os.path.join(work, 'v%02d.wav' % i)
            run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', '%.3f' % a, '-to', '%.3f' % b, '-i', full, '-af',
                 'silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.05,areverse,silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.08,areverse',
                 mp3])
            scenes[i]['_mp3'] = mp3
        VOICE_USED = 'gemini:%s:%s' % (model, VOICE)
    except Exception as e:  # noqa: BLE001
        log('gemini narration unavailable → edge voice:', e)
        for sc in scenes:
            sc.pop('_mp3', None)

t = 0.0
for i, sc in enumerate(scenes):
    say = (sc.get('say') or '').strip()
    words = say.split()
    marks = None
    if sc.get('_mp3'):
        d = dur(sc['_mp3'])
    elif say and not LOCAL:
        mp3 = os.path.join(work, 'v%02d.mp3' % i)
        voice = EDGE_VOICE
        if sc.get('who') == 'kid':
            voice = spec.get('edgeKidVoice') or 'ar-EG-SalmaNeural'
        for k in range(4):
            try:
                marks = asyncio.run(edge_tts_line(say, mp3, voice))
                break
            except Exception as e:  # noqa: BLE001
                log('tts retry', k, e)
                time.sleep(4 * (k + 1))
        else:
            raise SystemExit('TTS failed')
        sc['_mp3'] = mp3
        d = dur(mp3)
        VOICE_USED = 'edge:' + EDGE_VOICE
    else:
        d = max(1.2, len(say) * 0.075)
        mp3 = os.path.join(work, 'v%02d.mp3' % i)
        run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono', '-t', '%.2f' % d, mp3])
        sc['_mp3'] = mp3
    if not marks or len(marks) < len(words) * 0.6:
        # no word timings (Gemini voice): spread the words over the line by their length
        L = [len(w) + 2 for w in words] or [1]
        tot, acc, marks = sum(L), 0.0, []
        for w, l in zip(words, L):
            a = acc / tot * d * 0.97
            acc += l
            marks.append([a, acc / tot * d * 0.97, w])
    wt = [[round(marks[j][0], 3), round(marks[j][1], 3)] if j < len(marks) else [round(d, 3), round(d, 3)] for j in range(len(words))]
    sc['_voice'] = d
    sc['_words'] = [[w, a, b] for w, (a, b) in zip(words, wt)]
    sc['_dur'] = max(float(sc.get('min', 2.5)), PAD_IN + d + PAD_OUT + float(sc.get('hold', 0)))
    sc['_start'] = t
    t += sc['_dur']
TOTAL = t
log('scenes', len(scenes), 'total %.1fs' % TOTAL, 'voice', VOICE_USED)

# voice track: each line placed at scene start + PAD_IN
inputs, filt = [], []
for i, sc in enumerate(scenes):
    inputs += ['-i', sc['_mp3']]
    ms = int((sc['_start'] + PAD_IN) * 1000)
    filt.append('[%d:a]aresample=44100,aformat=channel_layouts=mono,adelay=%d[a%d]' % (i, ms, i))
filt.append(''.join('[a%d]' % i for i in range(len(scenes))) + 'amix=inputs=%d:normalize=0,apad,atrim=0:%.3f[v]' % (len(scenes), TOTAL))
voice = os.path.join(work, 'voice.wav')
run(['ffmpeg', '-y', '-loglevel', 'error', *inputs, '-filter_complex', ';'.join(filt), '-map', '[v]', '-ar', '44100', voice])


# ---------------------------------------------------------------- 2) cheerful music (synthesised, no licensing issues)
def music(path, seconds, seed):
    sr, bpm = 44100, float(spec.get('bpm', 104))
    rnd = random.Random(seed)
    beat = 60.0 / bpm
    n = int(sr * (seconds + 1))
    buf = np.zeros(n)
    tt = np.arange(int(sr * beat * 2)) / sr

    def note(f, start, length, vol, kind='bell'):
        s = int(start * sr)
        if s >= n:
            return
        L = min(int(length * sr), n - s)
        x = tt[:L] if L <= len(tt) else np.arange(L) / sr
        if kind == 'bell':
            w = np.sin(2 * np.pi * f * x) + 0.35 * np.sin(2 * np.pi * 2 * f * x) + 0.12 * np.sin(2 * np.pi * 4.01 * f * x)
            env = np.exp(-x * 5.5) * np.minimum(1, x * 300)
        elif kind == 'bass':
            w = 2 / np.pi * np.arcsin(np.sin(2 * np.pi * f * x))
            env = np.exp(-x * 3) * np.minimum(1, x * 200)
        else:  # shaker
            w = np.random.default_rng(int(start * 1000)).standard_normal(L)
            env = np.exp(-x * 60)
        buf[s:s + L] += vol * w * env

    hz = lambda m: 440 * 2 ** ((m - 69) / 12)  # noqa: E731
    keys = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]  # C G Am F
    penta = [60, 62, 64, 67, 69, 72, 74, 76]
    motif = [rnd.choice(penta) for _ in range(8)]
    bars = int(seconds / (beat * 4)) + 2
    for b in range(bars):
        ch = keys[b % 4]
        t0 = b * beat * 4
        note(hz(ch[0] - 24), t0, beat * 1.8, 0.30, 'bass')
        note(hz(ch[2] - 24), t0 + beat * 2, beat * 1.8, 0.24, 'bass')
        mot = motif if b % 2 == 0 else [m if rnd.random() < 0.6 else rnd.choice(penta) for m in motif]
        for k in range(8):
            if rnd.random() < 0.85:
                m = mot[k]
                if m % 12 not in [c % 12 for c in ch] and k % 2 == 0:
                    m = ch[k % 3] + 12
                note(hz(m), t0 + k * beat / 2, beat, 0.16)
        for k in range(8):
            note(0, t0 + k * beat / 2 + beat / 4, 0.05, 0.035 if k % 2 else 0.02, 'shaker')
    buf = buf[:int(sr * seconds)]
    fade = int(sr * 1.5)
    buf[:fade] *= np.linspace(0, 1, fade)
    buf[-fade:] *= np.linspace(1, 0, fade)
    buf = buf / (np.abs(buf).max() + 1e-9) * 0.9
    with wave.open(path, 'wb') as wv:
        wv.setnchannels(1)
        wv.setsampwidth(2)
        wv.setframerate(sr)
        wv.writeframes((buf * 32767).astype(np.int16).tobytes())


def sfx(path, seconds):
    """little cartoon sound effects: whoosh between scenes, pop when things appear, chime for sparkles"""
    sr = 44100
    buf = np.zeros(int(sr * (seconds + 1)))
    rng = np.random.default_rng(7)

    def put(t0, w):
        s = int(t0 * sr)
        if 0 <= s < len(buf):
            e = min(len(buf), s + len(w))
            buf[s:e] += w[:e - s]

    def pop(f=520):
        x = np.arange(int(sr * .12)) / sr
        return np.sin(2 * np.pi * (f + 900 * np.exp(-x * 40)) * x) * np.exp(-x * 38) * .5

    def whoosh():
        L = int(sr * .45)
        x = np.arange(L) / sr
        n = rng.standard_normal(L)
        k = np.convolve(n, np.ones(18) / 18, mode='same')
        return k * np.sin(np.pi * x / x[-1]) ** 2 * .35

    def chime():
        x = np.arange(int(sr * .7)) / sr
        return sum(np.sin(2 * np.pi * f * x) * np.exp(-x * (5 + k * 2)) for k, f in enumerate((1568, 2093, 2637))) * .12

    for i, sc in enumerate(scenes):
        st = sc['_start']
        if i:
            put(st - .15, whoosh())
        if sc.get('label'):
            put(st + .2, pop(640))
        n = 0
        for j, it in enumerate(sc.get('items') or []):
            if it.get('nopop') or n >= 6:
                continue
            tt = st + float(it.get('dl', j * .12)) + .08
            put(tt, chime() if it.get('p') in ('sparkle', 'star') else pop(440 + 60 * (n % 4)))
            n += 1
    buf = buf[:int(sr * seconds)]
    buf = np.clip(buf, -1, 1)
    with wave.open(path, 'wb') as wv:
        wv.setnchannels(1)
        wv.setsampwidth(2)
        wv.setframerate(sr)
        wv.writeframes((buf * 32767).astype(np.int16).tobytes())


fx = os.path.join(work, 'sfx.wav')
sfx(fx, TOTAL)
mus = os.path.join(work, 'music.wav')
music(mus, TOTAL, spec.get('seed') or spec.get('title', 'x'))
audio = os.path.join(work, 'audio.m4a')
MV = float(spec.get('musicVol', 0.13))
run(['ffmpeg', '-y', '-loglevel', 'error', '-i', voice, '-i', mus, '-i', fx, '-filter_complex',
     '[0:a]asplit[v1][v2];[1:a]volume=%.3f[m];[m][v1]sidechaincompress=threshold=0.03:ratio=4:attack=20:release=400[md];'
     '[2:a]volume=%.3f[fx];[v2]volume=1.6[vv];[vv][md][fx]amix=inputs=3:normalize=0,alimiter=limit=0.95[a]' % (MV, float(spec.get('sfxVol', 0.55))),
     '-map', '[a]', '-c:a', 'aac', '-b:a', '160k', audio])
log('audio ready')


# ---------------------------------------------------------------- 3) visuals
def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def ff(name, file):
    p = os.path.join(FONTS, file)
    return "@font-face{font-family:%s;src:url('file://%s')}" % (name, p) if os.path.exists(p) else ''


FONTCSS = ff('Kid', 'BalooBhaijaan2.ttf') + ff('Big', 'Lalezar.ttf')
CSS = open(os.path.join(HERE, 'kids_scene.css'), encoding='utf-8').read()
JS = open(os.path.join(HERE, 'kids_scene.js'), encoding='utf-8').read()

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    run([sys.executable, '-m', 'pip', 'install', '--quiet', 'playwright'])
    from playwright.sync_api import sync_playwright

video = os.path.join(out, 'video.mp4')
cover = os.path.join(out, 'cover.jpg')
pub = [{k: v for k, v in sc.items() if not k.startswith('_') or k in ('_start', '_dur', '_words')} for sc in scenes]
for p in pub:
    p['_say0'] = PAD_IN
DATA = json.dumps({'title': spec.get('title', ''), 'wmPos': spec.get('wmPos', 'tl') if spec.get('watermark') else '', 'kind': KIND, 'scenes': pub, 'total': TOTAL}, ensure_ascii=False)


def launch(p):
    for opt in ({'channel': 'chrome'}, {}):
        try:
            return p.chromium.launch(**opt)
        except Exception:  # noqa: BLE001
            continue
    raise SystemExit('no chrome')


if KIND != 'toys':
    html = ('<!doctype html><html dir="rtl"><head><meta charset="utf-8"><style>%s%s</style></head><body><div id="stage"></div>'
            '<script>window.DATA=%s;</script><script>%s</script></body></html>') % (FONTCSS, CSS, DATA, JS)
    hp = os.path.join(work, 'scene.html')
    open(hp, 'w', encoding='utf-8').write(html)
    nfr = int(math.ceil(TOTAL * FPS))
    raw = os.path.join(work, 'frames.mp4')
    enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(FPS), '-c:v', 'mjpeg', '-i', '-',
                            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', str(FPS), raw],
                           stdin=subprocess.PIPE)
    with sync_playwright() as p:
        br = launch(p)
        page = br.new_page(viewport={'width': 540, 'height': 960}, device_scale_factor=2)
        page.goto('file://' + hp)
        page.evaluate('document.fonts.ready')
        page.wait_for_timeout(300)
        for f in range(nfr):
            page.evaluate('seek(%f)' % (f / FPS))
            enc.stdin.write(page.screenshot(type='jpeg', quality=90))
            if f % (FPS * 5) == 0:
                log('frame', f, '/', nfr)
        ct = float(spec.get('coverAt', scenes[min(1, len(scenes) - 1)]['_start'] + 1.2))
        page.evaluate('seek(%f, true)' % ct)
        page.screenshot(path=cover, type='jpeg', quality=90)
        br.close()
    enc.stdin.close()
    enc.wait()
    run(['ffmpeg', '-y', '-loglevel', 'error', '-i', raw, '-i', audio, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'copy',
         '-shortest', '-movflags', '+faststart', video])
else:
    # real toy clips: blurred fill + framed clip + animated caption overlay (rendered once per scene)
    with sync_playwright() as p:
        br = launch(p)
        page = br.new_page(viewport={'width': 540, 'height': 960}, device_scale_factor=2)
        for i, sc in enumerate(scenes):
            html = ('<!doctype html><html dir="rtl"><head><meta charset="utf-8"><style>%s%s</style></head><body class="clear"><div id="stage"></div>'
                    '<script>window.DATA=%s;</script><script>%s</script></body></html>') % (FONTCSS, CSS, DATA, JS)
            hp = os.path.join(work, 'ov.html')
            open(hp, 'w', encoding='utf-8').write(html)
            page.goto('file://' + hp)
            page.evaluate('document.fonts.ready')
            page.evaluate('overlay(%d)' % i)
            page.wait_for_timeout(120)
            page.screenshot(path=os.path.join(work, 'ov%02d.png' % i), omit_background=True)
        br.close()
    parts = []
    for i, sc in enumerate(scenes):
        d = sc['_dur']
        dst = os.path.join(work, 'p%02d.mp4' % i)
        ov = os.path.join(work, 'ov%02d.png' % i)
        if sc.get('clip'):
            src = sc['clip'] if os.path.exists(sc['clip']) else get(sc['clip'], os.path.join(work, 'c%02d.mp4' % i))
            cd = dur(src)
            ss = max(0.0, min(float(sc.get('from', 0.5)), cd - 0.5))
            loop = ['-stream_loop', '-1'] if cd - ss < d else []
            fc = ('[0:v]fps=%d,split[a][b];'
                  '[a]scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,boxblur=28:2,eq=brightness=-0.08:saturation=1.25[bg];'
                  '[b]scale=1000:1000:force_original_aspect_ratio=decrease,setsar=1,'
                  'pad=iw+24:ih+24:12:12:color=white[fg];'
                  '[bg][fg]overlay=(W-w)/2:(H-h)/2-40[v1];'
                  '[1:v]format=rgba,fade=t=in:st=0.15:d=0.35:alpha=1[o];'
                  '[v1][o]overlay=0:0,fade=t=in:st=0:d=0.25,fade=t=out:st=%.2f:d=0.25,format=yuv420p[v]') % (FPS, W, H, W, H, d - 0.25)
            run(['ffmpeg', '-y', '-loglevel', 'error', *loop, '-ss', '%.2f' % ss, '-i', src, '-loop', '1', '-i', ov,
                 '-filter_complex', fc, '-map', '[v]', '-t', '%.3f' % d, '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21',
                 '-r', str(FPS), dst])
        else:  # title / end card: colourful plain background + overlay
            fc = ('[1:v]format=rgba[o];[0:v][o]overlay=0:0,fade=t=in:st=0:d=0.25,fade=t=out:st=%.2f:d=0.25,format=yuv420p[v]') % (d - 0.25)
            run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'gradients=s=%dx%d:c0=0xffb347:c1=0xff6fa8:x0=0:y0=0:x1=%d:y1=%d:d=%.2f:r=%d'
                 % (W, H, W, H, d, FPS), '-loop', '1', '-i', ov, '-filter_complex', fc, '-map', '[v]', '-t', '%.3f' % d,
                 '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '21', '-r', str(FPS), dst])
        parts.append(dst)
        log('toy part', i, round(d, 1))
    lst = os.path.join(work, 'parts.txt')
    open(lst, 'w').write(''.join("file '%s'\n" % x for x in parts))
    run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-i', audio, '-map', '0:v', '-map', '1:a',
         '-c:v', 'copy', '-c:a', 'copy', '-shortest', '-movflags', '+faststart', video])
    ci = min(1, len(parts) - 1)
    run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', '1.2', '-i', parts[ci], '-frames:v', '1', '-q:v', '3', cover])


# ---------------------------------------------------------------- 4) channel watermark (small logo in a corner)
WM = str(spec.get('watermark') or '')
if WM:
    from urllib.parse import urlparse
    host = urlparse(WM).hostname or ''
    ok_host = WM.startswith('https://') and (host.endswith('.ggpht.com') or host.endswith('.googleusercontent.com') or host == 'raw.githubusercontent.com')
    try:
        if not ok_host:
            raise RuntimeError('watermark host not allowed: ' + host)
        src = get(WM, os.path.join(work, 'wm_src'))
        wm = os.path.join(work, 'wm.png')
        S = 132
        if spec.get('wmShape', 'circle') == 'circle':
            R = S / 2
            vf = ('scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,format=rgba,'
                  "geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='if(lte(hypot(X-%f,Y-%f),%f),255,if(lte(hypot(X-%f,Y-%f),%f),255*(%f-hypot(X-%f,Y-%f))/1.5,0))'") % (
                S, S, S, S, R, R, R - 1.5, R, R, R, R, R, R)
        else:
            vf = 'scale=170:170:force_original_aspect_ratio=decrease,format=rgba'
        run(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-frames:v', '1', '-vf', vf, wm])
        pos = spec.get('wmPos', 'tl')
        x = '36' if pos == 'tl' else 'W-w-36'
        y = '40'
        alpha = float(spec.get('wmAlpha', 0.85))
        fc = '[1:v]format=rgba,colorchannelmixer=aa=%.2f[w];[0:v][w]overlay=%s:%s:format=auto,format=yuv420p[v]' % (alpha, x, y)
        tmp = os.path.join(work, 'wm_video.mp4')
        run(['ffmpeg', '-y', '-loglevel', 'error', '-i', video, '-i', wm, '-filter_complex', fc, '-map', '[v]', '-map', '0:a',
             '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-c:a', 'copy', '-movflags', '+faststart', tmp])
        os.replace(tmp, video)
        ctmp = os.path.join(work, 'wm_cover.jpg')
        run(['ffmpeg', '-y', '-loglevel', 'error', '-i', cover, '-i', wm, '-filter_complex', fc.replace(',format=yuv420p[v]', '[v]'), '-map', '[v]', '-q:v', '3', ctmp])
        os.replace(ctmp, cover)
        log('watermark added', pos)
    except Exception as e:  # noqa: BLE001
        log('watermark skipped:', e)

info = {'voice': VOICE_USED, 'type': KIND, 'title': spec.get('title'), 'duration': round(dur(video), 2), 'size': os.path.getsize(video), 'scenes': len(scenes)}
json.dump(info, open(os.path.join(out, 'info.json'), 'w'), ensure_ascii=False)
log('done', json.dumps(info, ensure_ascii=False))
