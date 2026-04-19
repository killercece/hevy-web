"""Seed de la bibliothèque d'exercices (avec vidéos CDN Hevy).

Combine :
- Une liste curated (~180 exercices classiques avec name/muscle/equipment) ;
- Un TSV (`app/data/hevy_exercises_cdn.tsv`) contenant les `cdn_id`, `name`,
  `muscle` des ~363 vidéos du CDN public Hevy.

Flux :
1. On parse le TSV.
2. Pour chaque entrée curated, on cherche la meilleure vidéo CDN matchante
   (nom normalisé + muscle compatible).
3. On ajoute les entrées TSV non-matchées pour étoffer la bibliothèque
   (≈ 300 exercices au final, la grande majorité avec vidéo).
4. `seed_exercises()` fait le seed complet (table vide).
5. `sync_cdn_videos()` met à jour les DB existantes (attache les vidéos
   manquantes, ajoute les nouveaux exercices — idempotent).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from ..models import Exercise

# --------------------------------------------------------------------------
# Chemin du TSV
# --------------------------------------------------------------------------

_TSV_PATH = Path(__file__).resolve().parent.parent / "data" / "hevy_exercises_cdn.tsv"


# --------------------------------------------------------------------------
# Bibliothèque curated (inspirée des classiques + base Hevy)
# --------------------------------------------------------------------------

EXERCISES: list[tuple[str, str, str, str]] = [
    # ---- CHEST / Poitrine ---------------------------------------------
    ("Barbell Bench Press", "chest", "barbell", "weight"),
    ("Incline Barbell Bench Press", "chest", "barbell", "weight"),
    ("Decline Barbell Bench Press", "chest", "barbell", "weight"),
    ("Dumbbell Bench Press", "chest", "dumbbell", "weight"),
    ("Incline Dumbbell Bench Press", "chest", "dumbbell", "weight"),
    ("Decline Dumbbell Bench Press", "chest", "dumbbell", "weight"),
    ("Dumbbell Fly", "chest", "dumbbell", "weight"),
    ("Incline Dumbbell Fly", "chest", "dumbbell", "weight"),
    ("Cable Crossover", "chest", "cable", "weight"),
    ("Cable Fly (Low to High)", "chest", "cable", "weight"),
    ("Cable Fly (High to Low)", "chest", "cable", "weight"),
    ("Pec Deck Machine", "chest", "machine", "weight"),
    ("Chest Press Machine", "chest", "machine", "weight"),
    ("Push-Up", "chest", "bodyweight", "reps"),
    ("Incline Push-Up", "chest", "bodyweight", "reps"),
    ("Decline Push-Up", "chest", "bodyweight", "reps"),
    ("Diamond Push-Up", "chest", "bodyweight", "reps"),
    ("Dips (Chest)", "chest", "bodyweight", "reps"),
    ("Smith Machine Bench Press", "chest", "smith_machine", "weight"),
    ("Landmine Press", "chest", "barbell", "weight"),

    # ---- BACK / Dos ----------------------------------------------------
    ("Deadlift", "back", "barbell", "weight"),
    ("Romanian Deadlift", "back", "barbell", "weight"),
    ("Sumo Deadlift", "back", "barbell", "weight"),
    ("Trap Bar Deadlift", "back", "trap_bar", "weight"),
    ("Barbell Row", "back", "barbell", "weight"),
    ("Pendlay Row", "back", "barbell", "weight"),
    ("T-Bar Row", "back", "barbell", "weight"),
    ("Dumbbell Row", "back", "dumbbell", "weight"),
    ("Chest-Supported Dumbbell Row", "back", "dumbbell", "weight"),
    ("Seated Cable Row", "back", "cable", "weight"),
    ("Wide-Grip Lat Pulldown", "back", "cable", "weight"),
    ("Close-Grip Lat Pulldown", "back", "cable", "weight"),
    ("Reverse-Grip Lat Pulldown", "back", "cable", "weight"),
    ("Pull-Up", "back", "bodyweight", "reps"),
    ("Chin-Up", "back", "bodyweight", "reps"),
    ("Neutral-Grip Pull-Up", "back", "bodyweight", "reps"),
    ("Inverted Row", "back", "bodyweight", "reps"),
    ("Straight-Arm Pulldown", "back", "cable", "weight"),
    ("Face Pull", "back", "cable", "weight"),
    ("Machine Row", "back", "machine", "weight"),
    ("Hyperextension", "back", "bodyweight", "reps"),
    ("Good Morning", "back", "barbell", "weight"),
    ("Rack Pull", "back", "barbell", "weight"),
    ("Meadows Row", "back", "barbell", "weight"),

    # ---- SHOULDERS / Épaules -------------------------------------------
    ("Overhead Press", "shoulders", "barbell", "weight"),
    ("Seated Barbell Overhead Press", "shoulders", "barbell", "weight"),
    ("Dumbbell Shoulder Press", "shoulders", "dumbbell", "weight"),
    ("Seated Dumbbell Shoulder Press", "shoulders", "dumbbell", "weight"),
    ("Arnold Press", "shoulders", "dumbbell", "weight"),
    ("Lateral Raise", "shoulders", "dumbbell", "weight"),
    ("Cable Lateral Raise", "shoulders", "cable", "weight"),
    ("Machine Lateral Raise", "shoulders", "machine", "weight"),
    ("Front Raise", "shoulders", "dumbbell", "weight"),
    ("Cable Front Raise", "shoulders", "cable", "weight"),
    ("Rear Delt Fly", "shoulders", "dumbbell", "weight"),
    ("Cable Rear Delt Fly", "shoulders", "cable", "weight"),
    ("Reverse Pec Deck", "shoulders", "machine", "weight"),
    ("Upright Row", "shoulders", "barbell", "weight"),
    ("Cable Upright Row", "shoulders", "cable", "weight"),
    ("Smith Machine Overhead Press", "shoulders", "smith_machine", "weight"),
    ("Handstand Push-Up", "shoulders", "bodyweight", "reps"),
    ("Landmine Shoulder Press", "shoulders", "barbell", "weight"),

    # ---- BICEPS --------------------------------------------------------
    ("Barbell Curl", "biceps", "barbell", "weight"),
    ("EZ-Bar Curl", "biceps", "barbell", "weight"),
    ("Dumbbell Curl", "biceps", "dumbbell", "weight"),
    ("Incline Dumbbell Curl", "biceps", "dumbbell", "weight"),
    ("Hammer Curl", "biceps", "dumbbell", "weight"),
    ("Concentration Curl", "biceps", "dumbbell", "weight"),
    ("Preacher Curl", "biceps", "barbell", "weight"),
    ("Dumbbell Preacher Curl", "biceps", "dumbbell", "weight"),
    ("Machine Preacher Curl", "biceps", "machine", "weight"),
    ("Cable Curl", "biceps", "cable", "weight"),
    ("Cable Hammer Curl (Rope)", "biceps", "cable", "weight"),
    ("Spider Curl", "biceps", "dumbbell", "weight"),
    ("Zottman Curl", "biceps", "dumbbell", "weight"),
    ("21s", "biceps", "barbell", "weight"),

    # ---- TRICEPS -------------------------------------------------------
    ("Close-Grip Bench Press", "triceps", "barbell", "weight"),
    ("Dips (Triceps)", "triceps", "bodyweight", "reps"),
    ("Tricep Pushdown (Bar)", "triceps", "cable", "weight"),
    ("Tricep Pushdown (Rope)", "triceps", "cable", "weight"),
    ("Overhead Tricep Extension", "triceps", "dumbbell", "weight"),
    ("Overhead Cable Tricep Extension", "triceps", "cable", "weight"),
    ("Skull Crusher", "triceps", "barbell", "weight"),
    ("Dumbbell Skull Crusher", "triceps", "dumbbell", "weight"),
    ("Tricep Kickback", "triceps", "dumbbell", "weight"),
    ("Cable Kickback", "triceps", "cable", "weight"),
    ("Diamond Push-Up (Triceps)", "triceps", "bodyweight", "reps"),
    ("JM Press", "triceps", "barbell", "weight"),
    ("Machine Tricep Extension", "triceps", "machine", "weight"),

    # ---- QUADRICEPS ----------------------------------------------------
    ("Barbell Back Squat", "quadriceps", "barbell", "weight"),
    ("Barbell Front Squat", "quadriceps", "barbell", "weight"),
    ("High-Bar Squat", "quadriceps", "barbell", "weight"),
    ("Low-Bar Squat", "quadriceps", "barbell", "weight"),
    ("Goblet Squat", "quadriceps", "dumbbell", "weight"),
    ("Bulgarian Split Squat", "quadriceps", "dumbbell", "weight"),
    ("Walking Lunge", "quadriceps", "dumbbell", "weight"),
    ("Reverse Lunge", "quadriceps", "dumbbell", "weight"),
    ("Leg Press", "quadriceps", "machine", "weight"),
    ("Hack Squat", "quadriceps", "machine", "weight"),
    ("Leg Extension", "quadriceps", "machine", "weight"),
    ("Smith Machine Squat", "quadriceps", "smith_machine", "weight"),
    ("Step-Up", "quadriceps", "dumbbell", "weight"),
    ("Box Squat", "quadriceps", "barbell", "weight"),
    ("Pistol Squat", "quadriceps", "bodyweight", "reps"),
    ("Sissy Squat", "quadriceps", "bodyweight", "reps"),

    # ---- HAMSTRINGS ----------------------------------------------------
    ("Lying Leg Curl", "hamstrings", "machine", "weight"),
    ("Seated Leg Curl", "hamstrings", "machine", "weight"),
    ("Nordic Hamstring Curl", "hamstrings", "bodyweight", "reps"),
    ("Stiff-Leg Deadlift", "hamstrings", "barbell", "weight"),
    ("Single-Leg Romanian Deadlift", "hamstrings", "dumbbell", "weight"),
    ("Glute-Ham Raise", "hamstrings", "bodyweight", "reps"),
    ("Cable Pull-Through", "hamstrings", "cable", "weight"),

    # ---- GLUTES --------------------------------------------------------
    ("Hip Thrust", "glutes", "barbell", "weight"),
    ("Glute Bridge", "glutes", "bodyweight", "reps"),
    ("Cable Kickback (Glute)", "glutes", "cable", "weight"),
    ("Sumo Squat", "glutes", "dumbbell", "weight"),
    ("Single-Leg Hip Thrust", "glutes", "bodyweight", "reps"),
    ("Machine Hip Abduction", "glutes", "machine", "weight"),
    ("Bulgarian Split Squat (Glute Focus)", "glutes", "dumbbell", "weight"),

    # ---- CALVES --------------------------------------------------------
    ("Standing Calf Raise", "calves", "machine", "weight"),
    ("Seated Calf Raise", "calves", "machine", "weight"),
    ("Smith Machine Calf Raise", "calves", "smith_machine", "weight"),
    ("Donkey Calf Raise", "calves", "machine", "weight"),
    ("Dumbbell Calf Raise", "calves", "dumbbell", "weight"),
    ("Single-Leg Calf Raise", "calves", "bodyweight", "reps"),
    ("Leg Press Calf Raise", "calves", "machine", "weight"),

    # ---- FOREARMS ------------------------------------------------------
    ("Wrist Curl", "forearms", "barbell", "weight"),
    ("Reverse Wrist Curl", "forearms", "barbell", "weight"),
    ("Farmers Walk", "forearms", "dumbbell", "duration"),
    ("Dead Hang", "forearms", "bodyweight", "duration"),
    ("Reverse Curl", "forearms", "barbell", "weight"),
    ("Wrist Roller", "forearms", "bodyweight", "reps"),

    # ---- CORE / Abdos --------------------------------------------------
    ("Crunch", "core", "bodyweight", "reps"),
    ("Sit-Up", "core", "bodyweight", "reps"),
    ("Hanging Leg Raise", "core", "bodyweight", "reps"),
    ("Hanging Knee Raise", "core", "bodyweight", "reps"),
    ("Cable Crunch", "core", "cable", "weight"),
    ("Machine Crunch", "core", "machine", "weight"),
    ("Plank", "core", "bodyweight", "duration"),
    ("Side Plank", "core", "bodyweight", "duration"),
    ("Russian Twist", "core", "bodyweight", "reps"),
    ("Weighted Russian Twist", "core", "dumbbell", "reps"),
    ("Ab Wheel Rollout", "core", "bodyweight", "reps"),
    ("Dragon Flag", "core", "bodyweight", "reps"),
    ("L-Sit", "core", "bodyweight", "duration"),
    ("Dead Bug", "core", "bodyweight", "reps"),
    ("Bicycle Crunch", "core", "bodyweight", "reps"),
    ("Mountain Climber", "core", "bodyweight", "reps"),
    ("V-Up", "core", "bodyweight", "reps"),
    ("Weighted Sit-Up", "core", "dumbbell", "reps"),
    ("Pallof Press", "core", "cable", "weight"),
    ("Woodchopper", "core", "cable", "weight"),

    # ---- TRAPS ---------------------------------------------------------
    ("Barbell Shrug", "traps", "barbell", "weight"),
    ("Dumbbell Shrug", "traps", "dumbbell", "weight"),
    ("Cable Shrug", "traps", "cable", "weight"),
    ("Smith Machine Shrug", "traps", "smith_machine", "weight"),
    ("Trap Bar Shrug", "traps", "trap_bar", "weight"),

    # ---- CARDIO --------------------------------------------------------
    ("Running", "core", "bodyweight", "distance"),
    ("Cycling", "quadriceps", "machine", "distance"),
    ("Rowing Machine", "back", "machine", "distance"),
    ("Elliptical", "core", "machine", "duration"),
    ("Stair Climber", "quadriceps", "machine", "duration"),
    ("Jump Rope", "calves", "bodyweight", "duration"),
    ("Treadmill Walk", "core", "machine", "distance"),
    ("Treadmill Run", "core", "machine", "distance"),
    ("Burpee", "core", "bodyweight", "reps"),
    ("Box Jump", "quadriceps", "bodyweight", "reps"),
    ("Battle Ropes", "shoulders", "bodyweight", "duration"),
    ("Kettlebell Swing", "glutes", "kettlebell", "reps"),

    # ---- OLYMPIC / FUNCTIONAL -----------------------------------------
    ("Clean and Jerk", "back", "barbell", "weight"),
    ("Snatch", "back", "barbell", "weight"),
    ("Power Clean", "back", "barbell", "weight"),
    ("Hang Clean", "back", "barbell", "weight"),
    ("Push Press", "shoulders", "barbell", "weight"),
    ("Thruster", "quadriceps", "barbell", "weight"),
    ("Turkish Get-Up", "core", "kettlebell", "reps"),
    ("Kettlebell Clean", "back", "kettlebell", "weight"),
    ("Kettlebell Snatch", "back", "kettlebell", "weight"),
]


# --------------------------------------------------------------------------
# Normalisation des muscles Hevy → muscle_group du clone
# --------------------------------------------------------------------------

# Les libellés du TSV Hevy sont fantaisistes (typos, casse, variantes).
# On les mappe vers notre nomenclature stable.
MUSCLE_MAP: dict[str, str] = {
    "chest": "chest",
    "back": "back",
    "shoulders": "shoulders",
    "shoulder": "shoulders",
    "sho": "shoulders",
    "should": "shoulders",
    "upper-arms": "biceps",  # défaut : biceps (on affine au nom ensuite)
    "upper-arm": "biceps",
    "hips": "glutes",
    "hips-fix": "glutes",
    "thighs": "quadriceps",
    "thigh": "quadriceps",
    "thig": "quadriceps",
    "waist": "core",
    "calves": "calves",
    "cardio": "core",
    "forearm": "forearms",
    "forearms": "forearms",
}


def _normalize_muscle(raw: str) -> str:
    """Convertit le libellé de muscle Hevy → notre muscle_group."""
    key = (raw or "").strip().lower()
    return MUSCLE_MAP.get(key, key or "core")


# --------------------------------------------------------------------------
# Normalisation des noms pour matching fuzzy
# --------------------------------------------------------------------------

# Suffixes/tokens à retirer pour matcher les variantes Hevy
_IGNORE_TOKENS = {
    "female",
    "male",
    "version",
    "version-2",
    "version-3",
    "version-4",
    "v2",
    "v3",
    "v4",
    "plate-loaded",
    "plate",
    "loaded",
    "chest-pad",
}

_PAREN_RE = re.compile(r"\([^)]*\)")
_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def _strip_noise(name: str) -> str:
    """Retire les parenthèses, hyphens, ponctuation et tokens de variante."""
    s = name.lower()
    s = _PAREN_RE.sub(" ", s)  # retire (female), (version-2), etc.
    s = s.replace("-", " ")
    for tok in ("version 2", "version 3", "version 4", "plate loaded"):
        s = s.replace(tok, " ")
    # Normalise
    s = _NON_ALNUM.sub(" ", s)
    # Retire tokens ignorés
    parts = [p for p in s.split() if p and p not in _IGNORE_TOKENS]
    return " ".join(parts).strip()


def _name_key(name: str) -> str:
    """Clé comparable : tokens triés pour matcher 'Dumbbell Row' ↔ 'Row Dumbbell'."""
    stripped = _strip_noise(name)
    tokens = sorted(stripped.split())
    return " ".join(tokens)


# --------------------------------------------------------------------------
# Devinette d'équipement depuis le nom
# --------------------------------------------------------------------------

_EQUIP_KEYWORDS: list[tuple[str, str]] = [
    ("smith", "smith_machine"),
    ("trap-bar", "trap_bar"),
    ("trap bar", "trap_bar"),
    ("barbell", "barbell"),
    ("dumbbell", "dumbbell"),
    ("kettlebell", "kettlebell"),
    ("cable", "cable"),
    ("lever", "machine"),
    ("machine", "machine"),
    ("band", "band"),
    ("resistance band", "band"),
    ("weighted plate", "plate"),
    ("plate", "plate"),
    ("landmine", "barbell"),
    ("bodyweight", "bodyweight"),
]


def _guess_equipment(name: str) -> str:
    """Meilleure supposition d'équipement à partir du nom d'exercice."""
    low = name.lower()
    for kw, eq in _EQUIP_KEYWORDS:
        if kw in low:
            return eq
    return "bodyweight"


def _guess_exercise_type(name: str, muscle: str) -> str:
    """Supposition grossière du type d'exercice (weight/reps/duration/distance)."""
    low = name.lower()
    if any(k in low for k in ("walk", "run", "cycling", "rowing-machine", "rowing")):
        return "distance"
    if any(k in low for k in ("plank", "hang", "hold", "l-sit")):
        return "duration"
    # Bodyweight non-weighted → reps
    equip = _guess_equipment(name)
    if equip == "bodyweight":
        return "reps"
    return "weight"


# --------------------------------------------------------------------------
# Parsing du TSV
# --------------------------------------------------------------------------


def _load_cdn_entries() -> list[dict]:
    """Charge le TSV CDN en liste de dicts {cdn_id, name, muscle, slug}.

    Retourne [] si le fichier est absent (pas de vidéos attachées).
    """
    if not _TSV_PATH.exists():
        return []
    entries = []
    with _TSV_PATH.open("r", encoding="utf-8") as f:
        header = f.readline()  # skip header
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            cdn_id, raw_name, raw_muscle = parts[0], parts[1], parts[2]
            # Le slug CDN est la concat `Name-With-Hyphens_Muscle` telle qu'écrite
            # dans l'URL ; on reconstruit depuis les valeurs brutes.
            slug = f"{raw_name}_{raw_muscle}"
            entries.append(
                {
                    "cdn_id": cdn_id.strip(),
                    "raw_name": raw_name.strip(),
                    "raw_muscle": raw_muscle.strip(),
                    "slug": slug.strip(),
                    # Nom humain : remplace les hyphens par espaces
                    "name": raw_name.replace("-", " ").strip(),
                    "muscle": _normalize_muscle(raw_muscle),
                    "key": _name_key(raw_name.replace("-", " ")),
                }
            )
    return entries


# --------------------------------------------------------------------------
# Matching curated ↔ CDN
# --------------------------------------------------------------------------


def _is_variant(raw_name: str) -> bool:
    """Variante secondaire (female, version-2, etc.) à éviter si possible."""
    low = raw_name.lower()
    return any(
        tok in low
        for tok in (
            "(female)",
            "(male)",
            "(version-2)",
            "(version-3)",
            "(version-4)",
        )
    )


def _find_cdn_match(
    name: str, muscle_group: str, entries: Iterable[dict]
) -> dict | None:
    """Cherche la meilleure entrée CDN pour un exercice (name, muscle).

    Stratégie :
    1. Match exact sur clé normalisée (tokens triés).
    2. Match par inclusion (tokens curated ⊂ tokens CDN).
    3. Score similitude (taille de l'intersection de tokens).
    En cas d'égalité, on privilégie muscle compatible et non-variante.
    """
    target_key = _name_key(name)
    target_tokens = set(target_key.split())
    if not target_tokens:
        return None

    exact: list[dict] = []
    partial: list[tuple[int, dict]] = []

    for e in entries:
        cdn_tokens = set(e["key"].split())
        if not cdn_tokens:
            continue
        if e["key"] == target_key:
            exact.append(e)
            continue
        # Inclusion : tous les tokens curated sont dans cdn → fort candidat
        inter = target_tokens & cdn_tokens
        if not inter:
            continue
        # Score : taille de l'intersection − pénalité tokens en trop
        extra = len(cdn_tokens - target_tokens)
        score = len(inter) * 10 - extra
        partial.append((score, e))

    def _rank(e: dict) -> tuple[int, int]:
        # Priorité : muscle compatible, puis non-variante
        muscle_ok = 1 if e["muscle"] == muscle_group else 0
        variant = 0 if _is_variant(e["raw_name"]) else 1
        return (muscle_ok, variant)

    if exact:
        exact.sort(key=_rank, reverse=True)
        return exact[0]

    if partial:
        # On trie par score DESC, puis par rank
        partial.sort(key=lambda p: (p[0], _rank(p[1])), reverse=True)
        best_score, best = partial[0]
        # Exige un score minimum (au moins 2 tokens en commun, ou un match fort sur 1 long)
        min_tokens = 2 if len(target_tokens) >= 3 else 1
        if len(target_tokens & set(best["key"].split())) >= min_tokens:
            return best
    return None


# --------------------------------------------------------------------------
# Seed complet (table vide)
# --------------------------------------------------------------------------


def _make_curated_list() -> list[dict]:
    """Construit la liste des exercices curated avec vidéos matchées.

    Retourne une liste de dicts exploitables pour insertion.
    """
    entries = _load_cdn_entries()
    used_cdn_ids: set[str] = set()
    curated_result: list[dict] = []

    for name, muscle, equipment, etype in EXERCISES:
        match = _find_cdn_match(name, muscle, entries)
        cdn_id = match["cdn_id"] if match else None
        cdn_slug = match["slug"] if match else None
        if cdn_id:
            used_cdn_ids.add(cdn_id)
        curated_result.append(
            {
                "name": name,
                "muscle_group": muscle,
                "equipment": equipment,
                "exercise_type": etype,
                "cdn_video_id": cdn_id,
                "cdn_video_slug": cdn_slug,
            }
        )

    # Ajoute les entrées CDN non-matchées (best effort, évite les variantes female/version)
    # pour étoffer la bibliothèque à ≈ 300 exercices.
    curated_keys = {_name_key(e["name"]) for e in curated_result}
    extras: list[dict] = []
    for e in entries:
        if e["cdn_id"] in used_cdn_ids:
            continue
        if _is_variant(e["raw_name"]):
            continue
        # Évite les noms trop collisionnels (déjà dans curated)
        if e["key"] in curated_keys:
            continue
        extras.append(
            {
                "name": e["name"].title(),
                "muscle_group": e["muscle"],
                "equipment": _guess_equipment(e["name"]),
                "exercise_type": _guess_exercise_type(e["name"], e["muscle"]),
                "cdn_video_id": e["cdn_id"],
                "cdn_video_slug": e["slug"],
            }
        )
        used_cdn_ids.add(e["cdn_id"])
        curated_keys.add(e["key"])

    return curated_result + extras


def seed_exercises(session) -> int:
    """Insère la bibliothèque d'exercices complète (seed initial).

    Retourne le nombre d'exercices insérés.
    """
    items = _make_curated_list()
    for item in items:
        session.add(
            Exercise(
                name=item["name"],
                muscle_group=item["muscle_group"],
                equipment=item["equipment"],
                exercise_type=item["exercise_type"],
                cdn_video_id=item["cdn_video_id"],
                cdn_video_slug=item["cdn_video_slug"],
                is_custom=False,
                user_id=None,
            )
        )
    session.commit()
    return len(items)


# --------------------------------------------------------------------------
# Sync idempotent (DB existante)
# --------------------------------------------------------------------------


def sync_cdn_videos(session) -> tuple[int, int]:
    """Attache les vidéos CDN aux exercices sans vidéo, ajoute les manquants.

    Retourne (updated, added) — nombre de MAJ et nombre d'inserts.
    Idempotent : rien n'est fait si tout est déjà synchro.
    """
    entries = _load_cdn_entries()
    if not entries:
        return (0, 0)

    updated = 0
    added = 0

    # 1. UPDATE : exercices sans vidéo → match par nom
    existing = session.query(Exercise).filter(Exercise.is_custom.is_(False)).all()
    used_cdn_ids = {e.cdn_video_id for e in existing if e.cdn_video_id}
    available = [e for e in entries if e["cdn_id"] not in used_cdn_ids]

    for ex in existing:
        if ex.cdn_video_id:
            continue
        match = _find_cdn_match(ex.name, ex.muscle_group or "", available)
        if not match:
            continue
        ex.cdn_video_id = match["cdn_id"]
        ex.cdn_video_slug = match["slug"]
        used_cdn_ids.add(match["cdn_id"])
        available = [e for e in available if e["cdn_id"] != match["cdn_id"]]
        updated += 1

    if updated:
        session.commit()

    # 2. INSERT : entrées TSV pas encore dans la DB (par cdn_id)
    existing_keys = {_name_key(e.name) for e in existing}
    for e in available:
        if _is_variant(e["raw_name"]):
            continue
        if e["key"] in existing_keys:
            continue
        session.add(
            Exercise(
                name=e["name"].title(),
                muscle_group=e["muscle"],
                equipment=_guess_equipment(e["name"]),
                exercise_type=_guess_exercise_type(e["name"], e["muscle"]),
                cdn_video_id=e["cdn_id"],
                cdn_video_slug=e["slug"],
                is_custom=False,
                user_id=None,
            )
        )
        existing_keys.add(e["key"])
        added += 1

    if added:
        session.commit()

    return (updated, added)
