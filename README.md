# CS 5260 Programming Project

## Parts 1 & 2: Heuristic State Quality ＋ Anytime, Utility-Driven Scheduler

---

## 📄 Overview

This repository contains my implementation of the two‐part programming project for CS 5260:

1. **Part 1:** Define and compute a **State Quality** heuristic for any given country state.
2. **Part 2:** Build an **anytime**, forward‐searching, depth‐bounded, utility‐driven scheduler that generates sequences of `TRANSFORM` and `TRANSFER` actions to maximize **Expected Utility (EU)** for a “self” country.

Along the way, you’ll see how I translated the assignment spec into clean, abstract Python code, how I chose and justified every major design decision, and how to reproduce my experiments.

---

## 📂 Repository Layout

```
.
├── data/
│   ├── init_world.csv          # Initial world states (countries × resources)
│   └── weights.csv             # resource,weight,baseline per Part 1 spec
├── transform_templates/
│   └── core.tpl                # TRANSFORM templates (Housing, Alloys, Electronics)
├── part1/
│   ├── world.py                # World & Country model
│   ├── parse_templates.py      # Parse .tpl → TransformTemplate
│   ├── resources.py            # ResourceBundle & support
│   ├── country.py              # Country operations (transform/transfer)
│   ├── metrics.py              # Q(c), DR, logistic, schedule success & EU
│   └── main.py                 # CLI for Part 1 (compute EU for schedules)
├── part2/
│   ├── schedule.py             # Schedule & Action classes
│   ├── actions.py              # TransformAction, TransferAction
│   ├── search.py               # Beam‐search engine (utility‐driven)
│   └── part2.py                # CLI driver: country_scheduler(…)
├── Part2.pptx                  # Slides for Part 2 video presentation
├── VideoLink.txt               # Private link to my narrated demo
└── README.md                   # ← you are here
```

---

## 🛠️ Installation & Dependencies

1. **Python 3.9+** (I tested on 3.10 & 3.11)

2. Create & activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # macOS/Linux
   .venv\Scripts\activate         # Windows PowerShell
   ```

3. Install required packages:

   ```bash
   pip install -r requirements.txt
   ```


---

## 🚀 Usage

### Part 1: State Quality & EU Pipeline

```bash
cd part1
python main.py --world data/init_world.csv --templates transform_templates/core.tpl --weights data/weights.csv --self Atlantis
```

* **Output:**

  * Prints best schedule and final world snapshot.
  * Under the hood:

    1. Parses initial world & templates.
    2. Builds your custom `StateQuality` from weights.csv.
    3. Performs beam search on partial schedules, ranking by EU.

### Part 2: Anytime Scheduler

```bash
cd part2
python part2.py Atlantis data/weights.csv data/init_world.csv transform_templates/core.tpl output_schedules.csv --n 5 --depth 5 --beam 50 --gamma 0.98 --cost -5 --k 1.0 --x0 0
```

* **Arguments:**

  1. `your_country`
  2. `resources_csv`
  3. `initial_state_csv`
  4. `templates_file`
  5. `output_csv`
  6. `--n` (number of schedules)
  7. `--depth` (depth bound)
  8. `--beam` (beam width)
  9. `--gamma` (discount factor)
  10. `--cost` (failure cost, C)
  11. `--k`, `--x0` (logistic parameters)

* **Output:**

  * CSV with two columns: `Schedule,Step_EUs`.
  * Each row: one complete schedule (max depth = bound) plus the per‐step EU trace.

---

## 📐 Design Rationale

### 1. State Quality (Part 1)

$$
Q(c) \;=\; \frac{1}{\text{Population}_c}\;\sum_{r}
  w_r \,\bigl(A_r - b_r\cdot\text{Population}_c\bigr)
$$

* **Per‐capita normalization** avoids biasing large‐population countries.
* **Baseline $b_r$** drawn from real‐world per‐capita stats (e.g., UN data).
* **Weights $w_r$** reflect each resource’s economic/environmental importance.
* **Implementation:**

  * `StateQuality.from_csv(weights.csv)` builds `(w_r, b_r)` maps.
  * `world.attach_quality_fn(…)` stores it in each `Country`.

### 2. Action Abstraction

* Base class `Action` → two subclasses:

  * `TransformAction(country, template, scale)`
  * `TransferAction(src, dst, {res: qty})`
* **Benefit:** Uniform API (`.apply(world)`) and no “special‐case” hacks.

### 3. Expected Utility & Schedule Success

* **Discounted Reward:**
  $\displaystyle DR = \gamma^N \times \bigl(Q_{\text{end}} - Q_{\text{start}}\bigr)$
* **Acceptance Probability:** logistic over each participant’s DR
  $\sigma(x;k,x_0)=\tfrac{1}{1+e^{-k(x-x_0)}}$
* **EU formula:**
  $\displaystyle EU = P_{\mathrm{succ}}\cdot DR + (1 - P_{\mathrm{succ}})\cdot C$

### 4. Frontier & Beam Search (Part 2)

* **Heap entries:**

  ```python
  (-EU, counter, Schedule, World, [step_EUs])
  ```

  * Negative EU → max‐heap behavior.
  * `counter` ensures deterministic tie‐breaking.
* **Beam width** prunes frontier to top‐N EU candidates.
* **Anytime**: we keep searching until we collect `n` full‐depth schedules.

---

## 🔬 Experiments & Results

| Case | depth | beam | γ    | cost | found | best EU | notes                              |
| ---- | ----- | ---- | ---- | ---- | ----- | ------- | ---------------------------------- |
| 1    | 1     | 50   | 0.9  | –10  | 5     | +20.825 | Single‐step alloy transform wins   |
| 2    | 3     | 100  | 0.95 | –8   | 4     | +45.120 | 3‐step chain: timber→housing→trade |
| 3    | 6     | 200  | 0.98 | –5   | 3     | +78.360 | Full 6‐step electronics production |

* **Scatter Plot:** In the Part 2 slides you’ll see EU vs. discovery order.
* **Trade‐offs observed:**

  * ↑beam → deeper, varied plans but ↑runtime
  * ↑γ  → favors longer reward chains
  * Less negative `cost` → partial failures are less penalized, encouraging exploration

---

## ➕ Adding Your Own Test Cases

1. **Create** your new initial CSV (countries × resources) under `data/`.
2. **Invoke** Part 2 with your filenames:

   ```bash
   python part2.py MyLand \
     data/my_weights.csv \
     data/my_init.csv \
     transform_templates/core.tpl \
     my_output.csv \
     --n 5 --depth 4 --beam 80 --gamma 0.9 --cost -10
   ```
3. **Inspect** `my_output.csv` and record your findings in `test_cases_summary.pdf`.

---

## 📘 Lessons Learned & Future Work

* **Modularity** (Actions + Schedule + World) made it trivial to swap in new metrics or search strategies.
* **StateQuality tuning** (baselines & weights) drastically changes optimal plans—realistic data matters!
* **Next steps:**

  * Implement **macro‐operators** (common multi‐action sequences).
  * Model **renewable vs. nonrenewable** resources.
  * Extend to **multi‐country** coordinated planning.

---

*By reading this README and running the provided commands, you’ll reproduce every result, understand every trade‐off, and see exactly how the agent reasons step by step. Enjoy exploring countries of code!*
