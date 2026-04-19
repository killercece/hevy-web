/**
 * App global - init, auth helpers, fetch wrapper
 */

window.Hevy = window.Hevy || {};

Hevy.api = {
  async get(url) {
    const r = await fetch(url, { credentials: 'same-origin' });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  },

  async post(url, body) {
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify(body)
    });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  },

  async put(url, body) {
    const r = await fetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify(body)
    });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  },

  async delete(url) {
    const r = await fetch(url, {
      method: 'DELETE',
      credentials: 'same-origin'
    });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json().catch(() => ({}));
  }
};

Hevy.format = {
  duration(seconds) {
    if (!seconds && seconds !== 0) return '—';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  },

  volume(v, unit = 'kg') {
    if (!v) return `0 ${unit}`;
    if (v >= 1000 && unit === 'kg') return (v / 1000).toFixed(1) + ' t';
    return Math.round(v) + ' ' + unit;
  },

  dateRelative(ts) {
    if (!ts) return '';
    const now = Date.now();
    const diff = now - ts;
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    if (days > 7) return new Date(ts).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
    if (days >= 1) return `il y a ${days}j`;
    if (hours >= 1) return `il y a ${hours}h`;
    if (minutes >= 1) return `il y a ${minutes}min`;
    return 'à l\'instant';
  }
};

Hevy.storage = {
  KEY: 'hevy.active_workout',

  saveSession(data) {
    try {
      localStorage.setItem(this.KEY, JSON.stringify(data));
    } catch (e) {}
  },

  loadSession() {
    try {
      const raw = localStorage.getItem(this.KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  },

  clearSession() {
    try {
      localStorage.removeItem(this.KEY);
    } catch (e) {}
  }
};

Hevy.haptics = {
  vibrate(pattern = 40) {
    if (navigator.vibrate) {
      try { navigator.vibrate(pattern); } catch (e) {}
    }
  },

  success() { this.vibrate([30, 30, 30]); },
  tick() { this.vibrate(20); },
  long() { this.vibrate([120, 60, 120]); }
};

/* --------------------------------------------------------------
 * Lazy Video Loader
 *
 * Scanne la page pour les <video data-lazy-src="..."> et les charge
 * uniquement quand ils entrent dans le viewport via IntersectionObserver.
 * Permet d'afficher des centaines de vidéos sans les télécharger toutes.
 * -------------------------------------------------------------- */
Hevy.video = {
  _observer: null,

  _ensureObserver() {
    if (this._observer || !('IntersectionObserver' in window)) return this._observer;
    this._observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        const v = entry.target;
        if (entry.isIntersecting) {
          // Load + play
          const src = v.getAttribute('data-lazy-src');
          if (src && !v.src) {
            v.src = src;
            v.load();
          }
          const p = v.play();
          if (p && typeof p.catch === 'function') p.catch(() => {});
        } else if (!v.paused) {
          try { v.pause(); } catch (e) {}
        }
      }
    }, { rootMargin: '150px 0px', threshold: 0.1 });
    return this._observer;
  },

  scan(root = document) {
    const obs = this._ensureObserver();
    const videos = root.querySelectorAll('video[data-lazy-src]:not([data-lazy-bound])');
    videos.forEach(v => {
      v.setAttribute('data-lazy-bound', '1');
      v.muted = true;
      v.playsInline = true;
      v.loop = true;
      v.setAttribute('preload', 'none');
      if (obs) {
        obs.observe(v);
      } else {
        // Fallback: charge direct
        v.src = v.getAttribute('data-lazy-src');
      }
    });
  }
};

/* --------------------------------------------------------------
 * Sound (AudioContext beep)
 *
 * Génère un petit son de fin de timer sans fichier audio.
 * -------------------------------------------------------------- */
Hevy.sound = {
  _ctx: null,

  _ensureCtx() {
    if (this._ctx) return this._ctx;
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    try {
      this._ctx = new AC();
    } catch (e) { return null; }
    return this._ctx;
  },

  beep(frequency = 880, duration = 0.18, volume = 0.25) {
    const ctx = this._ensureCtx();
    if (!ctx) return;
    const now = ctx.currentTime;
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.value = frequency;
    gain.gain.value = volume;
    gain.gain.setValueAtTime(volume, now);
    gain.gain.exponentialRampToValueAtTime(0.001, now + duration);
    osc.connect(gain).connect(ctx.destination);
    osc.start(now);
    osc.stop(now + duration);
  },

  chime() {
    // Deux tonalités — plus agréable qu'un simple bip
    this.beep(880, 0.18, 0.22);
    setTimeout(() => this.beep(1175, 0.25, 0.22), 180);
  }
};

// HTMX headers
document.addEventListener('htmx:configRequest', (evt) => {
  evt.detail.headers['Accept'] = 'application/json';
});

// Init : icônes Lucide + lazy videos
function hevyInitAll(root) {
  if (window.lucide) window.lucide.createIcons({ nameAttr: 'data-lucide' });
  if (Hevy.video) Hevy.video.scan(root || document);
}

document.addEventListener('DOMContentLoaded', () => hevyInitAll());
document.addEventListener('htmx:afterSettle', (e) => hevyInitAll(e.target || document));

// Alpine peut remplacer le DOM : rebind après chaque mutation
if (window.MutationObserver) {
  const mo = new MutationObserver((muts) => {
    let needScan = false;
    for (const m of muts) {
      for (const n of m.addedNodes) {
        if (n.nodeType === 1 && (n.matches?.('video[data-lazy-src]') || n.querySelector?.('video[data-lazy-src]'))) {
          needScan = true; break;
        }
      }
      if (needScan) break;
    }
    if (needScan) hevyInitAll(document);
  });
  document.addEventListener('DOMContentLoaded', () => {
    mo.observe(document.body, { childList: true, subtree: true });
  });
}
