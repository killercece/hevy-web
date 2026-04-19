/**
 * Charts - Chart.js wrapper pour les pages de détail exercice
 * Thème dark Hevy
 */

window.HevyCharts = {
  _defaults() {
    if (!window.Chart) return;
    Chart.defaults.color = '#AAAAAA';
    Chart.defaults.borderColor = '#2A2A2A';
    Chart.defaults.font.family = 'Inter, system-ui, sans-serif';
  },

  _gradient(ctx) {
    const g = ctx.createLinearGradient(0, 0, 0, 240);
    g.addColorStop(0, 'rgba(38, 127, 232, 0.4)');
    g.addColorStop(1, 'rgba(38, 127, 232, 0)');
    return g;
  },

  renderE1rm(canvasId, history) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !window.Chart) return;
    this._defaults();

    const labels = history.map(s => new Date(s.date).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' }));
    const data = history.map(s => {
      const best = (s.sets || []).reduce((max, set) => {
        if (!set.weight || !set.reps) return max;
        const e1rm = set.weight * (1 + set.reps / 30);
        return Math.max(max, e1rm);
      }, 0);
      return Math.round(best * 10) / 10;
    });

    new Chart(canvas, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'e1RM',
          data,
          borderColor: '#267fe8',
          backgroundColor: this._gradient(canvas.getContext('2d')),
          fill: true,
          tension: 0.3,
          pointBackgroundColor: '#267fe8',
          pointRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: false, grid: { color: '#1F1F1F' } },
          x: { grid: { display: false } }
        }
      }
    });
  },

  renderVolume(canvasId, history) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !window.Chart) return;
    this._defaults();

    const labels = history.map(s => new Date(s.date).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' }));
    const data = history.map(s =>
      (s.sets || []).reduce((sum, set) => sum + (set.weight || 0) * (set.reps || 0), 0)
    );

    new Chart(canvas, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Volume',
          data,
          backgroundColor: '#267fe8',
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: '#1F1F1F' } },
          x: { grid: { display: false } }
        }
      }
    });
  },

  renderCalendar(containerId, days) {
    // Simple heatmap CSS — géré en CSS dans profile
    // Placeholder si chart custom demandé
  }
};
