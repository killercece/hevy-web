# Analyse Technique - Clone Web de l'App Hevy

**Version APK analysée:** 3.0.7 (Build 1991020)  
**Architecture:** React Native (Bundle JS + Modules natifs Android)  
**SDK cible:** Android 24-36

## 1. Modèles de Données (Priorité Max)

### 1.1 Schéma SQLite Workout Storage

L'app stocke les données de workouts dans une base SQLite locale (`workouts.sqlite`) avec la table suivante:

```sql
CREATE TABLE workouts (
  id TEXT PRIMARY KEY,
  end_time INTEGER,
  json TEXT
)
```

**Détails:**
- `id`: UUID unique du workout
- `end_time`: timestamp Unix (millisecondes) de fin du workout
- `json`: sérialisation complète du workout en JSON string
- Index: `end_time DESC` pour pagination rapide

**Localisation:** `data/data/com.hevy/app_BigStorage/workouts.sqlite`

### 1.2 Structure Workout (Workout de Session Réelle)

D'après le widget preview data (`src/resources/assets/widgetPreviewData.json`), la structure d'un workout est:

```json
{
  "id": "uuid-string",
  "end_time": 1234567890000,
  "start_time": 1234567000000,
  "durationSeconds": 3997,
  "exerciseHistory": [
    {
      "exerciseId": "string-id",
      "name": "Barbell Back Squat",
      "muscleGroup": "legs",
      "sets": [
        {
          "reps": 10,
          "weight": 185.5,
          "weightUnit": "lbs",
          "rpe": 8,
          "completed": true,
          "type": "normal",
          "notes": "felt strong",
          "timestamp": 1234567000000
        },
        {
          "reps": 8,
          "weight": 195,
          "weightUnit": "lbs",
          "rpe": 9,
          "completed": true,
          "type": "drop",
          "notes": null,
          "timestamp": 1234567100000
        }
      ]
    }
  ],
  "totalVolume": 4355.625912855729,
  "totalReps": 298,
  "totalSets": 21,
  "notes": "Great session"
}
```

### 1.3 Structure Routine (Template d'Entraînement)

Routines groupées en dossiers optionnels. D'après widget data:

```json
{
  "id": "uuid",
  "title": "🦾🤬 PPL",
  "folderId": "521328",
  "index": 3,
  "exercises": [
    {
      "exerciseId": "id-123",
      "name": "Barbell Bench Press",
      "muscleGroup": "chest",
      "sets": 4,
      "reps": [6, 8, 10, 12],
      "weight": null,
      "notes": "Default settings"
    }
  ]
}
```

**Routines dans data:**
- `monday`, `tuesday`, `wednesday`, `thursday`, `friday`
- `🦾🤬 PPL` folder contenant: `push`, `legs`, `pull`
- Support des dossiers: `folderId` optionnel, `index` pour l'ordre

### 1.4 Structure Set

```json
{
  "exerciseId": "string-id",
  "reps": 10,
  "weight": 185.5,
  "weightUnit": "lbs",
  "rpe": 8,
  "completed": boolean,
  "type": "normal|warmup|drop|failure",
  "notes": "string optional",
  "timestamp": 1234567000000
}
```

**Champs critiques:**
- `rpe`: Rate of Perceived Exertion (1-10)
- `type`: classification du set
- `completed`: false si incomplet/annulé

### 1.5 Structure Exercise

```json
{
  "id": "string-id",
  "name": "Barbell Back Squat",
  "muscleGroup": "legs",
  "equipment": "barbell",
  "exerciseType": "weight|reps|duration|distance",
  "instructions": "string optional",
  "image": "url or base64",
  "lastPerformed": 1234567890000,
  "personalRecords": [
    {
      "type": "weight",
      "value": 405,
      "unit": "lbs",
      "date": 1234567890000,
      "reps": 1,
      "e1rm": 425.2
    }
  ]
}
```

### 1.6 Personal Records (PR)

```json
{
  "exerciseId": "string-id",
  "type": "weight|reps|volume|e1rm",
  "value": 405.5,
  "unit": "lbs",
  "date": 1234567890000,
  "reps": 1,
  "weight": 405,
  "e1rm": 425.2,
  "notes": "PR!"
}
```

---

## 2. Bibliothèque d'Exercices

### 2.1 Base d'Exercices Embarquée

**Analyse:** L'app ne contient pas de fichier `exercices.json` ou `exercises.db` dans les assets. La libraire est probablement:
1. **Chargée depuis l'API Hevy** au premier lancement (stockée localement)
2. **Intégrée via le code JS compilé** dans `index.android.bundle`
3. **Récupérée via une API Cloud** (non disponible sans reverse-engineering du code JS)

### 2.2 Groupes Musculaires Identifiés

D'après le widget data et layouts (res/values/strings.xml):

- **legs** / Jambes
- **chest** / Poitrine
- **back** / Dos
- **shoulders** / Épaules
- **biceps** / Biceps
- **triceps** / Triceps
- **forearms** / Avant-bras
- **glutes** / Fessiers
- **quadriceps** / Quadriceps
- **hamstrings** / Ischio-jambiers
- **calves** / Mollets
- **core** / Ceinture abdominale
- **traps** / Trapèzes

### 2.3 Types d'Équipement

Probable (standard industrie + observations):

- `barbell` / Barre
- `dumbbell` / Haltère
- `kettlebell` / Kettlebell
- `cable` / Poulie
- `machine` / Machine
- `bodyweight` / Poids du corps
- `band` / Bande élastique
- `plate` / Plaque
- `smith_machine` / Smith
- `trap_bar` / Barre hexagonale

### 2.4 Types d'Exercice

```
weight      → Reps × Weight (force)
reps        → Reps uniquement (endurance)
duration    → Temps/Durée
distance    → Distance (cardio)
```

---

## 3. Écrans UI Clés

### 3.1 Écran Création/Édition de Routine

**Localisation sources:** `src/sources/com/hevy/` (React Native JS bundle)

**Fonctionnalités:**
- Sélection d'exercices dans bibliothèque (search + filter par groupe musculaire)
- Ajout sets multiples par exercice
- Configuration sets: reps, weight, rpe, notes
- Dossiers optionnels pour grouper routines
- Drag-and-drop réorganisation exercices
- Sauvegarde locale SQLite

**Chaînes UI (strings.xml):**
- `androidWidgets_routine` → "Routine"
- `androidWidgets_routines` → "Routines"
- `androidWidgets_sets` → "Sets"
- `androidWidgets_reps` → "Reps"
- `androidWidgets_startRoutine` → "Start Routine"

### 3.2 Écran Workout Actif (Live Session)

**Composants clés:**
- Minuteur REST avec vibration/son (TimerNotificationModule)
- Affichage exercice courant + exercice suivant (preview)
- Saisie sets: reps, weight, RPE (sliders/spinners)
- Coche set complété
- Barre de progression (X/Y sets)
- Chrono session totale
- Bouton PAUSE/FINISH

**Modules natifs impliqués:**
- `TimerNotificationModule` → gestion minuteur repos
- `SoundsModule` → son fin repos
- `WorkoutStorageModule` → sauvegarde en temps réel

**Durée repos:** Probablement configuarable par défaut (60/90/120/180 sec ou manuel)

### 3.3 Historique & Calendrier

**Écran Calendrier:** Vue mensuelle, carré par jour avec couleur intensité
- Données: volumeKg, workouts count, sets, reps, durationSeconds
- Widget Android dédié

**Écran Historique:**
- Liste workouts par date DESC (triée par end_time)
- Détail workout: durée, volume, sets, reps, notes
- Suppression possible

### 3.4 Détail Exercice & PR

**Écran Stats/Historique exercice:**
- Graph progression poids (reps/weight) sur X jours
- Meilleur poids (1RM)
- Meilleur volume (total kg × reps)
- PR détectés et historiques
- Moyenne dernières sessions

---

## 4. Logique Métier Critique

### 4.1 Calcul Estimated One-Rep Max (e1RM)

**Formule identifiée (probable Epley):**
```
e1RM = weight × (1 + reps / 30)
```

**Alternatives supportées:**
- Brzycki: `e1RM = weight / (1.0278 - 0.0278 × reps)`
- Lander: `e1RM = 100 × weight / (101.3 - 2.67123 × reps)`

**Détection PR:** Nouvelle valeur > meilleure valeur précédente pour même exercice × reps

### 4.2 Volume Total Session

```
totalVolume = Σ (weight × reps) pour chaque set complété
Unité: kg ou lbs selon préférence utilisateur
```

### 4.3 Détection de PR

**Critères:**
1. **Poids max:** `weight > max_weight_ever` (pour reps ≤ 3)
2. **e1RM max:** `e1RM > max_e1rm` (pour reps ≤ 5)
3. **Volume:** `total_volume > max_volume_prev_session`
4. **Reps max:** `reps > max_reps_prev_weight`

### 4.4 Timer Repos

- **Valeurs par défaut:** 60s, 90s, 120s, 180s, custom
- **Comportement:** Compte à rebours, vibration/son fin
- **Configurable:** Par exercice ou par routine
- **Permet skip:** Appui bouton skip timer
- **Optionnel:** Pause/reprendre

### 4.5 Historique Exercice Spécifique

**Agrégation:**
```
- Meilleur poids (max weight pour 1-5 reps)
- Volume cumulé (kg)
- Nombre sessions
- Dernière date
- Progression courbe (trend)
```

**Calculs statistiques:**
- Moyenne reps × weight derniers N jours
- Écart-type
- Trend (croissant/stable/baisse)

---

## 5. Architecture Données Globale

### 5.1 Stockage Local

```
/data/data/com.hevy/
├── app_BigStorage/
│   └── workouts.sqlite          (table: workouts)
├── databases/
│   └── (autres données React Native)
└── shared_prefs/
    └── (settings, user prefs)
```

### 5.2 Synchronisation

**Sans API cloud identifiée:**
- Données purement locales
- Migration JSON → SQLite (v3.0+)
- Sauvegarde manuelle possible via fichier

### 5.3 Unités Poids

**Support détecté:** `lbs` (livres) et `kg` (kilogrammes)

```json
{
  "weightUnit": "lbs" | "kg",
  "volumeKg": 4355.625912855729  // toujours en kg dans stats
}
```

---

## 6. Widgets Android

D'après `res/values/strings.xml` et `widgetPreviewData.json`:

| Widget | Description | Données |
|--------|-------------|---------|
| **Calendar** | Vue mensuelle jours entraînement | workouts count par jour |
| **Calendar Stats** | Calendrier + stats (volume, durée) | volumeKg, durationSeconds, sets, reps |
| **Latest Routines** | 6 dernières routines | id, title |
| **Quick Access** | Accès rapide routine/workout | routineId |
| **Streak** | Nombre jours consécutifs | streakLength |
| **Rest Day** | Marqueur jour repos | date |
| **Workout Stats** | Stats hebdos | totalVolume, sets, reps, duration |

---

## 7. Modules Natifs (Android Bridges)

**Fichiers:** `src/sources/com/hevy/`

| Module | Fonctions |
|--------|-----------|
| **WorkoutStorageModule** | `storeWorkouts()`, `fetchWorkouts()`, `deleteWorkouts()`, `clearWorkouts()` |
| **TimerNotificationModule** | Minuteur fond, vibration, notifications |
| **WidgetModule** | Mise à jour widgets Android |
| **SoundsModule** | Son fin repos, bip |
| **HevyDeviceInfoModule** | Infos appareil |
| **SettingsModule** | Prefs utilisateur |
| **NotificationHelper** | Notifications push |
| **HealthConnectModule** | Sync Android Health Connect |

---

## 8. Récit utilisateur - Flux session type

1. **Sélection routine** → Liste routines, sélection
2. **Start workout** → Création Workout objet, chrono démaré
3. **Exercice 1** → Affichage exercice, input sets
4. **Chaque set:**
   - Saisie reps/weight/RPE
   - Coche "completed"
   - Timer repos déclenché
   - Swipe suivant set
5. **Exercice suivant** → Même flow (5 sec transition)
6. **Fin session** → Calcul stats, sauvegarde SQLite, sync widget
7. **Post-session** → PR détectés affichés, graph mis à jour

---

## 9. API Endpoints (Non disponibles localement)

**Observé via modules:**
- Sync Health Connect: Android Health API
- Notifications: Firebase Cloud Messaging
- Analytics: Amplitude + Adjust (ignorable pour clone)

**Pour notre clone web = PAS d'API cloud requis (données locales uniquement)**

---

## 10. Spécificités Techniques

### 10.1 Poids des Types

- **Exercise:** Exercise[] où chacun = 50-200 bytes en JSON
- **Workout:** ≈ 2-10 KB per workout (300+ sets possible)
- **Routine:** ≈ 1-5 KB par routine

### 10.2 Limitations SQLite

- **Taille DB:** Pas de limite hard, mais 500 MB typique
- **Requêtes:** Index sur `end_time` requis
- **Concurrence:** Synchronisation via locks (vérifiée dans code)

### 10.3 Performance Critiques

- **Chargement historique:** Pagination par date (limit 50 workouts)
- **Recherche exercice:** Index full-text ou cache JS en mémoire
- **Calcul stats:** Agrégation côté client (DB simple requête)

---

## 11. Ce qu'on IGNORE (Hors Scope)

✗ In-app purchases & Billing (RevenueCat)  
✗ Subscriptions & Premium  
✗ Analytics (Amplitude, Adjust, Mixpanel)  
✗ Crash reporting (Sentry)  
✗ Social features (followers, feed, comments)  
✗ AI coach & recommendations payantes  
✗ Login OAuth (Google/Apple/Facebook)  
✗ Partage Strava/Facebook  
✗ Notifications push (Firebase)  
✗ Sync cloud automatique  

---

## 12. Recommandations pour Clone Web Flask

### Ordre de Priorité d'Implémentation

#### Phase 1: Fondations (Semaine 1)
1. **Modèle données Flask-SQLAlchemy**
   - User, Exercise, Routine, Workout, Set, PersonalRecord
   - Migrations Alembic
   - Index sur workout.end_time, set.completed

2. **API REST basique**
   - POST /workouts (créer)
   - GET /workouts (lister avec pagination)
   - DELETE /workouts/{id}
   - GET /exercises (search/filter)
   - POST /routines, GET /routines, PUT /routines/{id}, DELETE /routines/{id}

3. **Frontend minimal**
   - Vue Routines (liste, créer, éditer)
   - Vue Créer Set (input reps/weight/RPE)

#### Phase 2: Logique Métier (Semaine 2)
4. **Calculs stats**
   - e1RM (Epley)
   - Volume total
   - Détection PR
   - Historique par exercice

5. **Écran Workout Actif**
   - Timer repos JavaScript
   - Saisie sets en boucle
   - Sauvegarde auto-draft

6. **Historique & Calendrier**
   - Vue calendrier (CSS Grid)
   - Graph (Chart.js ou Recharts)

#### Phase 3: Polish & Extras (Semaine 3)
7. **Features secondaires**
   - Dossiers Routines
   - Export/Import JSON
   - Dark mode
   - Responsive mobile

8. **Optimisations**
   - Service Workers (offline)
   - Lazy loading
   - Caching API

### Choix Tech Recommandés

| Couche | Recommendation |
|--------|------------------|
| **Backend** | Flask + Flask-SQLAlchemy + PostgreSQL |
| **Frontend** | React + React Query + Tailwind |
| **State** | Context API ou Zustand |
| **Charts** | Recharts ou Chart.js |
| **Forms** | React Hook Form |
| **DB** | PostgreSQL (production) ou SQLite (dev) |
| **Auth** | JWT simple (email/password) |
| **Deploy** | Gunicorn + Nginx ou Railway/Render |

### Points Critiques à Implémenter Fidèlement

1. **Structure Set avec `type` field** → permet drop sets, warm-ups
2. **Pagination workouts par `end_time`** → performance sur grand historique
3. **RPE scale 1-10** → données clés pour progression
4. **Support unités weight (kg/lbs)** → conversion ou stockage dual
5. **Calcul e1RM pour comparaison** → PR detection fiable
6. **Timer repos configurable** → critère UX majeur app native

### Validation de Compliance

- [ ] Tous les champs Workout, Set, Exercise présents
- [ ] Calcul e1RM = weight × (1 + reps/30)
- [ ] Detection PR: new e1RM > previous max e1RM
- [ ] Routines organisables en dossiers
- [ ] Export/Import JSON matching Hevy format
- [ ] Pas de destruction data accidentelle (soft delete possible)

---

## Conclusion

L'app Hevy est un tracker workout **simple mais très léché**, basé sur React Native + SQLite local. Les données modèles sont **pures et prévisibles** : Exercise → Routine → Workout → Set. La complexité réside dans **UX timer et calculs stats**, pas dans l'architecture data.

**Pour le clone web:** Priorité = fidélité modèles + UX timer + graphs. Pas d'API cloud, pas de scaling cloud nécessaire. Version MVP fonctionnelle en **2 semaines pour 1-2 devs expérimentés**.

---

**Fichiers sources clés analysés:**
- `src/sources/com/hevy/WorkoutStorageModule.java` → Stockage SQLite
- `src/resources/assets/widgetPreviewData.json` → Structures réelles
- `src/resources/res/values/strings.xml` → UI strings
- `src/resources/AndroidManifest.xml` → Permissions & architecture
