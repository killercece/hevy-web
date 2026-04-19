"""Seed de la bibliothèque d'exercices.

~180 exercices populaires pré-chargés au premier démarrage.
Format : (name, muscle_group, equipment, exercise_type)
"""

from __future__ import annotations

from ..models import Exercise

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

    # ---- LEGS / Jambes (quads dominant) --------------------------------
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

    # ---- GLUTES / Fessiers ---------------------------------------------
    ("Hip Thrust", "glutes", "barbell", "weight"),
    ("Glute Bridge", "glutes", "bodyweight", "reps"),
    ("Cable Kickback (Glute)", "glutes", "cable", "weight"),
    ("Sumo Squat", "glutes", "dumbbell", "weight"),
    ("Single-Leg Hip Thrust", "glutes", "bodyweight", "reps"),
    ("Machine Hip Abduction", "glutes", "machine", "weight"),
    ("Bulgarian Split Squat (Glute Focus)", "glutes", "dumbbell", "weight"),

    # ---- CALVES / Mollets ----------------------------------------------
    ("Standing Calf Raise", "calves", "machine", "weight"),
    ("Seated Calf Raise", "calves", "machine", "weight"),
    ("Smith Machine Calf Raise", "calves", "smith_machine", "weight"),
    ("Donkey Calf Raise", "calves", "machine", "weight"),
    ("Dumbbell Calf Raise", "calves", "dumbbell", "weight"),
    ("Single-Leg Calf Raise", "calves", "bodyweight", "reps"),
    ("Leg Press Calf Raise", "calves", "machine", "weight"),

    # ---- FOREARMS / Avant-bras -----------------------------------------
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


def seed_exercises(session) -> int:
    """Insère la bibliothèque d'exercices si la table est vide.

    Retourne le nombre d'exercices insérés.
    """
    count = 0
    for name, muscle, equipment, etype in EXERCISES:
        ex = Exercise(
            name=name,
            muscle_group=muscle,
            equipment=equipment,
            exercise_type=etype,
            is_custom=False,
            user_id=None,
        )
        session.add(ex)
        count += 1
    session.commit()
    return count
