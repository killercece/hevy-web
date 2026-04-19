/**
 * Bibliothèque d'exercices - recherche + filtres + lazy videos.
 */

document.addEventListener('alpine:init', () => {
  Alpine.data('exerciseLibrary', () => ({
    items: [],
    query: '',
    muscleFilter: null,
    equipmentFilter: null,
    viewMode: localStorage.getItem('hevy.exlib.view') || 'grid',
    loading: true,

    init() {
      // Persiste le choix de vue
      this.$watch('viewMode', (v) => {
        try { localStorage.setItem('hevy.exlib.view', v); } catch (e) {}
        this._rescan();
      });
      this.$watch('muscleFilter', () => this._rescan());
      this.$watch('equipmentFilter', () => this._rescan());
      this.$watch('query', () => this._rescan());
    },

    async load() {
      try {
        const r = await fetch('/api/exercises');
        const d = await r.json();
        this.items = d.items || d.exercises || d;
      } catch (e) {
        this.items = [];
      }
      this.loading = false;
      this.$nextTick(() => {
        if (window.lucide) window.lucide.createIcons();
        this._rescan();
      });
    },

    _rescan() {
      this.$nextTick(() => {
        if (window.Hevy?.video) window.Hevy.video.scan(document);
      });
    },

    get muscleGroups() {
      return [...new Set(this.items.map(e => e.muscleGroup).filter(Boolean))].sort();
    },

    get equipments() {
      return [...new Set(this.items.map(e => e.equipment).filter(Boolean))].sort();
    },

    get filtered() {
      const q = this.query.toLowerCase().trim();
      return this.items.filter(e => {
        if (this.muscleFilter && e.muscleGroup !== this.muscleFilter) return false;
        if (this.equipmentFilter && e.equipment !== this.equipmentFilter) return false;
        if (q && !(e.name || '').toLowerCase().includes(q)) return false;
        return true;
      });
    }
  }));
});
