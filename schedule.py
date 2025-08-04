# schedule.py
from dataclasses import dataclass, field
from typing import List, Set
from actions import Action, TransformAction, TransferAction
from world import World

@dataclass
class Schedule:
    actions: List[Action] = field(default_factory=list)

    # utility helpers ---------------------------------------------------
    def extend(self, action: Action) -> "Schedule":
        return Schedule(self.actions + [action])

    def countries_involved(self) -> List[str]:
        seen: Set[str] = set()
        for a in self.actions:
            if isinstance(a, TransformAction):
                seen.add(a.country)
            elif isinstance(a, TransferAction):
                seen.update([a.src, a.dst])
        return list(seen)

    def apply(self, world: World) -> World:
        w = world.copy()
        for a in self.actions:
            a.apply(w)
        return w
