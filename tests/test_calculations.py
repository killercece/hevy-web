"""Tests des calculs métier (e1RM, volume, conversions)."""

from __future__ import annotations

import pytest

from app.utils.calculations import (
    convert_weight,
    e1rm,
    kg_to_lb,
    lb_to_kg,
    volume,
)


class TestE1RM:
    def test_epley_formula(self):
        # 100 × (1 + 10/30) = 133.33
        assert abs(e1rm(100, 10) - 133.33) < 0.1

    def test_single_rep_returns_weight(self):
        assert e1rm(150, 1) == 150

    def test_zero_returns_zero(self):
        assert e1rm(0, 10) == 0
        assert e1rm(100, 0) == 0
        assert e1rm(None, 5) == 0

    def test_brzycki(self):
        # Brzycki : 100 / (1.0278 - 0.0278×10) = 100 / 0.7498 ≈ 133.4
        result = e1rm(100, 10, formula="brzycki")
        assert 130 < result < 140


class TestVolume:
    class _Set:
        def __init__(self, weight, reps, completed=True):
            self.weight = weight
            self.reps = reps
            self.completed = completed

    def test_volume_sum(self):
        sets = [self._Set(100, 10), self._Set(110, 8)]
        # 1000 + 880 = 1880
        assert volume(sets) == 1880

    def test_ignores_incomplete(self):
        sets = [self._Set(100, 10), self._Set(110, 8, completed=False)]
        assert volume(sets) == 1000

    def test_empty(self):
        assert volume([]) == 0


class TestConversions:
    def test_kg_to_lb(self):
        assert abs(kg_to_lb(100) - 220.46) < 0.1

    def test_lb_to_kg(self):
        assert abs(lb_to_kg(220.46) - 100) < 0.1

    def test_convert_weight_noop(self):
        assert convert_weight(100, "kg", "kg") == 100

    def test_convert_kg_lb(self):
        assert abs(convert_weight(100, "kg", "lb") - 220.46) < 0.1
