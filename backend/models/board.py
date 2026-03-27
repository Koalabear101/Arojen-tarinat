"""Game board with grid-based unit placement and movement."""
from __future__ import annotations

from typing import Optional

from backend.models.unit import Unit


class Board:
    """A 2-D grid that holds units and supports coordinate operations."""

    def __init__(self, width: int = 10, height: int = 10) -> None:
        self.width = width
        self.height = height
        self._grid: list[list[Optional[Unit]]] = [
            [None for _ in range(width)] for _ in range(height)
        ]

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def get_unit(self, x: int, y: int) -> Optional[Unit]:
        if not self.in_bounds(x, y):
            return None
        return self._grid[y][x]

    def place_unit(self, x: int, y: int, unit: Unit) -> bool:
        """Place a unit; returns False if out of bounds or occupied."""
        if not self.in_bounds(x, y):
            return False
        if self._grid[y][x] is not None:
            return False
        self._grid[y][x] = unit
        return True

    def remove_unit(self, x: int, y: int) -> Optional[Unit]:
        """Remove and return the unit at (x, y)."""
        if not self.in_bounds(x, y):
            return None
        unit = self._grid[y][x]
        self._grid[y][x] = None
        return unit

    def move_unit(self, from_x: int, from_y: int, to_x: int, to_y: int) -> bool:
        """Move a unit from one cell to another. Validates distance <= speed."""
        unit = self.get_unit(from_x, from_y)
        if unit is None:
            return False
        if not self.in_bounds(to_x, to_y):
            return False
        if self._grid[to_y][to_x] is not None:
            return False
        dist = self.distance(from_x, from_y, to_x, to_y)
        if dist > unit.speed:
            return False
        self._grid[from_y][from_x] = None
        self._grid[to_y][to_x] = unit
        return True

    @staticmethod
    def distance(x1: int, y1: int, x2: int, y2: int) -> int:
        """Chebyshev distance (diagonal movement costs 1)."""
        return max(abs(x2 - x1), abs(y2 - y1))

    def find_unit(self, uid: str) -> Optional[tuple[int, int]]:
        """Return (x, y) of a unit by its uid, or None."""
        for y in range(self.height):
            for x in range(self.width):
                u = self._grid[y][x]
                if u is not None and u.uid == uid:
                    return (x, y)
        return None

    def get_units_by_faction(self, faction_id: str) -> list[tuple[int, int, Unit]]:
        """Return all (x, y, unit) triples for a faction."""
        results: list[tuple[int, int, Unit]] = []
        for y in range(self.height):
            for x in range(self.width):
                u = self._grid[y][x]
                if u is not None and u.faction_id == faction_id:
                    results.append((x, y, u))
        return results

    def units_in_range(
        self, x: int, y: int, attack_range: int, exclude_faction: Optional[str] = None
    ) -> list[tuple[int, int, Unit]]:
        """Return enemy units within attack range of (x, y)."""
        targets: list[tuple[int, int, Unit]] = []
        for dy in range(-attack_range, attack_range + 1):
            for dx in range(-attack_range, attack_range + 1):
                tx, ty = x + dx, y + dy
                if (tx, ty) == (x, y):
                    continue
                u = self.get_unit(tx, ty)
                if u is not None and (exclude_faction is None or u.faction_id != exclude_faction):
                    targets.append((tx, ty, u))
        return targets

    def to_list(self) -> list[list[Optional[dict]]]:
        """Serialize entire board for API responses."""
        result: list[list[Optional[dict]]] = []
        for y in range(self.height):
            row: list[Optional[dict]] = []
            for x in range(self.width):
                u = self._grid[y][x]
                row.append(u.to_dict() if u is not None else None)
            result.append(row)
        return result
