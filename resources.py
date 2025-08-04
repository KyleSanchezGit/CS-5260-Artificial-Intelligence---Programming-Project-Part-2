"""resources.py
Core resource abstractions for the CS 5260 *AI Nations* project.

A **ResourceBundle** is an immutable‑by‑default mapping from resource names
(strings) to integer quantities (≥ 0 for assets, ≤ 0 for debts/waste).  The
class provides safe arithmetic (addition, subtraction, scaling) plus helper
methods used by *Country* and *World* objects.

Design choices
--------------
* **Self‑cleaning**: zero‑quantity keys are automatically removed to keep the
  bundle compact.
* **Functional flavour**: arithmetic operators return *new* bundles; in‑place
  mutation is available via :py:meth:`add` when performance matters.
* **Type‑safe**: the public API uses only ``ResourceBundle`` or ``Mapping``
  where appropriate so static checkers (mypy/Pyright) succeed.
* **No floats**: integer arithmetic avoids rounding errors and matches the
  project’s *unit* resource model.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, Mapping


@dataclass
class ResourceBundle:
    """A multiset of resources with integer quantities."""

    amounts: Dict[str, int] = field(default_factory=dict)

    # ---------------------------------------------------------------------
    # Construction helpers
    # ---------------------------------------------------------------------
    def __post_init__(self) -> None:  # noqa: D401 – simple function
        # Ensure no 0‑entries remain right after construction
        self._clean_zeroes()

    @classmethod
    def from_pairs(cls, pairs: Iterable[tuple[str, int]]) -> "ResourceBundle":
        """Create a bundle from an iterable of *(resource, qty)* pairs."""
        return cls(dict(pairs))

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------
    def quantity(self, resource: str) -> int:
        """Return the current quantity (0 if absent)."""
        return self.amounts.get(resource, 0)
    
    def has(self, other: "ResourceBundle") -> bool:
        """Alias for has_enough(), so Country.has_resources can call .has()"""
        return self.has_enough(other)
    

    def has_enough(self, other: "ResourceBundle") -> bool:
        """True iff *self* contains at least the quantities in *other*."""
        return all(self.quantity(r) >= q for r, q in other)

    # ------------------------------------------------------------------
    # Functional arithmetic operators
    # ------------------------------------------------------------------
    def __add__(self, other: "ResourceBundle") -> "ResourceBundle":
        new = self.copy()
        new._iadd(other)
        return new

    def __sub__(self, other: "ResourceBundle") -> "ResourceBundle":
        new = self.copy()
        new._isub(other)
        return new

    def scale(self, factor: int) -> "ResourceBundle":
        """Return a *new* bundle scaled by *factor* (≥ 0)."""
        if factor < 0:
            raise ValueError("Factor must be non‑negative")
        return ResourceBundle({r: q * factor for r, q in self})

    # ------------------------------------------------------------------
    # In‑place helpers (prefixed with underscore to discourage casual use)
    # ------------------------------------------------------------------
    def _iadd(self, other: "ResourceBundle") -> "ResourceBundle":
        for r, q in other:
            self.amounts[r] = self.quantity(r) + q
        self._clean_zeroes()
        return self

    def _isub(self, other: "ResourceBundle") -> "ResourceBundle":
        for r, q in other:
            self.amounts[r] = self.quantity(r) - q
        self._clean_zeroes()
        return self

    # Public mutating shortcut used by Transform/Transfer internals
    def add(self, other: "ResourceBundle", sign: int = 1) -> None:
        if sign not in (1, -1):
            raise ValueError("sign must be +1 or -1")
        (self._iadd if sign == 1 else self._isub)(other)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    def copy(self) -> "ResourceBundle":
        """Return a *shallow* copy (resource names are immutable strings)."""
        return ResourceBundle(dict(self.amounts))

    def __iter__(self) -> Iterator[tuple[str, int]]:  # pragma: no cover
        return iter(self.amounts.items())

    # prettier debug‑print
    def __repr__(self) -> str:  # pragma: no cover – cosmetic
        inner = ", ".join(f"{r}: {q}" for r, q in sorted(self.amounts.items()))
        return f"ResourceBundle({{{inner}}})"

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _clean_zeroes(self) -> None:
        """Drop any resources whose quantity has fallen to zero."""
        for r in [k for k, v in self.amounts.items() if v == 0]:
            del self.amounts[r]


# ---------------------------------------------------------------------------
# Convenience constants & factory
# ---------------------------------------------------------------------------
BASIC_RESOURCES: tuple[str, ...] = (
    "AvailableLand",
    "Water",
    "Population",
    "PopulationWaste",
    "MetallicElements",
    "Timber",
    "MetallicAlloys",
    "MetallicAlloysWaste",
    "Electronics",
    "ElectronicsWaste",
    "Housing",
    "HousingWaste",
)


def bundle(pairs: Iterable[tuple[str, int]] | Mapping[str, int]) -> ResourceBundle:
    """Shorthand: ``bundle({"Timber": 25, "Water": 5})`` or list of pairs."""
    if isinstance(pairs, Mapping):
        return ResourceBundle(dict(pairs))
    return ResourceBundle.from_pairs(pairs)