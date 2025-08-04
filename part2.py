# part2.py

import csv
import heapq
import logging
import itertools
from typing import List, Tuple, Dict

from world import World, load_world_from_csv
from parse_templates import load_templates, TransformTemplate
from state_quality import StateQuality
from metrics import expected_utility
from schedule import Schedule, Action
from actions import TransferAction

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def country_scheduler(
    your_country: str,
    resources_filename: str,
    initial_state_filename: str,
    templates_filename: str,
    output_schedule_filename: str,
    num_output_schedules: int,
    depth_bound: int,
    frontier_max_size: int,
    gamma: float = 0.9,
    failure_cost: float = -10.0,
    k: float = 1.0,
    x0: float = 0.0
):
    """
    Anytime, forward‐searching, depth‐bounded, utility‐driven scheduler.
    Writes the top `num_output_schedules` schedules (with per-step EU) to the output file.
    """
    # 1) Load data
    logger.info("Loading world state…")
    world = load_world_from_csv(initial_state_filename)

    logger.info("Loading transforms…")
    tpl_dict = load_templates(templates_filename)  # or point at your .tpl directory
    templates: List[TransformTemplate] = list(tpl_dict.values())

    logger.info(f"Loaded {len(templates)} transform templates: {[tpl.name for tpl in templates]}")
    acts0 = world.legal_actions(your_country, templates)
    logger.info(f"Initial legal_actions count for {your_country}: {len(acts0)}")

    logger.info("Loading weights & building StateQuality fn…")
    quality_fn = StateQuality.from_csv(resources_filename)
    world.attach_quality_fn(quality_fn)

    # 2) Frontier entries are tuples:
    #    (–EU_of_partial, Schedule obj, World obj, [EU_after_each_step])
    frontier: List[Tuple[float, Schedule, World, List[float]]] = []
    completed: List[Tuple[Schedule, List[float]]] = []
    counter = itertools.count()

    # initial EU (empty schedule)
    empty = Schedule([])
    initial_eu = expected_utility(
        schedule=empty,
        world=world,
        self_country=your_country,
        gamma=gamma,
        failure_cost=failure_cost,
        k=k,
        x0=x0
    )
    # push: negative so heapq is max‐heap by EU
    heapq.heappush(frontier, (-initial_eu, next(counter), empty, world, [initial_eu]))

        # 3) Anytime loop
    while frontier and len(completed) < num_output_schedules:
        # Pop best partial schedule
        neg_eu, _, sched, wstate, eus = heapq.heappop(frontier)
        current_eu = -neg_eu
        logger.info(f"Popped a schedule of depth={len(sched.actions)}, EU={current_eu:.4f}")

        # If at depth bound, record and continue
        if len(sched.actions) >= depth_bound:
            completed.append((sched, eus))
            continue

        # Generate successors (forward, singleton TRANSFER & TRANSFORM)
        for act in wstate.legal_actions(your_country, templates):
                # —— A) FILTER 1: no back-to-back identical actions —— 
                if sched.actions and act == sched.actions[-1]:
                    continue

                # build the new candidate schedule
                new_sched = sched.extend(act)

                # compute the EU if we did this action
                try:
                    eu_new = expected_utility(
                        schedule=new_sched,
                        world=wstate,
                        self_country=your_country,
                        gamma=gamma,
                        failure_cost=failure_cost,
                        k=k,
                        x0=x0
                    )
                except ValueError:
                    # not enough resources / invalid, skip
                    continue

                # —— B) FILTER 2: skip if intermediate EU is too bad —— 
                # for example, don’t let EU drop below -2.0 at any intermediate step
                if eu_new < -2.0:
                    continue

                # now actually apply it once
                new_world = wstate.copy()
                new_world.apply_action(act)

                new_eus = eus + [eu_new]
                heapq.heappush(
                    frontier,
                    (-eu_new, next(counter), new_sched, new_world, new_eus)
                )
        # 4) If we have enough completed schedules, stop
        if len(frontier) > frontier_max_size:
            # keep only top‐beam items
            frontier = heapq.nsmallest(frontier_max_size, frontier)
            heapq.heapify(frontier)
    logger.info(f"Completed {len(completed)} schedules, frontier size: {len(frontier)}")
            

    # 4) Write out the completed schedules
    with open(output_schedule_filename, "w", newline="") as outf:
        writer = csv.writer(outf)
        writer.writerow(["Schedule", "Step_EUs"])
        for sched, eus in completed:
            # flatten actions into their Lisp‐style strings
            acts_str = " | ".join(str(a) for a in sched.actions)
            eus_str  = ";".join(f"{u:.4f}" for u in eus)
            writer.writerow([acts_str, eus_str])

    logger.info(f"Wrote {len(completed)} schedules to {output_schedule_filename}")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("your_country")
    p.add_argument("resources_csv")
    p.add_argument("initial_state_csv")
    p.add_argument("templates_file")
    p.add_argument("output_csv")
    p.add_argument("--n",   type=int, default=5)
    p.add_argument("--depth", type=int, default=6)
    p.add_argument("--beam",  type=int, default=50)
    p.add_argument("--gamma", type=float, default=0.9)
    p.add_argument("--cost",  type=float, default=-10.0)
    p.add_argument("--k",     type=float, default=1.0)
    p.add_argument("--x0",    type=float, default=0.0)
    args = p.parse_args()

    country_scheduler(
        args.your_country,
        args.resources_csv,
        args.initial_state_csv,
        args.templates_file,
        args.output_csv,
        args.n,
        args.depth,
        args.beam,
        args.gamma,
        args.cost,
        args.k,
        args.x0,
    )
