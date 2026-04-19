"""Traductions EN → FR pour l'UI (muscle groups, équipements, noms d'exercices).

Stratégie noms d'exercices : on découpe un nom en [qualifieurs] + [mouvement]
puis on réassemble en français avec les qualifieurs en suffixe naturel.
"""

from __future__ import annotations

import re

# --------------------------------------------------------------------------
# Groupes musculaires
# --------------------------------------------------------------------------

MUSCLE_FR: dict[str, str] = {
    "chest": "Pectoraux",
    "back": "Dos",
    "lats": "Dorsaux",
    "shoulders": "Épaules",
    "traps": "Trapèzes",
    "biceps": "Biceps",
    "triceps": "Triceps",
    "forearms": "Avant-bras",
    "upper arms": "Bras",
    "legs": "Jambes",
    "quads": "Quadriceps",
    "quadriceps": "Quadriceps",
    "hamstrings": "Ischios",
    "glutes": "Fessiers",
    "hips": "Hanches",
    "thighs": "Cuisses",
    "calves": "Mollets",
    "core": "Abdos",
    "abs": "Abdos",
    "waist": "Taille",
    "cardio": "Cardio",
    "neck": "Cou",
}

# --------------------------------------------------------------------------
# Équipements
# --------------------------------------------------------------------------

EQUIPMENT_FR: dict[str, str] = {
    "barbell": "Barre",
    "dumbbell": "Haltères",
    "cable": "Poulie",
    "machine": "Machine",
    "smith_machine": "Smith machine",
    "smith machine": "Smith machine",
    "bodyweight": "Poids du corps",
    "kettlebell": "Kettlebell",
    "band": "Élastique",
    "bands": "Élastique",
    "resistance band": "Élastique",
    "trap_bar": "Trap bar",
    "trap bar": "Trap bar",
    "ez bar": "Barre EZ",
    "ez_bar": "Barre EZ",
    "medicine_ball": "Medicine ball",
    "medicine ball": "Medicine ball",
    "bench": "Banc",
    "other": "Autre",
    "none": "—",
    "": "—",
}

EXERCISE_TYPE_FR: dict[str, str] = {
    "weight": "Poids + reps",
    "reps": "Répétitions",
    "duration": "Durée",
    "distance": "Distance",
    "bodyweight": "Poids du corps",
    "assisted_bodyweight": "Assisté",
    "weighted_bodyweight": "Lesté",
}


# --------------------------------------------------------------------------
# Qualifieurs équipement (extraits du nom, repositionnés en suffixe)
# Ordre : plus spécifique d'abord
# --------------------------------------------------------------------------

_EQUIP_PREFIXES: list[tuple[str, str]] = [
    (r"\bsmith machine\b", "à la Smith machine"),
    (r"\bresistance band\b", "avec élastique"),
    (r"\btrap[- ]?bar\b", "à la trap bar"),
    (r"\bmedicine ball\b", "avec medicine ball"),
    (r"\bez[- ]?bar\b", "à la barre EZ"),
    (r"\bbarbell\b", "à la barre"),
    (r"\bdumbbell\b", "haltères"),
    (r"\bkettlebell\b", "kettlebell"),
    (r"\bcable\b", "à la poulie"),
    (r"\bmachine\b", "machine"),
    (r"\bband\b", "élastique"),
    (r"\bbodyweight\b", "poids du corps"),
]


# --------------------------------------------------------------------------
# Mouvements : traduction pour la partie "core" du nom
# Ordre : plus spécifique d'abord, car on applique les substitutions en
# séquence et sur résultat.
# --------------------------------------------------------------------------

_MOVEMENT_PATTERNS: list[tuple[str, str]] = [
    # Deadlift variations (avant la règle générique)
    (r"\bromanian deadlift\b", "soulevé de terre roumain"),
    (r"\bstraight leg deadlift\b", "soulevé jambes tendues"),
    (r"\bstiff leg deadlift\b", "soulevé jambes tendues"),
    (r"\bsumo deadlift\b", "soulevé sumo"),
    (r"\brack pull\b", "rack pull"),
    (r"\bdeadlift\b", "soulevé de terre"),

    # Squat variations
    (r"\bfront squat\b", "squat avant"),
    (r"\bback squat\b", "squat"),
    (r"\bgoblet squat\b", "goblet squat"),
    (r"\bhack squat\b", "hack squat"),
    (r"\bbulgarian split squat\b", "fente bulgare"),
    (r"\bsplit squat\b", "fente bulgare"),
    (r"\bjump squat\b", "squat sauté"),
    (r"\bsumo squat\b", "squat sumo"),
    (r"\bzercher squat\b", "squat Zercher"),
    (r"\bwide squat\b", "squat écarté"),
    (r"\bfull squat\b", "squat complet"),
    (r"\bsquat\b", "squat"),

    # Lunge / step
    (r"\bwalking lunge\b", "fente marchée"),
    (r"\breverse lunge\b", "fente arrière"),
    (r"\bside lunge\b", "fente latérale"),
    (r"\blateral lunge\b", "fente latérale"),
    (r"\blunges\b", "fentes"),
    (r"\blunge\b", "fente"),
    (r"\bstep[- ]?ups?\b", "montée sur banc"),
    (r"\bhip thrust\b", "hip thrust"),
    (r"\bglute bridge\b", "pont fessier"),
    (r"\bgood morning\b", "good morning"),

    # Press (spécifique avant générique)
    (r"\bclose grip bench press\b", "développé couché prise serrée"),
    (r"\bwide grip bench press\b", "développé couché prise large"),
    (r"\bincline bench press\b", "développé incliné"),
    (r"\bdecline bench press\b", "développé décliné"),
    (r"\bincline chest press\b", "développé incliné"),
    (r"\bflat bench press\b", "développé couché"),
    (r"\bbench press\b", "développé couché"),
    (r"\bchest press\b", "développé pectoraux"),
    (r"\bshoulder press\b", "développé épaules"),
    (r"\boverhead press\b", "développé militaire"),
    (r"\bmilitary press\b", "développé militaire"),
    (r"\bpush press\b", "push press"),
    (r"\bpike press\b", "pike press"),
    (r"\blandmine press\b", "landmine press"),
    (r"\barnold press\b", "Arnold press"),
    (r"\bfloor press\b", "floor press"),
    (r"\bleg press\b", "presse à cuisses"),
    (r"\bpress\b", "développé"),

    # Pull / row
    (r"\blat pulldown\b", "tirage vertical"),
    (r"\bpulldown\b", "tirage"),
    (r"\bpull[- ]?ups?\b", "traction"),
    (r"\bchin[- ]?ups?\b", "traction supination"),
    (r"\bbent[- ]?over row\b", "rowing buste penché"),
    (r"\bpendlay row\b", "rowing Pendlay"),
    (r"\bt[- ]?bar row\b", "rowing T-bar"),
    (r"\binverted row\b", "rowing inversé"),
    (r"\bseated row\b", "rowing assis"),
    (r"\bone arm row\b", "rowing un bras"),
    (r"\bmeadows row\b", "rowing Meadows"),
    (r"\bchest supported row\b", "rowing à plat ventre"),
    (r"\brow\b", "rowing"),
    (r"\bshrugs?\b", "shrugs"),
    (r"\bface pull\b", "face pull"),
    (r"\bstraight[- ]arm pulldown\b", "pull-over poulie"),
    (r"\bpullover\b", "pull-over"),

    # Bicep curls
    (r"\bbarbell curl\b", "curl à la barre"),
    (r"\bdumbbell curl\b", "curl haltères"),
    (r"\bhammer curl\b", "curl marteau"),
    (r"\bpreacher curl\b", "curl au pupitre"),
    (r"\bspider curl\b", "curl spider"),
    (r"\bconcentration curl\b", "curl concentration"),
    (r"\bzottman curl\b", "curl Zottman"),
    (r"\bincline curl\b", "curl incliné"),
    (r"\bdrag curl\b", "curl drag"),
    (r"\bprone incline curl\b", "curl incliné face"),
    (r"\bcurl\b", "curl"),

    # Triceps
    (r"\btriceps? extension\b", "extension triceps"),
    (r"\blying triceps? extension\b", "triceps allongé"),
    (r"\bskull crushers?\b", "barre au front"),
    (r"\boverhead triceps extension\b", "extension triceps verticale"),
    (r"\boverhead extension\b", "extension verticale"),
    (r"\bkickbacks?\b", "kickback"),
    (r"\btriceps? pushdown\b", "pushdown triceps"),
    (r"\bpushdown\b", "pushdown"),
    (r"\bdips?\b", "dips"),

    # Shoulders
    (r"\blateral raises?\b", "élévation latérale"),
    (r"\bside raises?\b", "élévation latérale"),
    (r"\bfront raises?\b", "élévation frontale"),
    (r"\brear delt fly\b", "oiseau"),
    (r"\brear delt raises?\b", "oiseau"),
    (r"\breverse fly\b", "oiseau inversé"),
    (r"\breverse pec deck\b", "pec deck inversé"),
    (r"\bupright row\b", "rowing menton"),
    (r"\bhandstand push[- ]?ups?\b", "ATR pompe"),
    (r"\bhandstand\b", "équilibre"),

    # Chest / flys
    (r"\bcable crossover\b", "cable crossover"),
    (r"\bcable fly\b", "écartés poulie"),
    (r"\bdumbbell fly\b", "écartés haltères"),
    (r"\bincline fly\b", "écartés inclinés"),
    (r"\bflys?\b", "écartés"),
    (r"\bflyes\b", "écartés"),
    (r"\bpec deck\b", "pec deck"),
    (r"\bpush[- ]?ups?\b", "pompes"),
    (r"\bdiamond push[- ]?ups?\b", "pompes diamant"),

    # Legs isolation
    (r"\bleg extensions?\b", "leg extension"),
    (r"\bleg curls?\b", "leg curl"),
    (r"\bhamstring curls?\b", "leg curl"),
    (r"\bseated calf raises?\b", "mollets assis"),
    (r"\bstanding calf raises?\b", "mollets debout"),
    (r"\bdonkey calf raises?\b", "mollets âne"),
    (r"\bcalf raises?\b", "mollets"),

    # Abs / core
    (r"\b3[- ]?4 sit[- ]?ups?\b", "redressement 3/4"),
    (r"\bhanging leg raises?\b", "relevé de jambes suspendu"),
    (r"\bleg raises?\b", "relevé de jambes"),
    (r"\bknee raises?\b", "relevé de genoux"),
    (r"\bsit[- ]?ups?\b", "redressement assis"),
    (r"\bcrunches?\b", "crunch"),
    (r"\bside plank\b", "planche latérale"),
    (r"\bplank\b", "planche"),
    (r"\brussian twists?\b", "Russian twist"),
    (r"\bhyperextension\b", "hyperextension"),
    (r"\bback extension\b", "extension lombaire"),
    (r"\bdead bug\b", "dead bug"),
    (r"\bv[- ]?ups?\b", "V-up"),
    (r"\bmountain climbers?\b", "climber"),
    (r"\bburpees?\b", "burpee"),
    (r"\bheel touchers?\b", "touchers de talons"),
    (r"\bside bends?\b", "flexion latérale"),
    (r"\bwood chops?\b", "wood chop"),
    (r"\bab wheel\b", "roue abdo"),
    (r"\bair bike\b", "air bike"),
    (r"\braises?\b", "élévation"),
    (r"\b21s\b", "21s"),

    # Qualifiers (adjectifs) — positionnés en adjectif français
    (r"\bincline\b", "incliné"),
    (r"\bdecline\b", "décliné"),
    (r"\bflat\b", "plat"),
    (r"\bseated\b", "assis"),
    (r"\bstanding\b", "debout"),
    (r"\blying\b", "allongé"),
    (r"\bkneeling\b", "à genoux"),
    (r"\bassisted\b", "assisté"),
    (r"\bweighted\b", "lesté"),
    (r"\bone[- ]?arm\b", "un bras"),
    (r"\bsingle[- ]?arm\b", "un bras"),
    (r"\btwo[- ]?arm\b", "deux bras"),
    (r"\bone[- ]?leg\b", "une jambe"),
    (r"\bsingle[- ]?leg\b", "une jambe"),
    (r"\balternating\b", "alterné"),
    (r"\balternate\b", "alterné"),
    (r"\boverhead\b", "au-dessus de la tête"),
    (r"\bbehind the neck\b", "derrière la nuque"),
    (r"\bwide[- ]?grip\b", "prise large"),
    (r"\bclose[- ]?grip\b", "prise serrée"),
    (r"\breverse[- ]?grip\b", "prise inversée"),
    (r"\breverse\b", "inversé"),
    (r"\bwith rope\b", "à la corde"),

    # Connectors
    (r"\band\b", "et"),
    (r"\bor\b", "ou"),
    (r"\bwith\b", "avec"),
]

_EQUIP_COMPILED = [(re.compile(p, re.IGNORECASE), repl) for p, repl in _EQUIP_PREFIXES]
_MOVE_COMPILED = [(re.compile(p, re.IGNORECASE), repl) for p, repl in _MOVEMENT_PATTERNS]


def _extract_equipment(name: str) -> tuple[str, str]:
    """Retire le préfixe d'équipement du nom, retourne (reste, qualifier_fr).

    `name` est passé en minuscules pour le matching mais on renvoie le
    reste nettoyé (espaces). Le qualifier est vide si aucun équipement
    détecté.
    """
    lowered = name.strip()
    for rx, repl in _EQUIP_COMPILED:
        m = rx.search(lowered)
        if m:
            rest = (lowered[: m.start()] + " " + lowered[m.end():]).strip()
            rest = re.sub(r"\s+", " ", rest)
            return rest, repl
    return lowered, ""


def _translate_core(text: str) -> str:
    """Applique les patterns de mouvement sur le texte (in-place)."""
    result = text
    for rx, repl in _MOVE_COMPILED:
        result = rx.sub(repl, result)
    return result


def translate_exercise_name(name: str) -> str:
    """Traduit un nom d'exercice EN → FR.

    Algo :
    1. Extrait le qualificatif d'équipement (barbell/dumbbell/cable/...).
    2. Traduit le reste (mouvement + adjectifs).
    3. Réassemble "Mouvement [qualifieur]" capitalisé.
    """
    if not name:
        return name
    rest, equip_fr = _extract_equipment(name)
    core = _translate_core(rest)
    # Nettoyage
    core = re.sub(r"\s+", " ", core).strip(" -()")
    if not core and equip_fr:
        core = equip_fr
        equip_fr = ""
    # Capitalisation
    if core:
        core = core[0].upper() + core[1:]
    result = f"{core} {equip_fr}".strip() if equip_fr else core
    return result


def translate_muscle(muscle: str) -> str:
    if not muscle:
        return ""
    return MUSCLE_FR.get(muscle.lower(), muscle.title())


def translate_equipment(equipment: str) -> str:
    if not equipment:
        return "—"
    return EQUIPMENT_FR.get(equipment.lower(), equipment.replace("_", " ").title())


def translate_exercise_type(etype: str) -> str:
    if not etype:
        return ""
    return EXERCISE_TYPE_FR.get(etype.lower(), etype.title())
