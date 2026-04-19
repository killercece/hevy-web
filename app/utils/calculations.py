"""Calculs métier : e1RM, volume, conversions d'unités.

Formules :
- Epley (par défaut) : e1RM = weight × (1 + reps / 30)
- Brzycki : e1RM = weight / (1.0278 - 0.0278 × reps)
- Lander : e1RM = 100 × weight / (101.3 - 2.67123 × reps)
"""

from __future__ import annotations

from typing import Iterable

KG_TO_LB = 2.2046226218
LB_TO_KG = 1 / KG_TO_LB


def e1rm(weight: float | None, reps: int | None, formula: str = "epley") -> float:
    """Calcule l'e1RM (estimated 1-rep max).

    Retourne 0.0 si weight ou reps est nul/None.
    Pour reps == 1, e1RM = weight quelle que soit la formule.
    """
    if not weight or not reps or reps < 1:
        return 0.0
    if reps == 1:
        return float(weight)

    if formula == "brzycki":
        denom = 1.0278 - 0.0278 * reps
        return weight / denom if denom > 0 else 0.0
    if formula == "lander":
        denom = 101.3 - 2.67123 * reps
        return 100 * weight / denom if denom > 0 else 0.0
    # Epley par défaut
    return weight * (1 + reps / 30)


def volume(sets: Iterable) -> float:
    """Calcule le volume total d'une liste de sets (weight × reps).

    Ignore les sets non-completés ou avec champ manquant.
    """
    total = 0.0
    for s in sets:
        if getattr(s, "completed", False):
            w = getattr(s, "weight", None) or 0
            r = getattr(s, "reps", None) or 0
            total += w * r
    return total


def kg_to_lb(weight_kg: float) -> float:
    """Convertit kilogrammes en livres."""
    return weight_kg * KG_TO_LB


def lb_to_kg(weight_lb: float) -> float:
    """Convertit livres en kilogrammes."""
    return weight_lb * LB_TO_KG


def convert_weight(weight: float, from_unit: str, to_unit: str) -> float:
    """Convertit un poids entre unités (kg/lb)."""
    if from_unit == to_unit:
        return weight
    if from_unit == "kg" and to_unit in ("lb", "lbs"):
        return kg_to_lb(weight)
    if from_unit in ("lb", "lbs") and to_unit == "kg":
        return lb_to_kg(weight)
    return weight
