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
VOICE = spec.get('voice') or 'ar-SA-ZariyahNeural'
RATE, PITCH = spec.get('rate') or '-8%', spec.get('pitch') or '+6Hz'


async def tts(text, mp3):
    import edge_tts
    try:
        c = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH, boundary='WordBoundary')
    except TypeError:
        c = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    marks = []
    with open(mp3, 'wb') as f:
        async for ch in c.stream():
            if ch['type'] == 'audio':
                f.write(ch['data'])
            elif ch['type'] == 'WordBoundary':
                marks.append([ch['offset'] / 1e7, (ch['offset'] + ch['duration']) / 1e7, ch['text']])
    return marks


scenes = spec['scenes']
PAD_IN, PAD_OUT = 0.45, 0.75
t = 0.0
for i, sc in enumerate(scenes):
    say = (sc.get('say') or '').strip()
    words = say.split()
    mp3 = os.path.join(work, 'v%02d.mp3' % i)
    if say and not LOCAL:
        for k in range(4):
            try:
                marks = asyncio.run(tts(say, mp3))
                break
            except Exception as e:  # noqa: BLE001
                log('tts retry', k, e)
                time.sleep(4 * (k + 1))
        else:
            raise SystemExit('TTS failed')
        d = dur(mp3)
    else:
        d = max(1.2, len(say) * 0.075)
        run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono', '-t', '%.2f' % d, mp3])
        marks, step = [], d / max(1, len(words))
        for j, w in enumerate(words):
            marks.append([j * step, (j + 1) * step, w])
    # map boundaries → caption words (same order)
    wt = []
    for j, w in enumerate(words):
        if j < len(marks):
            wt.append([round(marks[j][0], 3), round(marks[j][1], 3)])
        else:
            wt.append([round(d, 3), round(d, 3)])
    sc['_mp3'], sc['_voice'] = mp3, d
    sc['_words'] = [[w, a, b] for w, (a, b) in zip(words, wt)]
    sc['_dur'] = max(float(sc.get('min', 2.5)), PAD_IN + d + PAD_OUT + float(sc.get('hold', 0)))
    sc['_start'] = t
    t += sc['_dur']
TOTAL = t
log('scenes', len(scenes), 'total %.1fs' % TOTAL)

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


mus = os.path.join(work, 'music.wav')
music(mus, TOTAL, spec.get('seed') or spec.get('title', 'x'))
audio = os.path.join(work, 'audio.m4a')
MV = float(spec.get('musicVol', 0.13))
run(['ffmpeg', '-y', '-loglevel', 'error', '-i', voice, '-i', mus, '-filter_complex',
     '[1:a]volume=%.3f[m];[m][0:a]sidechaincompress=threshold=0.03:ratio=4:attack=20:release=400[md];'
     '[0:a]volume=1.6[vv];[vv][md]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]' % MV,
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
DATA = json.dumps({'title': spec.get('title', ''), 'kind': KIND, 'scenes': pub, 'total': TOTAL}, ensure_ascii=False)


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
                  '[b]scale=1000:1240:force_original_aspect_ratio=decrease,setsar=1,'
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

info = {'type': KIND, 'title': spec.get('title'), 'duration': round(dur(video), 2), 'size': os.path.getsize(video), 'scenes': len(scenes)}
json.dump(info, open(os.path.join(out, 'info.json'), 'w'), ensure_ascii=False)
log('done', json.dumps(info, ensure_ascii=False))
