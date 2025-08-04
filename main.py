#!/usr/bin/env python3
"""
main.py – Entry point for CS 5260 Programming Project (Part 1)
----------------------------------------------------------------
Runs a heuristic search that finds the schedule (sequence of TRANSFORM/TRANSFER
operations) with the highest Expected Utility for the designated “self” country.

The file intentionally depends only on the project’s own modules so it stays
portable.  Typical invocation:

    python main.py \
        --world data/init_world.csv \
        --templates transform_templates/core.tpl \
        --weights data/weights.csv \
        --self Atlantis \
        --max‑depth 6

Command‑line parameters let you experiment with γ, logistic‑curve settings,
beam width, etc.  All heavy lifting (state representation, schedule search,
metrics) lives in their respective modules – this script merely glues them
together.
"""
from __future__ import annotations

import argparse
import logging
import pathlib
import sys
from typing import List, Tuple

# --- Project‑internal imports -------------------------------------------------
# These modules must exist in SourceCode.zip; they follow the structure outlined
# in the architecture document.
from state_quality import StateQuality
from world import World, load_world_from_csv
from parse_templates import TransformTemplate
from parse_templates import load_templates
from search import SearchEngine, Schedule

# -----------------------------------------------------------------------------
# Argument parsing helpers
# -----------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Search for the best schedule given an initial world state."
    )
    p.add_argument(
        "--world",
        type=pathlib.Path,
        required=True,
        help="CSV file describing the initial world state (countries × resources)",
    )
    p.add_argument(
        "--templates",
        type=pathlib.Path,
        required=True,
        help="File containing (TRANSFORM …) templates in Lisp‑style syntax.",
    )
    p.add_argument(
        "--weights",
        type=pathlib.Path,
        required=True,
        help="CSV with resource,weight,baseline columns for State Quality.",
    )
    p.add_argument(
        "--self",
        default="self",
        help="Name of the country controlled by THIS AI agent.",
    )
    p.add_argument("--max-depth", type=int, default=6, help="Search depth limit.")
    p.add_argument(
        "--beam-width",
        type=int,
        default=50,
        help="If >0, perform beam search with this width; 0 ⇒ full A* search.",
    )
    p.add_argument("--gamma", type=float, default=0.9, help="Discount factor γ.")
    p.add_argument(
        "--failure-cost",
        type=float,
        default=-10.0,
        help="Constant C (utility if schedule negotiations fail).",
    )
    p.add_argument("--k", type=float, default=1.0, help="Logistic steepness k.")
    p.add_argument(
        "--x0", type=float, default=0.0, help="Logistic inflection point x₀."
    )
    p.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Python logging verbosity.",
    )
    return p


# -----------------------------------------------------------------------------
# Main driver
# -----------------------------------------------------------------------------

def run_search(args: argparse.Namespace) -> Tuple[Schedule, World, float]:
    """Load data, configure engine, and execute search.

    Returns a tuple (best_schedule, resulting_world, best_eu).
    """

    # 1. Input ----------------------------------------------------------------
    logging.info("Loading initial world state …")
    world: World = load_world_from_csv(args.world)

    quality_fn = StateQuality.from_csv(args.weights)
    world.attach_quality_fn(quality_fn)

    logging.info("Parsing transformation templates …")
    templates_dict = load_templates(args.templates)
    templates = list(templates_dict.values())

    logging.info("Initialising State Quality function …")
    quality_fn = StateQuality.from_csv(args.weights)

    # 2. Search engine setup ---------------------------------------------------
    engine = SearchEngine(
        self_country=args.self,
        transforms=templates,
        quality_fn=quality_fn,
        gamma=args.gamma,
        failure_cost=args.failure_cost,
        logistic_k=args.k,
        logistic_x0=args.x0,
        max_depth=args.max_depth,
        beam_width=args.beam_width,
    )

    # 3. Execute search --------------------------------------------------------
    logging.info(
        "Starting search (max_depth=%d, beam_width=%d) …",
        args.max_depth,
        args.beam_width,
    )
    best_schedule, best_world, best_eu = engine.find_best_schedule(world)
    logging.info("Search complete – best EU = %.3f", best_eu)
    return best_schedule, best_world, best_eu


def main(argv: List[str] | None = None) -> None:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    # Configure root logger ----------------------------------------------------
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="[%(levelname)s] %(message)s",
    )

    best_sched, final_world, eu = run_search(args)

    # 4. Pretty print results --------------------------------------------------
    print("\n=== Best Schedule ===")
    for idx, action in enumerate(best_sched.actions, start=1):
        print(f"{idx:02d}. {action}")

    print(f"\nExpected Utility for {args.self}: {eu:.3f}\n")
    print("Final world snapshot (truncated):")
    print(final_world.pretty())


if __name__ == "__main__":
    sys.exit(main())
