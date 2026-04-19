/**
 * Workout actif - Alpine component
 * - Timer session total (updates chaque seconde)
 * - Saisie sets (reps/weight)
 * - Validation set -> rest timer
 * - Persistance localStorage
 * - Finish -> POST /api/workouts
 */

document.addEventListener('alpine:init', () => {
  Alpine.data('activeWorkout', (initial = {}) => ({
    data: {
      id: initial.id || null,
      title: initial.title || '',
      start_time: initial.start_time || Date.now(),
      end_time: null,
      routineId: initial.routineId || null,
      exercises: initial.exercises || [],
      notes: ''
    },

    // UI state
    unit: 'kg',
    openPicker: false,
    pickerQuery: '',
    pickerMuscle: null,
    exerciseLibrary: [],
    muscleGroups: ['chest', 'back', 'legs', 'shoulders', 'arms', 'core', 'cardio'],

    // Timer session
    elapsed: 0,
    elapsedDisplay: '00:00',
    tickInterval: null,

    // Rest timer
    restActive: false,
    restRemaining: 0,
    restDisplay: '00:00',
    restInterval: null,
    restDefault: 90,

    start() {
      // Restaurer session localStorage si présente
      const saved = Hevy.storage.loadSession();
      if (saved && saved.id === this.data.id && !initial.exercises?.length) {
        this.data = saved;
      }

      // Charger unité + repos default depuis settings
      fetch('/api/settings').then(r => r.json()).then(d => {
        const s = d.settings || d;
        this.unit = (s.unit_system === 'imperial') ? 'lbs' : 'kg';
        this.restDefault = s.rest_timer_default || 90;
      }).catch(() => {});

      // Charger bibliothèque
      fetch('/api/exercises').then(r => r.json()).then(d => {
        this.exerciseLibrary = d.items || d.exercises || d;
        // Extract unique muscle groups
        const mgs = [...new Set(this.exerciseLibrary.map(e => e.muscleGroup).filter(Boolean))];
        if (mgs.length) this.muscleGroups = mgs;
      }).catch(() => {});

      // Tick session timer
      this.tick();
      this.tickInterval = setInterval(() => this.tick(), 1000);

      // Autosave
      setInterval(() => this.persist(), 5000);

      this.$nextTick(() => window.lucide?.createIcons());
    },

    tick() {
      this.elapsed = Math.floor((Date.now() - this.data.start_time) / 1000);
      this.elapsedDisplay = Hevy.format.duration(this.elapsed);
    },

    get totalVolume() {
      let v = 0;
      for (const ex of this.data.exercises) {
        for (const s of (ex.sets || [])) {
          if (s.completed && s.weight && s.reps) v += s.weight * s.reps;
        }
      }
      return v;
    },

    get totalVolumeDisplay() {
      return Hevy.format.volume(this.totalVolume, this.unit);
    },

    get completedSets() {
      let n = 0;
      for (const ex of this.data.exercises) {
        for (const s of (ex.sets || [])) {
          if (s.completed) n++;
        }
      }
      return n;
    },

    get filteredExercises() {
      const q = this.pickerQuery.toLowerCase().trim();
      return this.exerciseLibrary.filter(e => {
        if (this.pickerMuscle && e.muscleGroup !== this.pickerMuscle) return false;
        if (q && !e.name.toLowerCase().includes(q)) return false;
        return true;
      });
    },

    addExercise(ex) {
      this.data.exercises.push({
        exerciseId: ex.id,
        name: ex.name,
        muscleGroup: ex.muscleGroup,
        equipment: ex.equipment,
        notes: '',
        sets: [{ type: 'normal', weight: null, reps: null, completed: false, previous: null }]
      });
      this.loadPreviousForLast();
      this.persist();
      this.$nextTick(() => window.lucide?.createIcons());
    },

    loadPreviousForLast() {
      const ex = this.data.exercises[this.data.exercises.length - 1];
      if (!ex || !ex.exerciseId) return;
      fetch(`/api/exercises/${ex.exerciseId}/history?limit=1`)
        .then(r => r.json())
        .then(d => {
          const hist = d.history || [];
          if (!hist.length) return;
          const sets = hist[0].sets || [];
          ex.sets.forEach((s, i) => {
            const prev = sets[i];
            if (prev) s.previous = `${prev.weight || 0} × ${prev.reps || 0}`;
          });
        })
        .catch(() => {});
    },

    removeExercise(i) {
      if (!confirm('Retirer cet exercice ?')) return;
      this.data.exercises.splice(i, 1);
      this.persist();
    },

    addSet(exIndex) {
      const ex = this.data.exercises[exIndex];
      const last = ex.sets[ex.sets.length - 1] || {};
      ex.sets.push({
        type: 'normal',
        weight: last.weight || null,
        reps: last.reps || null,
        completed: false,
        previous: null
      });
      this.persist();
      this.$nextTick(() => window.lucide?.createIcons());
    },

    cycleSetType(exIndex, sIndex) {
      const types = ['normal', 'warmup', 'drop', 'failure'];
      const s = this.data.exercises[exIndex].sets[sIndex];
      const current = types.indexOf(s.type || 'normal');
      s.type = types[(current + 1) % types.length];
      this.persist();
    },

    toggleSet(exIndex, sIndex) {
      const s = this.data.exercises[exIndex].sets[sIndex];
      if (!s.completed && (!s.weight || !s.reps)) {
        alert('Saisissez le poids et les reps avant de valider.');
        return;
      }
      s.completed = !s.completed;
      if (s.completed) {
        s.timestamp = Date.now();
        Hevy.haptics.success();
        this.startRest();
        // Focus suivant input
        this.$nextTick(() => {
          const next = this.data.exercises[exIndex].sets[sIndex + 1];
          if (next) {
            const el = document.querySelectorAll('.set-row input')[sIndex * 2 + 2];
            el?.focus();
          }
        });
      }
      this.persist();
    },

    startRest() {
      this.restRemaining = this.restDefault;
      this.restActive = true;
      this.restDisplay = Hevy.format.duration(this.restRemaining);
      clearInterval(this.restInterval);
      this.restInterval = setInterval(() => {
        this.restRemaining--;
        this.restDisplay = Hevy.format.duration(this.restRemaining);
        if (this.restRemaining <= 0) {
          this.finishRest();
        }
      }, 1000);
    },

    adjustRest(delta) {
      this.restRemaining = Math.max(5, this.restRemaining + delta);
      this.restDisplay = Hevy.format.duration(this.restRemaining);
    },

    stopRest() {
      clearInterval(this.restInterval);
      this.restActive = false;
    },

    finishRest() {
      clearInterval(this.restInterval);
      Hevy.haptics.success();
      try {
        const chime = document.getElementById('rest-chime');
        if (chime) chime.play().catch(() => {});
      } catch (e) {}
      setTimeout(() => { this.restActive = false; }, 800);
    },

    persist() {
      Hevy.storage.saveSession(this.data);
    },

    async cancel() {
      if (!confirm('Abandonner ce workout ? Les données saisies seront perdues.')) return;
      clearInterval(this.tickInterval);
      clearInterval(this.restInterval);
      Hevy.storage.clearSession();
      window.location = '/';
    },

    async finish() {
      if (this.completedSets === 0) {
        if (!confirm('Aucun set validé. Terminer quand même ?')) return;
      }
      clearInterval(this.tickInterval);
      clearInterval(this.restInterval);
      this.data.end_time = Date.now();
      this.data.durationSeconds = Math.floor((this.data.end_time - this.data.start_time) / 1000);
      this.data.totalVolume = this.totalVolume;
      this.data.totalSets = this.completedSets;
      this.data.totalReps = this.data.exercises.reduce((sum, ex) =>
        sum + (ex.sets || []).filter(s => s.completed).reduce((a, s) => a + (s.reps || 0), 0), 0);

      // Adapter payload au format backend (snake_case)
      const payload = {
        name: this.data.title || 'Workout',
        notes: this.data.notes || null,
        routine_id: this.data.routineId || null,
        exercises: this.data.exercises.map((ex, i) => ({
          exercise_id: ex.exerciseId,
          order_index: i,
          notes: ex.notes || null,
          sets: (ex.sets || []).map((s, j) => ({
            order_index: j,
            set_type: s.type || 'normal',
            reps: s.reps,
            weight: s.weight,
            rpe: s.rpe || null,
            completed: !!s.completed
          }))
        }))
      };
      try {
        const res = await fetch('/api/workouts', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error('Save failed');
        const d = await res.json();
        const w = d.workout || d;
        // Marquer comme terminé via finish endpoint
        if (w.id) {
          await fetch(`/api/workouts/${w.id}/finish`, { method: 'POST' });
        }
        Hevy.storage.clearSession();
        window.location = w.id ? `/workouts/${w.id}` : '/workouts';
      } catch (e) {
        alert('Erreur d\'enregistrement : ' + e.message);
      }
    }
  }));
});
