# API Hevy-Web

Préfixe : `/api`. Toutes les routes (sauf auth register/login) nécessitent une session active (cookie).

Les erreurs renvoient `{ "error": "<code>", "message": "..." }` avec un code HTTP approprié (400/401/404/409).

---

## Auth

### `POST /api/auth/register`
```json
// body
{ "email": "x@y.com", "password": "secret" }
// 201
{ "user": { "id": 1, "email": "x@y.com", ... } }
```

### `POST /api/auth/login`
```json
// body
{ "email": "x@y.com", "password": "secret", "remember": true }
// 200
{ "user": { "id": 1, "email": "x@y.com", "unit_system": "metric", ... } }
```

### `POST /api/auth/logout`
`{ "ok": true }`

### `GET /api/auth/me`
`{ "user": { ... } }` ou 401 si non connecté.

---

## Settings

### `GET /api/settings`
```json
{
  "settings": {
    "unit_system": "metric",
    "rest_timer_default": 90,
    "sound_enabled": true,
    "vibration_enabled": true
  }
}
```

### `PUT /api/settings`
Body : n'importe quel sous-ensemble de `settings`. Retourne settings mis à jour.

---

## Exercises

### `GET /api/exercises?muscle_group=chest&equipment=barbell&search=bench`
```json
{
  "exercises": [
    {
      "id": 1,
      "name": "Barbell Bench Press",
      "muscleGroup": "chest",
      "equipment": "barbell",
      "exerciseType": "weight",
      "isCustom": false,
      ...
    }
  ]
}
```

### `POST /api/exercises`
```json
// body — crée exercice custom du user courant
{
  "name": "Kettlebell Halo",
  "muscle_group": "shoulders",
  "equipment": "kettlebell",
  "exercise_type": "reps"
}
// 201 { "exercise": { ... "isCustom": true } }
```

### `GET /api/exercises/<id>`
Détail de l'exercice.

### `GET /api/exercises/<id>/history?limit=20`
```json
{
  "history": [
    {
      "workout_id": 42,
      "date": 1712345678000,  // timestamp ms
      "sets": [ { "reps": 10, "weight": 100, "rpe": 8, "type": "normal", "is_pr": false } ]
    }
  ]
}
```

### `GET /api/exercises/<id>/prs`
```json
{
  "prs": {
    "weight": { "value": 140, "unit": "kg", "reps": 3, "weight": 140, "achieved_at": "..." },
    "e1rm": { "value": 154.3, ... },
    "volume": { "value": 1200, ... },
    "reps": { "value": 15, ... }
  }
}
```

### `GET /api/exercises/<id>/stats`
```json
{
  "series": [
    { "date": "2026-03-01", "max_e1rm": 133.3, "volume": 2400, "max_weight": 100 }
  ]
}
```

---

## Folders & Routines

### `GET /api/folders` · `POST /api/folders` · `PATCH /api/folders/<id>` · `DELETE /api/folders/<id>`

### `GET /api/routines`
```json
{
  "routines": [
    {
      "id": 1, "title": "Push Day", "name": "Push Day",
      "folder_id": null, "total_sets": 12,
      "exercises": [
        {
          "id": 5, "exerciseId": 42, "name": "Bench Press", "muscleGroup": "chest",
          "order_index": 0, "rest_seconds": 90,
          "sets": [ { "target_reps": 10, "target_weight": 80, "set_type": "normal" } ]
        }
      ]
    }
  ]
}
```

### `POST /api/routines`
```json
// body
{
  "name": "Push Day",
  "folder_id": null,
  "exercises": [
    {
      "exercise_id": 42,
      "rest_seconds": 90,
      "sets": [
        { "target_reps": 10, "target_weight": 80, "set_type": "normal" },
        { "target_reps": 8, "target_weight": 85 }
      ]
    }
  ]
}
```

### `GET /api/routines/<id>` · `PATCH /api/routines/<id>` · `DELETE /api/routines/<id>`
Patch remplace entièrement la structure `exercises` si fournie.

### `POST /api/routines/<id>/duplicate`
Duplique la routine. Retourne la copie.

### `POST /api/routines/<id>/start`
Crée un workout avec les exercices/sets pré-remplis depuis la routine. Renvoie le workout.

---

## Workouts

### `GET /api/workouts?page=1&per_page=20&from=2026-01-01&to=2026-04-19&finished_only=1`
```json
{
  "items": [
    {
      "id": 1, "title": "Leg Day",
      "start_time": 1712345000000, "end_time": 1712348600000,
      "durationSeconds": 3600, "totalVolume": 4500, "totalSets": 18, "totalReps": 180,
      "pr_count": 2,
      "date_relative": "Hier",
      "exerciseHistory": [
        {
          "exerciseId": 42, "name": "Squat", "muscleGroup": "quadriceps",
          "sets": [ { "reps": 10, "weight": 100, "rpe": 8, "completed": true, "type": "normal", "is_pr": false } ]
        }
      ]
    }
  ],
  "total": 47,
  "page": 1, "per_page": 20, "has_more": true,
  "stats": {
    "workouts_count": 47,
    "total_volume_display": "142,3t",
    "total_duration_display": "38h 24m"
  }
}
```

### `POST /api/workouts`
Crée un workout (vide ou pré-rempli) :
```json
{
  "name": "Quick Session",
  "notes": "Felt strong today",
  "exercises": [
    { "exercise_id": 42, "sets": [ { "reps": 10, "weight": 100, "completed": true } ] }
  ]
}
```

### `GET /api/workouts/active`
Retourne le workout en cours (ended_at null) ou `{ "workout": null }`.

### `GET /api/workouts/<id>` · `PATCH /api/workouts/<id>` · `DELETE /api/workouts/<id>`

### `POST /api/workouts/<id>/exercises`
Ajoute un exercice en live. Body : `{ "exercise_id": 42, "notes": "..." }`.

### `POST /api/workouts/<id>/sets`
Ajoute un set à un exercice :
```json
{
  "workout_exercise_id": 3,
  "reps": 10, "weight": 100, "rpe": 8,
  "set_type": "normal",
  "completed": true
}
```

### `PATCH /api/sets/<id>`
Met à jour un set. Fields : reps, weight, rpe, set_type, completed, notes, order_index.

### `DELETE /api/sets/<id>`

### `POST /api/workouts/<id>/finish`
Termine le workout, calcule la durée, détecte les PRs :
```json
{
  "workout": { ... "is_finished": true, "duration_seconds": 3600 },
  "new_prs": [ { "pr_type": "weight", "value": 140, ... } ]
}
```

---

## Stats

### `GET /api/stats` (= `/api/stats/overview`)
```json
{
  "total_workouts": 47, "workouts_count": 47,
  "total_volume": 142345.5, "total_volume_display": "142,3t",
  "total_duration_display": "38h 24m",
  "total_sets": 850, "total_reps": 9200,
  "prs_count": 23, "streak": 5
}
```

### `GET /api/stats/calendar?month=2026-04`
```json
{
  "month": "2026-04",
  "days": [
    { "date": "2026-04-18", "count": 1, "volume": 4500, "duration_seconds": 3600 }
  ]
}
```

### `GET /api/prs/recent?limit=5`
```json
{
  "items": [
    {
      "id": 12, "exercise_name": "Squat", "pr_type": "weight",
      "value": 140, "reps": 3, "weight": 140, "unit": "kg",
      "date": 1712345678000
    }
  ]
}
```

---

## Export / Import

### `GET /api/export`
Dump JSON complet des données utilisateur (user, routines, workouts, exercices custom).

### `POST /api/import`
Body : même structure que l'export. Ajoute les données sans remplacer.

---

## Conventions

- **IDs** : entiers auto-incréments (pas d'UUID)
- **Dates** : ISO 8601 (`created_at`) ou timestamp ms (`start_time`, `end_time`, `date`) selon champ
- **Poids** : toujours stocké/retourné en kg côté DB (l'UI convertit selon `unit_system`)
- **Ownership** : tous les endpoints filtrent par `user_id = current_user.id` ; accès à un objet d'un autre user = 404
- **Set types** : `normal` | `warmup` | `drop` | `failure`
- **PR types** : `weight` | `reps` | `volume` | `e1rm`
- **e1RM formule** : Epley (`weight × (1 + reps / 30)`), Brzycki et Lander disponibles dans `calculations.py`
