/* Kids art v2: shaded characters with expressions & lip-sync mouths, layered depth backgrounds. Loaded before kids_scene.js. */
(function () {
  let U = 0;
  const uid = p => (p || 'g') + (++U);
  const shade = (hex, k) => { const n = parseInt(hex.slice(1), 16); const f = c => Math.max(0, Math.min(255, Math.round(k >= 1 ? c + (255 - c) * (k - 1) : c * k)));
    return '#' + [f(n >> 16), f((n >> 8) & 255), f(n & 255)].map(v => v.toString(16).padStart(2, '0')).join(''); };
  const svg = (vb, w, h, body) => `<svg viewBox="${vb}" width="${w}" height="${h}" xmlns="http://www.w3.org/2000/svg" overflow="visible">${body}</svg>`;
  const rad = (id, c, cx, cy) => `<radialGradient id="${id}" cx="${cx || '38%'}" cy="${cy || '30%'}" r="75%"><stop offset="0" stop-color="${shade(c, 1.35)}"/><stop offset=".55" stop-color="${c}"/><stop offset="1" stop-color="${shade(c, .78)}"/></radialGradient>`;
  const lin = (id, a, b) => `<linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${a}"/><stop offset="1" stop-color="${b}"/></linearGradient>`;
  const shadow = rx => `<ellipse cx="0" cy="-3" rx="${rx}" ry="${rx * .17}" fill="#1b2a10" opacity=".22" filter="url(#ksoft)"/>`;

  // big glossy eyes + brows by mood
  function eyes(dx, y, r, mood) {
    const g = uid('eye');
    const bt = { happy: [5, 0, 0], sad: [2, 7, 0], surprised: [9, 0, 7], angry: [1, -7, 0] }[mood] || [5, 0, 0];
    const b = s => { const yb = y - r * 1.85 - bt[2], xo = s * (dx + r * 1.05), xi = s * (dx - r * .9);
      return `<path d="M${xo} ${yb} Q${s * dx} ${yb - bt[0]} ${xi} ${yb - bt[1]}" stroke="#4a2a14" stroke-width="${r * .36}" fill="none" stroke-linecap="round" opacity=".8"/>`; };
    const e = s => `<ellipse cx="${s * dx}" cy="${y}" rx="${r}" ry="${r * (mood === 'surprised' ? 1.3 : 1.15)}" fill="url(#${g})"/>
      <circle cx="${s * dx + r * .38}" cy="${y - r * .42}" r="${r * .36}" fill="#fff"/><circle cx="${s * dx - r * .35}" cy="${y + r * .42}" r="${r * .16}" fill="#fff" opacity=".85"/>`;
    return `<defs><radialGradient id="${g}" cx="40%" cy="35%" r="70%"><stop offset="0" stop-color="#5b3a22"/><stop offset=".6" stop-color="#2a1608"/><stop offset="1" stop-color="#120802"/></radialGradient></defs>
      ${b(-1)}${b(1)}<g class="blink">${e(-1)}${e(1)}</g>`;
  }
  // mouth: closed shape (smile / frown) + open mouth that the engine scales with the voice
  function mouth(y, w, mood) {
    const closed = mood === 'sad' ? `<path d="M${-w} ${y + w * .45} q${w} ${-w * .75} ${2 * w} 0" stroke="#7a2a1a" stroke-width="${w * .32}" fill="none" stroke-linecap="round"/>`
      : mood === 'surprised' ? `<ellipse cx="0" cy="${y + 2}" rx="${w * .35}" ry="${w * .45}" fill="#7a2a1a"/>`
      : `<path d="M${-w} ${y} q${w} ${w * .95} ${2 * w} 0" stroke="#7a2a1a" stroke-width="${w * .32}" fill="none" stroke-linecap="round"/>`;
    return `<g class="mclosed">${closed}</g><g class="mopen" style="transform:scaleY(0)"><ellipse cx="0" cy="${y + w * .45}" rx="${w * .78}" ry="${w * .62}" fill="#6b1d12"/>
      <ellipse cx="0" cy="${y + w * .78}" rx="${w * .48}" ry="${w * .26}" fill="#ff7b8a"/><rect x="${-w * .55}" y="${y - w * .08}" width="${w * 1.1}" height="${w * .22}" rx="${w * .1}" fill="#fff"/></g>`;
  }
  const cheeks = (dx, y, r) => `<ellipse cx="${-dx}" cy="${y}" rx="${r}" ry="${r * .62}" fill="#ff7f9e" opacity=".42"/><ellipse cx="${dx}" cy="${y}" rx="${r}" ry="${r * .62}" fill="#ff7f9e" opacity=".42"/>`;

  const P = {
    chick: o => { const c = o.c || '#FFD23F', g = uid('ch'), w = uid('wg'), m = o.mood || 'happy';
      return svg('-100 -205 200 205', 200, 205, `<defs>${rad(g, c)}${rad(w, shade(c, .9), '30%', '20%')}</defs>${shadow(70)}
      <g stroke="#ee8a1c" stroke-width="7" stroke-linecap="round"><path d="M-28 -20 v14 M-28 -6 l-11 4 M-28 -6 l11 4"/><path d="M28 -20 v14 M28 -6 l-11 4 M28 -6 l11 4"/></g>
      <g class="wingL"><ellipse cx="-68" cy="-84" rx="21" ry="33" fill="url(#${w})"/></g><g class="wingR"><ellipse cx="68" cy="-84" rx="21" ry="33" fill="url(#${w})"/></g>
      <path d="M-4 -152 q-12 -26 6 -32 q-3 16 9 3 q4 19 -9 28z" fill="${shade(c, .88)}"/>
      <ellipse cx="0" cy="-88" rx="73" ry="71" fill="url(#${g})"/><ellipse cx="0" cy="-58" rx="44" ry="30" fill="#fffbe0" opacity=".45"/>
      <ellipse cx="-30" cy="-138" rx="22" ry="10" fill="#fff" opacity=".35" transform="rotate(-25 -30 -138)"/>
      ${eyes(25, -110, 12, m)}${cheeks(46, -84, 11)}
      <g transform="translate(0 -95)">${'<ellipse class="mopen" style="transform:scaleY(0)" cx="0" cy="9" rx="10" ry="9" fill="#6b1d12"/>'}<path d="M-14 0 L14 0 L0 15 Z" fill="#ff9a1f"/><path d="M-14 0 L14 0 L0 6Z" fill="#ffb54d"/></g>`); },
    bunny: o => { const c = o.c || '#ffffff', g = uid('bn'), m = o.mood || 'happy';
      return svg('-100 -250 200 250', 200, 250, `<defs>${rad(g, c === '#ffffff' ? '#f4f1fb' : c)}</defs>${shadow(58)}
      <g class="earL"><ellipse cx="-25" cy="-196" rx="16" ry="46" fill="url(#${g})"/><ellipse cx="-25" cy="-192" rx="8" ry="33" fill="#ffb3c8"/></g>
      <g class="earR"><ellipse cx="25" cy="-196" rx="16" ry="46" fill="url(#${g})"/><ellipse cx="25" cy="-192" rx="8" ry="33" fill="#ffb3c8"/></g>
      <ellipse cx="0" cy="-54" rx="53" ry="51" fill="url(#${g})"/><ellipse cx="0" cy="-46" rx="30" ry="30" fill="#fff" opacity=".5"/>
      <circle cx="0" cy="-128" r="48" fill="url(#${g})"/>
      <ellipse cx="-31" cy="-8" rx="21" ry="11" fill="url(#${g})"/><ellipse cx="31" cy="-8" rx="21" ry="11" fill="url(#${g})"/>
      ${eyes(18, -134, 9, m)}<ellipse cx="0" cy="-118" rx="7" ry="5" fill="#ff8fab"/>${mouth(-108, 9, m)}${cheeks(31, -114, 9)}`); },
    girl: o => { const c = o.c || '#ff6fa8', hair = o.hair || '#5a3420', skin = o.skin || '#ffd6b3', bow = o.bow || '#ffd23f', m = o.mood || 'happy';
      const gs = uid('sk'), gd = uid('dr'), gh = uid('hr');
      return svg('-110 -300 220 300', 220, 300, `<defs>${rad(gs, skin, '40%', '30%')}${rad(gd, c, '40%', '20%')}${rad(gh, hair, '35%', '25%')}</defs>${shadow(48)}
      <rect x="-24" y="-66" width="15" height="56" rx="7" fill="url(#${gs})"/><rect x="9" y="-66" width="15" height="56" rx="7" fill="url(#${gs})"/>
      <ellipse cx="-17" cy="-10" rx="15" ry="9" fill="#e64980"/><ellipse cx="17" cy="-10" rx="15" ry="9" fill="#e64980"/>
      <g class="armL"><rect x="-58" y="-142" width="16" height="62" rx="8" fill="url(#${gs})" transform="rotate(14 -50 -140)"/></g>
      <g class="armR"><rect x="42" y="-142" width="16" height="62" rx="8" fill="url(#${gs})" transform="rotate(-14 50 -140)"/></g>
      <path d="M-36 -152 Q0 -162 36 -152 L64 -62 Q0 -48 -64 -62 Z" fill="url(#${gd})"/>
      <path d="M-20 -154 Q0 -140 20 -154 L14 -160 Q0 -152 -14 -160Z" fill="#fff" opacity=".9"/>
      <circle cx="-72" cy="-205" r="24" fill="url(#${gh})"/><circle cx="72" cy="-205" r="24" fill="url(#${gh})"/>
      <path d="M-82 -228 l-14 -14 l2 22z M-62 -228 l14 -14 l-2 22z" fill="${bow}"/><circle cx="-72" cy="-229" r="6" fill="${shade(bow, .85)}"/>
      <path d="M62 -228 l-14 -14 l2 22z M82 -228 l14 -14 l-2 22z" fill="${bow}"/><circle cx="72" cy="-229" r="6" fill="${shade(bow, .85)}"/>
      <circle cx="0" cy="-208" r="68" fill="url(#${gh})"/>
      <ellipse cx="0" cy="-196" rx="60" ry="58" fill="url(#${gs})"/>
      <path d="M-62 -214 Q-58 -272 0 -274 Q58 -272 62 -214 Q40 -240 10 -236 Q-20 -250 -62 -214Z" fill="url(#${gh})"/>
      <ellipse cx="-24" cy="-258" rx="18" ry="6" fill="#fff" opacity=".22" transform="rotate(-20 -24 -258)"/>
      ${eyes(22, -194, 11, m)}${cheeks(36, -174, 11)}<path d="M-3 -180 q3 4 6 0" stroke="#d9906a" stroke-width="3" fill="none" stroke-linecap="round"/>${mouth(-166, 11, m)}`); },
    boy: o => { const c = o.c || '#4dabf7', hair = o.hair || '#3b2416', skin = o.skin || '#f6c9a0', m = o.mood || 'happy';
      const gs = uid('sk'), gd = uid('sh'), gh = uid('hr');
      return svg('-110 -300 220 300', 220, 300, `<defs>${rad(gs, skin, '40%', '30%')}${rad(gd, c, '40%', '20%')}${rad(gh, hair, '35%', '25%')}</defs>${shadow(48)}
      <rect x="-24" y="-72" width="16" height="62" rx="7" fill="url(#${gs})"/><rect x="8" y="-72" width="16" height="62" rx="7" fill="url(#${gs})"/>
      <ellipse cx="-17" cy="-10" rx="16" ry="9" fill="#343a40"/><ellipse cx="17" cy="-10" rx="16" ry="9" fill="#343a40"/>
      <path d="M-40 -96 h80 l4 34 h-88z" fill="#364fc7"/>
      <g class="armL"><rect x="-60" y="-146" width="17" height="64" rx="8" fill="url(#${gs})" transform="rotate(12 -52 -144)"/><rect x="-61" y="-150" width="20" height="26" rx="9" fill="url(#${gd})" transform="rotate(12 -52 -144)"/></g>
      <g class="armR"><rect x="43" y="-146" width="17" height="64" rx="8" fill="url(#${gs})" transform="rotate(-12 52 -144)"/><rect x="41" y="-150" width="20" height="26" rx="9" fill="url(#${gd})" transform="rotate(-12 52 -144)"/></g>
      <path d="M-40 -154 Q0 -164 40 -154 L42 -92 Q0 -84 -42 -92 Z" fill="url(#${gd})"/><circle cx="0" cy="-126" r="9" fill="#fff" opacity=".85"/><circle cx="0" cy="-126" r="4" fill="${shade(c, .7)}"/>
      <ellipse cx="0" cy="-200" rx="62" ry="60" fill="url(#${gs})"/>
      <ellipse cx="-62" cy="-196" rx="10" ry="14" fill="url(#${gs})"/><ellipse cx="62" cy="-196" rx="10" ry="14" fill="url(#${gs})"/>
      <path d="M-62 -210 Q-66 -270 -6 -272 Q60 -274 64 -214 Q56 -236 34 -236 L40 -250 L20 -238 L18 -254 L0 -238 L-10 -252 L-20 -236 Q-46 -238 -62 -210Z" fill="url(#${gh})"/>
      ${eyes(22, -196, 11, m)}${cheeks(36, -176, 10)}<path d="M-3 -182 q3 4 6 0" stroke="#c98258" stroke-width="3" fill="none" stroke-linecap="round"/>${mouth(-168, 11, m)}`); },
    apple: o => { const g = uid('ap'); return svg('-30 -62 60 62', 60, 62, `<defs>${rad(g, o.c || '#ef3b3b')}</defs>
      <path d="M0 -50 q-4 -8 2 -12" stroke="#6b3e1e" stroke-width="4" fill="none" stroke-linecap="round"/><path d="M3 -52 q14 -12 22 -4 q-10 10 -22 4z" fill="#51cf66"/>
      <path d="M0 -46 C-30 -58 -34 -18 -16 -4 C-8 2 -4 -2 0 -2 C4 -2 8 2 16 -4 C34 -18 30 -58 0 -46Z" fill="url(#${g})"/><ellipse cx="-12" cy="-34" rx="5" ry="9" fill="#fff" opacity=".4" transform="rotate(25 -12 -34)"/>`); },
    basket: o => { const g = uid('bk'); let ap = ''; [[-30, -66], [0, -74], [30, -66], [-14, -80], [16, -82]].forEach(([x, y], k) => { ap += `<circle cx="${x}" cy="${y}" r="17" fill="${['#ef3b3b', '#f03e3e', '#ffd43b', '#e03131', '#ff6b6b'][k]}"/><ellipse cx="${x - 5}" cy="${y - 6}" rx="4" ry="6" fill="#fff" opacity=".35"/>`; });
      return svg('-80 -120 160 120', 160, 120, `<defs>${lin(g, '#d9a066', '#8a5a2b')}</defs>${shadow(64)}<path d="M-60 -100 Q0 -150 60 -100" stroke="#8a5a2b" stroke-width="8" fill="none"/>${ap}
      <path d="M-66 -62 h132 l-14 56 q-52 10 -104 0z" fill="url(#${g})"/><path d="M-60 -44 h120 M-56 -26 h112" stroke="#6b4423" stroke-width="3" opacity=".5"/>`); },
    tree: o => { const g1 = uid('tr'), g2 = uid('tk'); let ap = '';
      if (o.apples !== false) [[-50, -230], [40, -260], [10, -190], [70, -205], [-15, -285]].forEach(([x, y]) => { ap += `<circle cx="${x}" cy="${y}" r="12" fill="#ef3b3b"/><circle cx="${x - 4}" cy="${y - 4}" r="4" fill="#fff" opacity=".45"/>`; });
      return svg('-150 -360 300 360', 300, 360, `<defs>${rad(g1, '#4cb85c', '35%', '25%')}${lin(g2, '#9a6a3a', '#6b4423')}</defs>${shadow(90)}
      <path d="M-24 0 Q-14 -90 -18 -170 L18 -170 Q14 -90 24 0Z" fill="url(#${g2})"/><path d="M-6 -60 q-30 -30 -40 -70" stroke="#7a5030" stroke-width="10" fill="none" stroke-linecap="round"/>
      <circle cx="-70" cy="-200" r="62" fill="url(#${g1})"/><circle cx="70" cy="-200" r="62" fill="url(#${g1})"/><circle cx="0" cy="-250" r="90" fill="url(#${g1})"/><circle cx="-40" cy="-300" r="50" fill="url(#${g1})"/><circle cx="45" cy="-300" r="48" fill="url(#${g1})"/>
      <ellipse cx="-30" cy="-300" rx="30" ry="14" fill="#fff" opacity=".18"/>${ap}`); },
    bush: o => { const g = uid('bs'); return svg('-110 -110 220 110', 220, 110, `<defs>${rad(g, o.c || '#3f9a4a', '40%', '20%')}</defs>
      <circle cx="-60" cy="-40" r="44" fill="url(#${g})"/><circle cx="0" cy="-62" r="56" fill="url(#${g})"/><circle cx="62" cy="-42" r="44" fill="url(#${g})"/><rect x="-100" y="-40" width="200" height="40" fill="url(#${g})"/>
      ${o.flowers ? '<circle cx="-40" cy="-70" r="7" fill="#ff8fab"/><circle cx="30" cy="-86" r="7" fill="#fff"/><circle cx="70" cy="-52" r="7" fill="#ffd43b"/>' : ''}`); },
    moon: () => svg('-90 -180 180 180', 180, 180, `<circle cx="0" cy="-90" r="80" fill="#fff6c8" opacity=".18" filter="url(#ksoft)"/><path d="M22 -158 A70 70 0 1 0 22 -22 A54 54 0 1 1 22 -158Z" fill="#fff3b0"/><circle cx="-30" cy="-110" r="7" fill="#f1e08a" opacity=".6"/><circle cx="-20" cy="-60" r="5" fill="#f1e08a" opacity=".6"/>`),
    bench: () => svg('-110 -110 220 110', 220, 110, `${shadow(90)}<rect x="-100" y="-74" width="200" height="16" rx="6" fill="#b5651d"/><rect x="-100" y="-104" width="200" height="14" rx="6" fill="#c97a2e"/>
      <rect x="-86" y="-60" width="12" height="58" fill="#6b4423"/><rect x="74" y="-60" width="12" height="58" fill="#6b4423"/>`),
  };

  // layered depth backgrounds (each layer drifts at its own speed = parallax)
  const PAL = {
    day: { sky: ['#4fb3ff', '#a9dcff', '#fff3d6'], far: '#a7cbe6', mid: ['#8fd16f', '#5eae4f'], near: ['#6cc35d', '#4a9c40'], glow: 'rgba(255,244,200,.85)', fog: 'rgba(255,255,255,.35)' },
    sunset: { sky: ['#ff8a65', '#ffc48a', '#ffe9c4'], far: '#d79aa0', mid: ['#9ac46b', '#6f9e4b'], near: ['#76b257', '#4f8a3c'], glow: 'rgba(255,210,150,.9)', fog: 'rgba(255,220,200,.35)' },
    night: { sky: ['#0d1b4c', '#233a7a', '#3e4f8f'], far: '#2b3d6e', mid: ['#2f5d4a', '#22473a'], near: ['#2d6a46', '#1f4d33'], glow: 'rgba(255,248,210,.35)', fog: 'rgba(120,140,220,.18)' },
  };
  function background(name) {
    const p = PAL[name];
    if (!p) return null;
    let flowers = '', grass = '';
    for (let k = 0; k < 26; k++) { const x = (k * 83) % 600 - 30, y = 830 + (k * 37) % 120, col = ['#ff8fab', '#ffe066', '#fff', '#b197fc', '#ff922b'][k % 5];
      flowers += `<g transform="translate(${x} ${y}) scale(${.7 + (k % 3) * .25})"><circle r="6" cx="-6" fill="${col}"/><circle r="6" cx="6" fill="${col}"/><circle r="6" cy="-6" fill="${col}"/><circle r="6" cy="6" fill="${col}"/><circle r="4" fill="#ffb703"/></g>`; }
    for (let k = 0; k < 70; k++) { const x = (k * 37) % 600 - 30, y = 800 + (k * 53) % 160; grass += `<path d="M${x} ${y} q2 -14 6 -18" stroke="${k % 2 ? p.near[1] : p.mid[0]}" stroke-width="3" fill="none" stroke-linecap="round" opacity=".7"/>`; }
    const stars = name === 'night' ? Array.from({ length: 40 }, (_, k) => `<circle class="tw" style="animation-delay:-${(k * .37) % 2}s" cx="${(k * 131) % 540}" cy="${(k * 89) % 520}" r="${1 + (k % 3) * .7}" fill="#fff"/>`).join('') : '';
    return `<div class="bg" style="background:linear-gradient(${p.sky[0]},${p.sky[1]} 48%,${p.sky[2]} 72%)"></div>
      <div class="bg" style="background:radial-gradient(circle at 80% 18%,${p.glow},transparent 38%)"></div>
      <svg class="lay l-far" viewBox="0 0 640 960" width="640" height="960">${stars}<path d="M-20 640 L60 560 L130 610 L230 500 L330 600 L420 530 L520 610 L660 540 V960 H-20Z" fill="${p.far}" opacity=".85"/>
        <rect x="-20" y="560" width="680" height="200" fill="url(#kfog)" opacity=".9"/></svg>
      <svg class="lay l-mid" viewBox="0 0 640 960" width="640" height="960"><defs>${lin('m' + name, p.mid[0], p.mid[1])}</defs><path d="M-20 700 Q120 590 290 670 T660 640 V960 H-20Z" fill="url(#m${name})"/>
        ${[60, 180, 470, 560].map((x, k) => `<g transform="translate(${x} ${662 - (k % 2) * 14}) scale(${.5 + (k % 2) * .2})"><rect x="-5" y="-10" width="10" height="34" fill="#6b4423"/><circle cy="-30" r="30" fill="${p.mid[1]}"/><circle cy="-36" cx="-8" r="18" fill="${p.mid[0]}" opacity=".7"/></g>`).join('')}</svg>
      <svg class="lay l-near" viewBox="0 0 640 960" width="640" height="960"><defs>${lin('n' + name, p.near[0], p.near[1])}</defs><path d="M-20 790 Q170 710 360 770 T660 760 V960 H-20Z" fill="url(#n${name})"/>${grass}${flowers}</svg>
      <div class="bg" style="background:linear-gradient(transparent 55%,${p.fog} 72%,transparent 85%)"></div>`;
  }
  function front(name) { // foreground depth-of-field bushes + light + particles + vignette
    if (!PAL[name] && name !== 'room') return '';
    const night = name === 'night';
    const parts = Array.from({ length: night ? 16 : 18 }, (_, k) => `<i class="pt ${night ? 'ff' : ''}" style="left:${(k * 61) % 540}px;top:${200 + (k * 97) % 640}px;animation-delay:-${(k * .71) % 6}s;--px:${(k % 2 ? 1 : -1) * (20 + k % 4 * 12)}px"></i>`).join('');
    const bushes = PAL[name] ? `<div class="lay l-front"><div class="fb" style="left:-90px">${P.bush({ c: night ? '#1d4a2f' : '#2f8a3e', flowers: !night })}</div><div class="fb" style="left:430px">${P.bush({ c: night ? '#1d4a2f' : '#2f8a3e' })}</div></div>` : '';
    return `${bushes}${night ? '' : '<div class="rays"></div>'}<div class="parts">${parts}</div><div class="vig"></div>`;
  }
  window.KIDS_ART = { P, background, front };
})();
