# state_quality.py

import csv
from typing import Dict
from country import Country

class StateQuality:
    """
    Q(country) → float.  Loads (resource,weight,baseline) from CSV
    and computes a per-country score.
    """

    def __init__(self, weight: Dict[str, float], baseline: Dict[str, float]):
        self.weight   = weight
        self.baseline = baseline

    @classmethod
    def from_csv(cls, path: str) -> "StateQuality":
        w: Dict[str, float] = {}
        b: Dict[str, float] = {}
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                res = (row.get("resource") or "").strip()
                wt  = (row.get("weight")   or "").strip()
                bl  = (row.get("baseline") or "").strip()

                # skip any empty or malformed rows
                if not res or not wt or not bl:
                    continue

                try:
                    w_val = float(wt)
                    b_val = float(bl)
                except ValueError:
                    raise ValueError(f"Invalid number in weights.csv: {row}")

                w[res] = w_val
                b[res] = b_val

        if not w:
            raise ValueError("No valid weight lines found in weights.csv")

        return cls(w, b)

    def __call__(self, country: Country) -> float:
        # avoid divide-by-zero
        pop = max(country.resources.quantity("Population"), 1)
        score = 0.0
        for res, qty in country.resources.amounts.items():
            wt = self.weight.get(res, 0.0)
            bs = self.baseline.get(res, 0.0) * pop
            score += wt * (qty - bs)
        return score
