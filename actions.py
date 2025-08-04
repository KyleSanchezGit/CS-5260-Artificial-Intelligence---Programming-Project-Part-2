# actions.py
from dataclasses import dataclass
from resources import ResourceBundle
from parse_templates import TransformTemplate
from typing import Dict, List

class Action:                      # base type
    def apply(self, world): ...    # every subclass must implement

@dataclass
class TransformAction(Action):
    country: str
    template: TransformTemplate
    scale: int = 1

    def apply(self, world):
        world.get_country(self.country).apply_transform(self.template, self.scale)

    def __str__(self):
        return f"(TRANSFORM {self.country} {self.template.name} x{self.scale})"

@dataclass
class TransferAction(Action):
    src: str
    dst: str
    payload: Dict[str, int]        # e.g. {"Timber": 5}

    def apply(self, world):
        bundle = ResourceBundle(self.payload)
        world.get_country(self.src).apply_transfer(world.get_country(self.dst), bundle)

    def __str__(self):
        res, qty = next(iter(self.payload.items()))
        return f"(TRANSFER {self.src} {self.dst} ({res} {qty}))"
