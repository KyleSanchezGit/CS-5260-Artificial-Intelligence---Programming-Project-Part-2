from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List
import copy
import csv
from resources import ResourceBundle

from country import Country
from parse_templates import TransformTemplate
from actions import TransformAction, TransferAction, Action

# world.py


@dataclass
class World:
    """
    Represents the global state: a collection of countries, each with its own resources.
    """
    countries: Dict[str, Country] = field(default_factory=dict)

    # … everything you already have in World …
    def __repr__(self) -> str:
        lines = ["World state:"]
        for name, country in self.countries.items():
            lines.append(f"  {name}: {country.resources.amounts}")
        return "\n".join(lines)

    

    def __init__(self, countries: dict[str, Country] = None):
        # allow both World() and World(countries_dict)
        self.countries = countries or {}

    def copy(self) -> World:
        """
        Return a deep copy of the world state to allow independent evolution of scenarios.
        """
        return copy.deepcopy(self)

    def get_country(self, name: str) -> Country:
        """
        Fetch a country by name, raising KeyError if not found.
        """
        try:
            return self.countries[name]
        except KeyError as e:
            raise KeyError(f"Country '{name}' not found in world.") from e

    def apply_action(self, action: Action) -> None:
        """
        Mutate this world by applying the given action (transform or transfer).
        Raises ValueError if preconditions are not met.
        """
        action.apply(self)

    def successor(self, action: Action) -> World:
        """
        Produce a new World instance that results from applying the action to a deep copy of the current state.
        """
        new_world = self.copy()
        new_world.apply_action(action)
        return new_world
    
    def legal_actions(
        self,
        country_name: str,
        transform_templates: List[TransformTemplate],
        allow_transfers: bool = True
    ) -> List[Action]:
        if transform_templates is None:
            transform_templates = []

        """
        Generate all legal actions for a given country:
        - Scaled TRANSFORM actions based on available resources.
        - Singleton TRANSFER actions to each other country for any resource with quantity > 0.
        """
        
        actions: List[Action] = []
        source = self.get_country(country_name)

        # TRANSFORM actions
        for tpl in transform_templates:
            max_scale = tpl.max_scale(source.resources)
            for scale in range(1, max_scale + 1):
                actions.append(TransformAction(country_name, tpl, scale))

        # TRANSFER actions (singleton transfers)
        if allow_transfers:
            for dst_name, dst in self.countries.items():
                if dst_name == country_name:
                    continue
                for resource, qty in source.resources.amounts.items():
                    if qty > 0:
                        # transfer one unit at a time
                        actions.append(TransferAction(country_name, dst_name, {resource: 1}))

        return actions
    
    # world.py  – inside class World
    # --------------------------------
    def attach_quality_fn(self, fn):
        """Attach a StateQuality instance so metrics.py can call world.quality()."""
        self._quality_fn = fn

    def quality(self, country_name: str) -> float:
        if not hasattr(self, "_quality_fn"):
            raise AttributeError("No StateQuality function attached to World")
        return self._quality_fn(self.get_country(country_name))
    
    # -- for duplicate-state detection in search.py ------------
    def signature(self) -> tuple:
        """Hashable snapshot of all country resources."""
        return tuple(
        (name, tuple(sorted(ctry.resources.amounts.items())))
        for name, ctry in sorted(self.countries.items())
    )

    def load_world_from_csv(path: str) -> "World":
        with open(path, newline='') as f:
            rdr = csv.DictReader(f)
            countries = {}
        for row in rdr:
            name = row.pop("Country")
            res = {k: int(v) for k, v in row.items() if v}
            countries[name] = Country(name, ResourceBundle(res))
        return World(countries)

        # -- pretty print used by main.py --------------------------
    def pretty(self, max_lines: int = 10) -> str:
        lines = []
        for idx, (name, c) in enumerate(sorted(self.countries.items())):
            if idx >= max_lines:
                lines.append("  …")
            break
        lines.append(f"  {name}: {dict(sorted(c.resources.amounts.items()))}")
        return "\n".join(lines)

# ==== end of class World ====

def load_world_from_csv(path: str) -> World:
    """
    Reads a CSV with header: Country,Resource1,Resource2,...
    and returns a World instance populated accordingly.
    """
    with open(path, newline="") as f:
        rdr = csv.DictReader(f)
        countries = {}
        for row in rdr:
            name = row.pop("Country")
            # convert all non-blank fields to int
            res = {k: int(v) for k, v in row.items() if v != ""}
            countries[name] = Country(name, ResourceBundle(res))
    return World(countries)

