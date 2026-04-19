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
  tick() { this.vibrate(20); }
};

// HTMX headers
document.addEventListener('htmx:configRequest', (evt) => {
  evt.detail.headers['Accept'] = 'application/json';
});

// Init : icônes Lucide
document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) window.lucide.createIcons();
});

document.addEventListener('htmx:afterSettle', () => {
  if (window.lucide) window.lucide.createIcons();
});
