/* Kids scene engine: builds every scene from DATA, then seek(t) freezes all CSS animations at time t (frame-exact). */
(function () {
  const D = window.DATA, stage = document.getElementById('stage');
  const darker = (hex, k) => { const n = parseInt(hex.slice(1), 16); const f = c => Math.max(0, Math.min(255, Math.round(c * k)));
    return '#' + [f(n >> 16), f((n >> 8) & 255), f(n & 255)].map(v => v.toString(16).padStart(2, '0')).join(''); };
  const AR = n => String(n).replace(/[0-9]/g, d => '٠١٢٣٤٥٦٧٨٩'[d]);
  const esc = s => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const svg = (vb, w, h, body) => `<svg viewBox="${vb}" width="${w}" height="${h}" xmlns="http://www.w3.org/2000/svg">${body}</svg>`;
  const eyes = (dx, y, r) => `<g class="blink"><circle cx="${-dx}" cy="${y}" r="${r}" fill="#2b2b2b"/><circle cx="${dx}" cy="${y}" r="${r}" fill="#2b2b2b"/>
    <circle cx="${-dx + r * .35}" cy="${y - r * .4}" r="${r * .38}" fill="#fff"/><circle cx="${dx + r * .35}" cy="${y - r * .4}" r="${r * .38}" fill="#fff"/></g>`;
  const smile = (y, w) => `<path d="M${-w} ${y} q${w} ${w * .9} ${2 * w} 0" stroke="#5a2d0c" stroke-width="4" fill="none" stroke-linecap="round"/>`;

  const P = {
    chick: o => { const c = o.c || '#FFD23F', d = darker(c, .85);
      return svg('-100 -200 200 200', 200, 200, `
      <g stroke="#F28C28" stroke-width="7" stroke-linecap="round"><path d="M-28 -18 v14 M-28 -4 l-11 4 M-28 -4 l11 4"/><path d="M28 -18 v14 M28 -4 l-11 4 M28 -4 l11 4"/></g>
      <g class="wingL"><ellipse cx="-66" cy="-82" rx="20" ry="32" fill="${d}"/></g><g class="wingR"><ellipse cx="66" cy="-82" rx="20" ry="32" fill="${d}"/></g>
      <path d="M-4 -150 q-12 -26 6 -32 q-3 16 9 3 q4 19 -9 28z" fill="${d}"/>
      <ellipse cx="0" cy="-86" rx="72" ry="70" fill="${c}"/><ellipse cx="0" cy="-58" rx="46" ry="34" fill="#fff8c9" opacity=".55"/>
      ${eyes(25, -106, 11)}<circle cx="-44" cy="-84" r="10" fill="#ff8fab" opacity=".6"/><circle cx="44" cy="-84" r="10" fill="#ff8fab" opacity=".6"/>
      <path d="M-13 -93 L13 -93 L0 -74 Z" fill="#F28C28"/>`); },
    bunny: o => { const c = o.c || '#ffffff';
      return svg('-100 -240 200 240', 200, 240, `<g stroke="#d6d3e6" stroke-width="3">
      <g class="earL"><ellipse cx="-24" cy="-190" rx="15" ry="44" fill="${c}"/><ellipse cx="-24" cy="-188" rx="7" ry="32" fill="#ffc2d4" stroke="none"/></g>
      <g class="earR"><ellipse cx="24" cy="-190" rx="15" ry="44" fill="${c}"/><ellipse cx="24" cy="-188" rx="7" ry="32" fill="#ffc2d4" stroke="none"/></g>
      <ellipse cx="0" cy="-52" rx="52" ry="50" fill="${c}"/><circle cx="0" cy="-124" r="46" fill="${c}"/>
      <ellipse cx="-30" cy="-6" rx="20" ry="10" fill="${c}"/><ellipse cx="30" cy="-6" rx="20" ry="10" fill="${c}"/></g>
      ${eyes(18, -130, 8)}<ellipse cx="0" cy="-114" rx="7" ry="5" fill="#ff8fab"/>${smile(-106, 8)}
      <circle cx="-30" cy="-112" r="8" fill="#ff8fab" opacity=".5"/><circle cx="30" cy="-112" r="8" fill="#ff8fab" opacity=".5"/>`); },
    butterfly: o => { const c = o.c || '#ff6fa8', d = darker(c, .8);
      return svg('-60 -110 120 110', 120, 110, `<g class="flapL"><ellipse cx="-28" cy="-72" rx="26" ry="30" fill="${c}"/><ellipse cx="-22" cy="-34" rx="18" ry="20" fill="${d}"/><circle cx="-30" cy="-74" r="8" fill="#fff" opacity=".7"/></g>
      <g class="flapR"><ellipse cx="28" cy="-72" rx="26" ry="30" fill="${c}"/><ellipse cx="22" cy="-34" rx="18" ry="20" fill="${d}"/><circle cx="30" cy="-74" r="8" fill="#fff" opacity=".7"/></g>
      <ellipse cx="0" cy="-55" rx="6" ry="32" fill="#3b2a4a"/><path d="M-3 -85 q-10 -20 -18 -22 M3 -85 q10 -20 18 -22" stroke="#3b2a4a" stroke-width="3" fill="none"/>`); },
    seed: () => svg('-30 -30 60 30', 60, 30, `<ellipse cx="0" cy="-14" rx="18" ry="12" fill="#8a5a2b"/><ellipse cx="-5" cy="-18" rx="6" ry="3" fill="#b98352"/>`),
    hole: () => svg('-70 -30 140 30', 140, 30, `<ellipse cx="0" cy="-12" rx="60" ry="14" fill="#6b4423"/><ellipse cx="0" cy="-16" rx="44" ry="8" fill="#4a2e16"/>`),
    sprout: () => svg('-60 -110 120 110', 120, 110, `<path d="M0 0 C0 -40 2 -60 0 -80" stroke="#3fa34d" stroke-width="8" fill="none" stroke-linecap="round"/>
      <path d="M0 -70 C-30 -100 -55 -80 -50 -66 C-35 -60 -15 -62 0 -70Z" fill="#5cc96b"/><path d="M0 -78 C30 -110 56 -90 50 -76 C34 -70 14 -70 0 -78Z" fill="#4cb85c"/>`),
    sunflower: o => { let pet = ''; for (let k = 0; k < 16; k++) pet += `<ellipse cx="0" cy="-48" rx="13" ry="30" fill="${k % 2 ? '#FFC93C' : '#FFB703'}" transform="rotate(${k * 22.5})"/>`;
      return svg('-110 -330 220 330', 220, 330, `<path d="M0 0 C-6 -90 6 -160 0 -240" stroke="#3fa34d" stroke-width="12" fill="none"/>
      <path d="M0 -90 C-50 -120 -90 -100 -86 -80 C-60 -70 -30 -76 0 -90Z" fill="#5cc96b"/><path d="M0 -150 C50 -180 92 -160 86 -140 C60 -130 30 -136 0 -150Z" fill="#4cb85c"/>
      <g transform="translate(0 -250)">${pet}<circle r="36" fill="#7a4a1d"/><circle r="28" fill="#8f5a26"/>${eyes(11, -6, 5)}${smile(8, 9)}</g>`); },
    tree: () => svg('-130 -330 260 330', 260, 330, `<path d="M-22 0 L-14 -150 L14 -150 L22 0Z" fill="#8a5a2b"/>
      <circle cx="0" cy="-210" r="90" fill="#4cb85c"/><circle cx="-70" cy="-170" r="60" fill="#5cc96b"/><circle cx="70" cy="-170" r="60" fill="#3fa34d"/><circle cx="0" cy="-270" r="60" fill="#5cc96b"/>
      <circle cx="-40" cy="-200" r="10" fill="#ff5d5d"/><circle cx="45" cy="-230" r="10" fill="#ff5d5d"/><circle cx="20" cy="-160" r="10" fill="#ff5d5d"/>`),
    sun: () => { let r = ''; for (let k = 0; k < 12; k++) r += `<rect x="-6" y="-102" width="12" height="30" rx="6" fill="#FFB703" transform="rotate(${k * 30})"/>`;
      return svg('-110 -220 220 220', 220, 220, `<g transform="translate(0 -110)"><g class="spin">${r}</g><circle r="62" fill="#FFD23F"/>${eyes(20, -10, 7)}${smile(12, 14)}
      <circle cx="-34" cy="8" r="9" fill="#ff8fab" opacity=".55"/><circle cx="34" cy="8" r="9" fill="#ff8fab" opacity=".55"/></g>`); },
    moon: () => svg('-80 -160 160 160', 160, 160, `<path d="M20 -150 A72 72 0 1 0 20 -10 A56 56 0 1 1 20 -150Z" fill="#fff3b0"/><circle cx="-18" cy="-86" r="5" fill="#2b2b2b"/>${smile(-66, 8).replace('-8 -66', '-26 -66')}`),
    star: o => svg('-40 -80 80 80', 80, 80, `<path transform="translate(0 -40)" d="M0 -34 L10 -10 L34 -10 L14 6 L22 32 L0 16 L-22 32 L-14 6 L-34 -10 L-10 -10Z" fill="${o.c || '#FFE066'}"/>`),
    sparkle: o => svg('-30 -60 60 60', 60, 60, `<path transform="translate(0 -30)" d="M0 -28 Q4 -4 28 0 Q4 4 0 28 Q-4 4 -28 0 Q-4 -4 0 -28Z" fill="${o.c || '#fff'}"/>`),
    heart: o => svg('-40 -76 80 76', 80, 76, `<path transform="translate(0 -6)" d="M0 0 C-40 -26 -40 -62 -16 -66 C-6 -68 0 -60 0 -52 C0 -60 6 -68 16 -66 C40 -62 40 -26 0 0Z" fill="${o.c || '#ff4d6d'}"/>`),
    cloud: o => svg('-120 -110 240 110', 240, 110, `<g fill="${o.c || '#fff'}"><circle cx="-50" cy="-40" r="38"/><circle cx="0" cy="-60" r="50"/><circle cx="55" cy="-42" r="36"/><rect x="-90" y="-44" width="180" height="40" rx="20"/></g>${o.face ? eyes(16, -52, 6) + smile(-38, 10) : ''}`),
    rain: () => { let d = ''; for (let k = 0; k < 14; k++) d += `<line class="drop" style="animation-delay:-${(k * .37) % 1}s" x1="${-110 + k * 17}" y1="-200" x2="${-114 + k * 17}" y2="-182" stroke="#5ab0ff" stroke-width="5" stroke-linecap="round"/>`;
      return svg('-130 -210 260 210', 260, 210, d); },
    rainbow: () => { const cs = ['#ff5d5d', '#ff9f43', '#ffd23f', '#5cc96b', '#4dabf7', '#9775fa']; let a = '';
      cs.forEach((c, k) => { const r = 200 - k * 18; a += `<path d="M${-r} 0 A${r} ${r} 0 0 1 ${r} 0" stroke="${c}" stroke-width="18" fill="none"/>`; });
      return svg('-210 -210 420 210', 420, 210, a); },
    can: () => { let d = ''; for (let k = 0; k < 6; k++) d += `<circle class="pour" style="animation-delay:-${k * .13}s" cx="${-96 + (k % 3) * 8}" cy="-40" r="5" fill="#5ab0ff"/>`;
      return svg('-140 -150 260 150', 260, 150, `<g class="tilt"><path d="M-30 -120 h80 l-8 80 h-64z" fill="#4dabf7"/><path d="M50 -110 q40 10 30 50" stroke="#1c7ed6" stroke-width="10" fill="none"/>
      <path d="M-30 -100 L-90 -60 L-84 -52 L-30 -80z" fill="#1c7ed6"/><rect x="-100" y="-66" width="18" height="14" rx="3" fill="#1c7ed6"/>${d}</g>`); },
    house: o => svg('-110 -220 220 220', 220, 220, `<path d="M-90 -110 L0 -200 L90 -110Z" fill="${o.c || '#ff6b6b'}"/><rect x="-75" y="-112" width="150" height="112" fill="#ffe8cc"/>
      <rect x="-20" y="-60" width="40" height="60" rx="6" fill="#a0522d"/><rect x="-60" y="-90" width="30" height="28" fill="#a5d8ff"/><rect x="30" y="-90" width="30" height="28" fill="#a5d8ff"/>`),
    balloon: o => { const c = o.c || '#ff5d5d';
      return svg('-60 -230 120 230', 120, 230, `<path d="M0 -92 C-6 -60 8 -40 0 0" stroke="#666" stroke-width="2.5" fill="none"/>
      <ellipse cx="0" cy="-160" rx="52" ry="64" fill="${c}"/><path d="M-7 -97 L7 -97 L0 -88Z" fill="${darker(c, .8)}"/><ellipse cx="-20" cy="-185" rx="10" ry="18" fill="#fff" opacity=".45" transform="rotate(25 -20 -185)"/>
      ${o.n != null ? `<text x="0" y="-140" text-anchor="middle" font-family="Big" font-size="58" fill="#fff">${AR(o.n)}</text>` : ''}`); },
    shape: o => { const c = o.c || '#4dabf7', k = o.k || 'circle'; let s = '';
      if (k === 'circle') s = `<circle cx="0" cy="-90" r="88" fill="${c}"/>`;
      else if (k === 'square') s = `<rect x="-85" y="-175" width="170" height="170" rx="18" fill="${c}"/>`;
      else if (k === 'triangle') s = `<path d="M0 -185 L95 -5 L-95 -5Z" fill="${c}" stroke="${c}" stroke-width="14" stroke-linejoin="round"/>`;
      else if (k === 'star') s = `<path transform="translate(0 -95) scale(2.7)" d="M0 -34 L10 -10 L34 -10 L14 6 L22 32 L0 16 L-22 32 L-14 6 L-34 -10 L-10 -10Z" fill="${c}"/>`;
      else if (k === 'heart') s = `<path transform="translate(0 -8) scale(2.6)" d="M0 0 C-40 -26 -40 -62 -16 -66 C-6 -68 0 -60 0 -52 C0 -60 6 -68 16 -66 C40 -62 40 -26 0 0Z" fill="${c}"/>`;
      return svg('-100 -200 200 200', 200, 200, s + eyes(24, -100, 10) + smile(-72, 16)); },
    bignum: o => `<div class="bignum" style="--c:${o.c || '#ff6b6b'}"><b>${AR(o.n)}</b>${o.t ? `<i>${esc(o.t)}</i>` : ''}</div>`,
    letter: o => `<div class="letter" style="--c:${o.c || '#9775fa'}"><b>${esc(o.t)}</b>${o.w ? `<i>${esc(o.w)}</i>` : ''}</div>`,
    text: o => `<div class="ttl" dir="${o.dir || "rtl"}" style="--c:${o.c || '#ffffff'};font-size:${o.size || 64}px">${esc(o.t)}</div>`,
  };

  if (window.KIDS_ART) Object.assign(P, window.KIDS_ART.P);
  const BG = {
    day: ['#7cc8ff', '#d9f2ff', '#8bd17c', '#6cc35d', '#7ccf5a'],
    sunset: ['#ff9e7a', '#ffe1b0', '#7fb069', '#5f9e57', '#6cbf55'],
    night: ['#14214d', '#3b4c8c', '#2f5d3a', '#244b2e', '#2f6b3a'],
  };
  function background(name) {
    if (name === 'none') return '';
    if (window.KIDS_ART) { const h = window.KIDS_ART.background(name); if (h) return h; }
    if (name === 'room') return `<div class="bg room"><div class="dots"></div><div class="floor"></div></div>`;
    if (name === 'sky') return `<div class="bg" style="background:linear-gradient(#7cc8ff,#e3f6ff)"></div>`;
    if (name && name[0] === '#') return `<div class="bg" style="background:${name}"></div>`;
    const c = BG[name] || BG.day;
    let fl = ''; for (let k = 0; k < 18; k++) { const x = (k * 97) % 540, y = 790 + (k * 53) % 150, col = ['#ff6fa8', '#ffd23f', '#fff', '#b197fc'][k % 4];
      fl += `<circle cx="${x}" cy="${y}" r="7" fill="${col}"/><circle cx="${x}" cy="${y}" r="3" fill="#ffb703"/>`; }
    return `<div class="bg" style="background:linear-gradient(${c[0]},${c[1]} 70%)"></div>
      <svg class="hills" viewBox="0 0 540 960" width="540" height="960"><path d="M-20 700 Q120 560 280 660 T600 620 V960 H-20Z" fill="${c[2]}"/>
      <path d="M-20 760 Q160 650 330 730 T600 700 V960 H-20Z" fill="${c[3]}"/><rect x="-20" y="770" width="580" height="200" fill="${c[4]}"/>${fl}</svg>`;
  }

  function item(o, i) {
    const all = String(o.a || '').split(/\s+/).filter(Boolean), wave = all.includes('wave');
    const anims = all.filter(a => a !== 'wave');
    let inner = (P[o.p] || P.text)(o);
    if (o.f) inner = `<div style="transform:scaleX(-1)">${inner}</div>`;
    const outerA = anims.filter(a => ['walk', 'fly', 'drift', 'rise', 'fall', 'enter'].includes(a));
    const innerA = anims.filter(a => !outerA.includes(a));
    innerA.reverse().forEach(a => { inner = `<div class="a-${a}">${inner}</div>`; });
    outerA.forEach(a => { inner = `<div class="a-${a}">${inner}</div>`; });
    const st = `left:${o.x ?? 270}px;top:${o.y ?? 760}px;--s:${o.s ?? 1};--dl:${o.dl ?? i * .12}s;--dx:${o.dx ?? 180}px;--dy:${o.dy ?? -120}px;z-index:${o.z ?? 10 + i}`;
    return `<div class="it ${o.nopop ? '' : 'pop'}${o.talk ? ' talk' : ''}${wave ? ' waving' : ''}" style="${st}">${inner}</div>`;
  }

  function caption(sc) {
    if (!sc._words || !sc._words.length || sc.nocap) return '';
    return `<div class="cap"><div class="capin">${sc._words.map(w => `<span data-a="${w[1]}" data-b="${w[2]}">${esc(w[0])}</span>`).join(' ')}</div></div>`;
  }

  stage.insertAdjacentHTML('beforebegin', '<svg width="0" height="0" style="position:absolute"><defs><filter id="ksoft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="5"/></filter><linearGradient id="kfog" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".45"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs></svg>');
  const els = [];
  D.scenes.forEach((sc, i) => {
    const el = document.createElement('div');
    el.className = 'scene'; el.style.setProperty('--d', sc._dur); el.style.zIndex = i + 1;
    const bgName = sc.bg || (D.kind === 'lesson' ? 'room' : 'day');
    const cams = D.kind === 'story' ? ['kb', 'panL', 'in', 'panR'] : ['kb'];
    let cam = sc.cam || cams[i % cams.length], fo = '';
    const talker = (sc.items || []).find(o => o.talk);
    if (talker && !sc.cam) { cam = 'focus'; fo = `--fx:${talker.x}px;--fy:${(talker.y || 760) - 160}px`; }
    const front = window.KIDS_ART ? window.KIDS_ART.front(bgName) : '';
    const world = D.kind === 'toys' ? '' : `<div class="world cam-${cam}" style="${fo}">${background(bgName)}${(sc.items || []).map(item).join('')}${front}</div>`;
    const badge = i > 0 && D.title ? `<div class="badge"${D.wmPos === 'tr' ? ' style="right:auto;left:22px"' : ''}>${esc(D.title)}</div>` : '';
    const label = sc.label ? `<div class="label">${esc(sc.label)}</div>` : '';
    el.innerHTML = world + badge + label + caption(sc);
    if (D.kind === 'toys' && !sc.clip) el.innerHTML = `<div class="world">${(sc.items || []).map(item).join('')}</div>` + caption(sc);
    stage.appendChild(el); els.push(el);
  });

  function freeze(el, local) {
    el.getAnimations({ subtree: true }).forEach(a => { a.pause(); a.currentTime = Math.max(0, local) * 1000; });
    const lv = local - (D.scenes[els.indexOf(el)]._say0 || 0);
    el.querySelectorAll('.cap span').forEach(s => { const a = +s.dataset.a, b = +s.dataset.b;
      s.className = lv >= a && lv < b + .12 ? 'on' : (lv >= b ? 'done' : ''); });
  }

  window.seek = function (t) {
    window.scrollTo(0, 0); document.documentElement.scrollLeft = 0; document.body.scrollLeft = 0;
    D.scenes.forEach((sc, i) => {
      const el = els[i], local = t - sc._start, vis = local >= 0 && local < sc._dur + 0.4;
      el.style.visibility = vis ? 'visible' : 'hidden';
      if (!vis) return;
      if (i === 0 || D.kind === 'toys') { el.style.opacity = i === 0 ? 1 : Math.min(1, local / 0.35); }
      else { el.style.opacity = 1; const p = Math.min(1, local / 0.7), e = 1 - Math.pow(1 - p, 3); el.style.clipPath = p >= 1 ? 'none' : `circle(${(e * 120).toFixed(2)}% at 50% 58%)`; }
      freeze(el, local);
      const A = D.amp || [], fps = D.fps || 24;
      el.querySelectorAll('.talk').forEach(tk => {
        const m = sc.who === 'kid' ? (A[Math.round(t * fps)] || 0) : 0;
        tk.querySelectorAll('.mopen').forEach(x => { x.style.transform = `scaleY(${m.toFixed(3)})`; });
        tk.querySelectorAll('.mclosed').forEach(x => { x.style.opacity = m > 0.12 ? 0 : 1; });
      });
    });
  };
  window.overlay = function (i) {
    document.body.classList.add('clear'); document.documentElement.classList.add('clear');
    els.forEach((el, k) => { el.style.visibility = k === i ? 'visible' : 'hidden'; el.style.opacity = 1; });
    freeze(els[i], 1.2);
    els[i].querySelectorAll('.cap span').forEach(s => { s.className = ''; });
  };
  seek(0);
})();
