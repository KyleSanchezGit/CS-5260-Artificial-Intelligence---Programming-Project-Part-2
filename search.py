# search.py
import heapq
import logging
from typing import List, Tuple, Dict, Any

from world import World
from schedule import Schedule
from metrics import expected_utility
from parse_templates import TransformTemplate

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class SearchEngine:
    def __init__(
        self,
        *,
        self_country: str,
        transforms: List[TransformTemplate],
        quality_fn: Any,
        gamma: float,
        failure_cost: float,
        logistic_k: float,
        logistic_x0: float,
        max_depth: int,
        beam_width: int
    ):
        self.self_country = self_country
        self.transforms   = transforms
        self.quality_fn   = quality_fn
        self.gamma        = gamma
        self.failure_cost = failure_cost
        self.logistic_k   = logistic_k
        self.logistic_x0  = logistic_x0
        self.max_depth    = max_depth
        self.beam_width   = beam_width

    def find_best_schedule(self, world: World) -> Tuple[Schedule, World, float]:
        sched, best_eu = best_schedule(
            initial_world=world,
            self_country=self.self_country,
            transforms=self.transforms,
            max_steps=self.max_depth,
            gamma=self.gamma,
            failure_cost=self.failure_cost,
            k=self.logistic_k,
            x0=self.logistic_x0
        )
        final_world = sched.apply(world)
        return sched, final_world, best_eu


def best_schedule(
    initial_world: World,
    self_country:    str,
    transforms:      List[TransformTemplate],
    max_steps:       int   = 5,
    gamma:           float = 0.9,
    failure_cost:    float = -10.0,
    k:               float = 1.0,
    x0:              float = 0.0
) -> Tuple[Schedule, float]:
    """
    Best-first search to maximize Expected Utility for self_country.
    Returns (best_schedule, best_eu).
    """

    # Priority queue of (-EU, WorldState, Schedule)
    frontier: List[Tuple[float, World, Schedule]] = []

    # 1) Utility of doing nothing
    empty_sched = Schedule([])
    start_eu = expected_utility(
        schedule=empty_sched,
        world=initial_world,
        self_country=self_country,
        gamma=gamma,
        failure_cost=failure_cost,
        k=k,
        x0=x0
    )
    heapq.heappush(frontier, (-start_eu, initial_world.copy(), empty_sched))

    visited: Dict[Tuple[Any,int], float] = {}
    best_sched = empty_sched
    best_eu    = start_eu
    logger.info(f"Initial EU for {self_country}: {start_eu:.4f}")

    # 2) Expand frontier
    while frontier:
        neg_eu, world_state, sched = heapq.heappop(frontier)
        current_eu = -neg_eu

        # Update best
        if current_eu > best_eu:
            best_eu    = current_eu
            best_sched = sched
            logger.info(f"New best EU {best_eu:.4f} at depth {len(sched.actions)}")

        # Depth cutoff
        if len(sched.actions) >= max_steps:
            continue

        # Generate next actions
        for action in world_state.legal_actions(self_country, transforms):
            next_world = world_state.copy()
            try:
                next_world.apply_action(action)
            except Exception:
                continue

            next_sched = sched.extend(action)
            eu_val = expected_utility(
                schedule=next_sched,
                world=next_world,
                self_country=self_country,
                gamma=gamma,
                failure_cost=failure_cost,
                k=k,
                x0=x0
            )

            key = (next_world.signature(), len(next_sched.actions))
            if visited.get(key, float('-inf')) < eu_val:
                visited[key] = eu_val
                heapq.heappush(frontier, (-eu_val, next_world, next_sched))

    return best_sched, best_eu