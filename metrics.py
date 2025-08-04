# metrics.py
"""
Core metric computations for CS5260 AI agent:
 - logistic acceptance function
 - undiscounted and discounted rewards
 - schedule success probability
 - expected utility
"""

from __future__ import annotations
import math
from typing import Protocol, List, Any

__all__ = [
    "Schedule", "World", "logistic",
    "undiscounted_reward", "discounted_reward",
    "schedule_success_probability", "expected_utility",
]


class Schedule(Protocol):
    """Protocol for a sequence of actions in the simulation."""
    actions: List[Any]

    def countries_involved(self) -> List[str]:
        """Return the list of country names referenced."""
        ...

    def apply(self, world: World) -> World:
        """Execute this schedule on a copy of `world`, returning the new state."""
        ...


class World(Protocol):
    """Protocol representing the virtual world state."""
    def quality(self, country: str) -> float:
        """Compute and return the State Quality for `country`."""
        ...


def logistic(x: float, x0: float = 0.0, k: float = 1.0) -> float:
    """
    Logistic (sigmoid) function.

    Returns 1 / (1 + exp(-k * (x - x0))).
    """
    return 1.0 / (1.0 + math.exp(-k * (x - x0)))  # uses math.exp for numeric stability


def undiscounted_reward(start_q: float, end_q: float) -> float:
    """
    Undiscounted reward R = end_quality - start_quality.
    """
    return end_q - start_q


def discounted_reward(
    start_q: float,
    end_q: float,
    steps: int,
    gamma: float = 0.9
) -> float:
    """
    Discounted reward: gamma^steps * (end_q - start_q).

    Gamma in [0,1) controls how future gains are valued.
    """
    return (gamma ** steps) * (end_q - start_q)


def schedule_success_probability(
    schedule, world, gamma=0.9, k: float = 1.0, x0: float = 0.0
) -> float:
    """
    Compute P(success) = ∏ logistic(dr_i) over all countries involved.

    For each country i:
      dr_i = discounted_reward for country i,
      then apply logistic(dr_i) to get acceptance probability.
    """
    final_world = schedule.apply(world.copy())
    probs: List[float] = []
    for country in schedule.countries_involved():
        dr_i = discounted_reward(
            world.quality(country),
            final_world.quality(country),
            steps=len(schedule.actions),
            gamma=gamma
        )
        probs.append(logistic(dr_i, k=k, x0=x0))
    return math.prod(probs)  # product of individual acceptance probabilities


def expected_utility(schedule, world, self_country,
                      gamma=0.9, failure_cost=-10.0,
                      k: float = 1.0, x0: float = 0.0):
    """
    Expected Utility:
      EU = P(success) * DR(self) + (1 - P(success)) * failure_cost.

    Where DR(self) is the discounted reward for `self_country`.
    """
    start_q = world.quality(self_country)
    end_world = schedule.apply(world.copy())
    dr_self = discounted_reward(
        start_q,
        end_world.quality(self_country),
        steps=len(schedule.actions),
        gamma=gamma
    )
    p_succ = schedule_success_probability(schedule, world.copy(), gamma=gamma,
                                           k=k, x0=x0)
    return p_succ * dr_self + (1.0 - p_succ) * failure_cost
