# CS 5260 Programming Project 1: Multi-Method AI Agent for Resource Trading

## Overview

This repository implements **Part 1** of the CS 5260 Programming Project: you build a pipeline that:

1. **Parses** an initial world state (CSV) and transform templates (Lisp-style `.tpl` files).  
2. Defines a **State Quality** function \(`Q(c)`\) that scores each country’s resource bundle.  
3. Computes **Expected Utility** (EU) of candidate schedules (`TRANSFER` + `TRANSFORM` operations) using:
   - Undiscounted Reward  
   - Discounted Reward with factor γ  
   - Logistic acceptance probabilities  
   - Failure cost penalty  
4. Runs a best-first search (beam/A\*) to find the schedule that maximizes EU for a designated “self” country.

When you run `python main.py --world data/init_world.csv --templates transform_templates/core.tpl --weights data/weights.csv --self "whatever world you choose from init_world"`, it prints:

- **Initial EU** (doing nothing)  
- **Best Schedule** (sequence of actions)  
- **Final world snapshot** for your country  
- **Best EU**

- Example Output:

INFO:root:Loading initial world state …
INFO:root:Parsing transformation templates …
INFO:root:Initialising State Quality function …
INFO:root:Starting search (max_depth=6, beam_width=50) …
INFO:search:Initial EU for Atlantis: 0.0000
INFO:root:Search complete – best EU = 0.000

=== Best Schedule ===

Expected Utility for Atlantis: 0.000

Final world snapshot (truncated):
  Atlantis: {'AvailableLand': 400, 'Electronics': 5, 'Housing': 20, 'MetallicAlloys': 10, 'MetallicElements': 50, 'Population': 100, 'Timber': 200, 'Water': 300}

---

## Repository Layout

├── README.md ← this file
├── main.py ← CLI entry point
├── state_quality.py ← loads weights.csv & defines Q()
├── metrics.py ← reward, discounted reward, acceptance, EU
├── world.py ← World, Country, legal_actions, loader
├── parse_templates.py ← Lisp-style .tpl → TransformTemplate
├── schedule.py ← Schedule + Action classes
├── search.py ← SearchEngine + best_schedule()
├── resources.py ← ResourceBundle helper
├── country.py ← Country model (apply_transform, transfer)
├── actions.py ← TransformAction, TransferAction
├── transform_templates/ ← your .tpl files here
│ └── core.tpl
└── data/
├── init_world.csv ← initial world-state CSV (must be populated)
└── weights.csv ← resource,weight,baseline


---

## Prerequisites

- **Python 3.8+**  
- Dependencies (only standard library modules: `csv`, `heapq`, `logging`, `argparse`, `dataclasses`, `typing`)

---

## Installation

1. Clone this repo:
   ```bash
   git clone https://github.com/KyleSanchezVanderbilt/CS5260-Project1.git
   cd CS5260-Project1

## OPTIONAL  Create and activate a virtual environment:

python -m venv venv
source venv/bin/activate    # macOS/Linux
venv\Scripts\activate       # Windows

Usage
1. Populate data/init_world.csv
Your CSV must have a header row:

Country,Population,MetallicElements,Timber,Water,AvailableLand,MetallicAlloys,Housing,Electronics
Atlantis,100,50,200,300,400,10,20,5
Carpania, 80,40,180,250,350, 8,15,3
Dinotopia,120,60,220,330,450,12,25,6

2. Define data/weights.csv
Comma-separated, no blank lines:

resource,weight,baseline
Food,2.0,675.2
Housing,1.0,0.29
MetallicElements,1.3,0.375
Timber,1.2,0.5
MetallicAlloys,1.5,0.219
Electronics,0.8,7.3
Water,0.5,580
PotentialFossilEnergyUsable,1.0,79
PotentialRenewableEnergyUsable,1.0,21394
FoodWaste,-1.0,74

3. Supply .tpl files
Put all your transformation templates in transform_templates/, e.g. core.tpl.

4. Run the search

python main.py \
  --world     data/init_world.csv \
  --templates transform_templates/core.tpl \
  --weights   data/weights.csv \
  --self      Atlantis \
  --max-depth 6 \
  --beam-width 50 \
  --gamma     0.9 \
  --failure-cost -10 \
  --k         1.0 \
  --x0        0


--world: path to your initial world CSV

--templates: path to one .tpl or directory of .tpl files

--weights: path to your weights CSV

--self: the country name whose EU you’re optimizing

Search parameters:

--max-depth (int): max number of actions in a schedule

--beam-width (int): frontier size for beam/A* search

--gamma (float): discount factor (0 ≤ γ < 1)

--failure-cost (float): EU penalty if schedule fails

--k (float): logistic steepness for acceptance probability

--x0 (float): logistic midpoint (neutral DR)

## Getting Non-Zero Schedules
If your search returns EU = 0 and the empty schedule, try one or more of the following:

1. Adjust resource weights / baselines

In data/weights.csv, increase positive weights (weight column) on desired outputs

lower baselines so that small outputs look more valuable

2. Tweak heuristic parameters

Raise γ (e.g. 0.95–0.99) so longer chains aren’t overly penalized

Reduce failure cost (e.g. –5) so low-risk gains become worthwhile

3. Expand search capacity

Steepen logistic (--k 1.5) to favor higher-DR actions

--max-depth 8 --beam-width 100

Allows longer, multi-step production chains.

4. Add or refine transforms

Edit transform_templates/*.tpl to include new processing steps (e.g., recycling)

Ensure each template’s net inputs vs. outputs can yield ΔQ>0 under some scale k.

5. Customize StateQuality

In state_quality.py, change the scoring formula: include additional resource factors, nonlinear terms, or per‐land/ecological normalization.

After each tweak, rerun the command above and inspect the printed Best Schedule and Final snapshot to see which actions your AI now prefers.


Contact & License
© 2025 Kyle Sanchez. MIT License.
Feel free to open issues or pull requests to improve templates, the quality function, or search heuristics!