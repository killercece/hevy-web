/**
 * Bibliothèque d'exercices - recherche + filtres
 */

document.addEventListener('alpine:init', () => {
  Alpine.data('exerciseLibrary', () => ({
    items: [],
    query: '',
    muscleFilter: null,
    equipmentFilter: null,
    loading: true,

    async load() {
      try {
        const r = await fetch('/api/exercises');
        const d = await r.json();
        this.items = d.items || d.exercises || d;
      } catch (e) {
        this.items = [];
      }
      this.loading = false;
      this.$nextTick(() => window.lucide?.createIcons());
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
