"""
Adaptive FDIA Attacker — core novel contribution.

Fills the gap left by Kaven et al. (NetSoft 2020):
  - Their attacker: random meter selection, manually pre-computed injection boundaries.
  - Our attacker:   learns detection boundaries through probing, then selects the
                    meter subset that maximises grid impact while staying undetected.

Two components:
  1. BoundaryProber  — binary-search probing to discover the chi2 detection threshold.
  2. MeterSelector   — greedy search for the meter subset with highest voltage impact.

Three-phase execution:
  PROBE  -> binary search for chi2 boundary (detections expected and intentional)
  SELECT -> greedy meter selection at the learned safe delta
  EXPLOIT-> sustained attack; re-probe only if exploit detection rate spikes hard
"""

import numpy as np
from dataclasses import dataclass
from enum import Enum, auto

from state_estimator import run_timestep, extract_true_measurements


class Phase(Enum):
    PROBE   = auto()
    SELECT  = auto()
    EXPLOIT = auto()


@dataclass
class AttackResult:
    phase: str
    attacked_buses: list
    delta: float
    detected: bool
    mean_dev_v: float
    converged: bool


class BoundaryProber:
    """
    Binary-search over injection magnitude delta to find where chi2 fires.

    SAFETY_MARGIN: back off to this fraction of lo (last safe delta) so
    we stay reliably below the threshold despite measurement noise.
    """

    SAFETY_MARGIN   = 0.50    # conservative: use 50% of last-safe delta
    MIN_DELTA       = 0.001
    MAX_DELTA       = 0.20
    CONVERGENCE_GAP = 0.002   # stop when hi-lo < this

    def __init__(self):
        self.lo        = self.MIN_DELTA
        self.hi        = self.MAX_DELTA
        self._best_lo  = self.MIN_DELTA   # highest confirmed non-detected delta
        self.converged = False
        self._first    = True

    def next_delta(self) -> float:
        if self._first:
            return self.MIN_DELTA * 3     # conservative first probe
        return (self.lo + self.hi) / 2.0

    def record(self, delta: float, detected: bool) -> None:
        self._first = False
        if detected:
            self.hi = delta
        else:
            self.lo      = delta
            self._best_lo = delta

        if (self.hi - self.lo) < self.CONVERGENCE_GAP:
            self.converged = True

    @property
    def safe_delta(self) -> float:
        # stay conservatively below the boundary
        return max(self._best_lo * self.SAFETY_MARGIN, self.MIN_DELTA)


class MeterSelector:
    """
    Greedy meter subset selection maximising voltage deviation
    subject to the chi2 detector not firing.
    """

    def __init__(self, max_meters: int = 6):
        self.max_meters  = max_meters
        self.best_subset: list = []
        self.done = False

    def run(self, net, profiles, t: int, candidates: list,
            safe_delta: float, rng: np.random.Generator) -> list:
        from grid_setup import apply_timestep, run_powerflow

        delta = {"vm_pu": safe_delta,
                 "p_mw":  safe_delta * 10,
                 "q_mvar": safe_delta * 5}

        # Score each candidate meter solo
        solo = {}
        for bus in candidates:
            apply_timestep(net, profiles, t)
            run_powerflow(net)
            true_meas = extract_true_measurements(net)
            r = run_timestep(net, true_meas, rng,
                             attacked_buses=[bus], fdia_delta=delta)
            solo[bus] = r["mean_dev_v"] if (r["converged"] and not r["detected"]) else 0.0

        ranked = sorted(solo, key=lambda b: solo[b], reverse=True)

        # Greedy expansion
        selected   = []
        best_score = 0.0
        for bus in ranked:
            if len(selected) >= self.max_meters:
                break
            trial = selected + [bus]
            apply_timestep(net, profiles, t)
            run_powerflow(net)
            true_meas = extract_true_measurements(net)
            r = run_timestep(net, true_meas, rng,
                             attacked_buses=trial, fdia_delta=delta)
            if r["converged"] and not r["detected"] and r["mean_dev_v"] >= best_score:
                selected   = trial
                best_score = r["mean_dev_v"]

        self.best_subset = selected if selected else [ranked[0]]
        self.done = True
        return self.best_subset


class AdaptiveAttacker:
    """
    Adaptive FDIA attacker combining boundary probing + optimal meter selection.

    Key difference from paper's baseline:
      - No pre-knowledge of detection thresholds required.
      - Meter selection is optimised for impact, not random.
      - Automatically re-calibrates when grid conditions shift.
    """

    REPROBE_THRESHOLD = 0.60   # only re-probe if >60% of recent exploit steps detected
    ROLLING_WINDOW    = 10

    def __init__(self, bus_indices: list, max_meters: int = 6, seed: int = 42):
        self.bus_indices = bus_indices
        self.candidates  = bus_indices[1:]   # exclude slack bus
        self.max_meters  = max_meters
        self.rng         = np.random.default_rng(seed)

        self.prober      = BoundaryProber()
        self.selector    = MeterSelector(max_meters)

        self.phase       = Phase.PROBE
        self.probe_bus   = self.candidates[0]
        self.safe_delta  = BoundaryProber.MIN_DELTA
        self.best_meters: list = []

        self.history: list[AttackResult] = []
        self._exploit_log: list[bool]    = []

    # ------------------------------------------------------------------
    def step(self, net, profiles, t: int) -> AttackResult:
        if self.phase == Phase.PROBE:
            r = self._probe_step(net, profiles, t)
        elif self.phase == Phase.SELECT:
            r = self._select_step(net, profiles, t)
        else:
            r = self._exploit_step(net, profiles, t)
            self._exploit_log.append(r.detected)
            window = self._exploit_log[-self.ROLLING_WINDOW:]
            if (len(window) == self.ROLLING_WINDOW
                    and sum(window) / len(window) > self.REPROBE_THRESHOLD):
                self._reset_probe()

        self.history.append(r)
        return r

    # ------------------------------------------------------------------
    def _probe_step(self, net, profiles, t: int) -> AttackResult:
        from grid_setup import apply_timestep, run_powerflow
        delta_val = self.prober.next_delta()
        delta     = {"vm_pu": delta_val, "p_mw": delta_val * 10, "q_mvar": delta_val * 5}
        apply_timestep(net, profiles, t)
        run_powerflow(net)
        true_meas = extract_true_measurements(net)
        r = run_timestep(net, true_meas, self.rng,
                         attacked_buses=[self.probe_bus], fdia_delta=delta)
        self.prober.record(delta_val, r["detected"])
        if self.prober.converged:
            self.safe_delta = self.prober.safe_delta
            self.phase      = Phase.SELECT
        return AttackResult("PROBE", [self.probe_bus], delta_val,
                            r["detected"], r["mean_dev_v"], r["converged"])

    def _select_step(self, net, profiles, t: int) -> AttackResult:
        best = self.selector.run(
            net, profiles, t, self.candidates, self.safe_delta, self.rng
        )
        self.best_meters = best
        self.phase = Phase.EXPLOIT
        delta_val  = self.safe_delta
        delta      = {"vm_pu": delta_val, "p_mw": delta_val * 10, "q_mvar": delta_val * 5}
        from grid_setup import apply_timestep, run_powerflow
        apply_timestep(net, profiles, t)
        run_powerflow(net)
        true_meas = extract_true_measurements(net)
        r = run_timestep(net, true_meas, self.rng,
                         attacked_buses=self.best_meters, fdia_delta=delta)
        return AttackResult("SELECT", self.best_meters, delta_val,
                            r["detected"], r["mean_dev_v"], r["converged"])

    def _exploit_step(self, net, profiles, t: int) -> AttackResult:
        from grid_setup import apply_timestep, run_powerflow
        delta_val = self.safe_delta
        delta     = {"vm_pu": delta_val, "p_mw": delta_val * 10, "q_mvar": delta_val * 5}
        apply_timestep(net, profiles, t)
        run_powerflow(net)
        true_meas = extract_true_measurements(net)
        r = run_timestep(net, true_meas, self.rng,
                         attacked_buses=self.best_meters, fdia_delta=delta)
        return AttackResult("EXPLOIT", self.best_meters, delta_val,
                            r["detected"], r["mean_dev_v"], r["converged"])

    def _reset_probe(self):
        self.prober   = BoundaryProber()
        self.selector = MeterSelector(self.max_meters)
        self.phase    = Phase.PROBE

    # ------------------------------------------------------------------
    def summary(self) -> dict:
        exploit = [r for r in self.history if r.phase == "EXPLOIT"]
        n_e     = len(exploit)
        return {
            "learned_safe_delta":          round(self.safe_delta, 5),
            "learned_meters":              self.best_meters,
            "n_meters_selected":           len(self.best_meters),
            "exploit_timesteps":           n_e,
            "exploit_detection_rate":      round(sum(r.detected for r in exploit) / n_e, 4) if n_e else 0,
            "mean_voltage_impact_exploit": round(float(np.mean([r.mean_dev_v for r in exploit])), 6) if exploit else 0,
        }


# ---------------------------------------------------------------------------

class RandomBaselineAttacker:
    """
    Paper baseline: random k meters, fixed delta from a manually estimated boundary.
    The fixed delta is intentionally slightly above the true chi2 threshold to
    represent a conservative but imprecise manual boundary calculation.
    """

    FIXED_DELTA_V = 0.010   # manual boundary estimate — above safe threshold
    FIXED_DELTA_P = 0.100
    FIXED_DELTA_Q = 0.050

    def __init__(self, bus_indices: list, n_meters: int = 6, seed: int = 99):
        self.candidates = bus_indices[1:]
        self.n_meters   = min(n_meters, len(self.candidates))
        self.rng        = np.random.default_rng(seed)
        self.history: list[AttackResult] = []

    def step(self, net, profiles, t: int) -> AttackResult:
        from grid_setup import apply_timestep, run_powerflow
        attacked = list(self.rng.choice(self.candidates, size=self.n_meters, replace=False))
        delta    = {"vm_pu": self.FIXED_DELTA_V,
                    "p_mw":  self.FIXED_DELTA_P,
                    "q_mvar": self.FIXED_DELTA_Q}
        apply_timestep(net, profiles, t)
        run_powerflow(net)
        true_meas = extract_true_measurements(net)
        r = run_timestep(net, true_meas, self.rng,
                         attacked_buses=attacked, fdia_delta=delta)
        result = AttackResult("RANDOM", attacked, self.FIXED_DELTA_V,
                              r["detected"], r["mean_dev_v"], r["converged"])
        self.history.append(result)
        return result

    def summary(self) -> dict:
        n = len(self.history)
        return {
            "n_meters":             self.n_meters,
            "fixed_delta":          self.FIXED_DELTA_V,
            "total_timesteps":      n,
            "detection_rate":       round(sum(r.detected for r in self.history) / n, 4) if n else 0,
            "mean_voltage_impact":  round(float(np.mean([r.mean_dev_v for r in self.history])), 6) if self.history else 0,
        }


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from grid_setup import load_grid, print_grid_summary

    print("Loading grid...")
    net, profiles = load_grid()
    print_grid_summary(net)
    bus_indices = list(net.bus.index)

    attacker = AdaptiveAttacker(bus_indices, max_meters=6, seed=42)
    print("\nRunning 40 timesteps of adaptive attacker...")
    for t in range(40):
        r = attacker.step(net, profiles, t)
        print(f"  t={t:02d} [{r.phase:7s}] delta={r.delta:.4f}  "
              f"meters={len(r.attacked_buses)}  "
              f"detected={str(r.detected):5}  dev_v={r.mean_dev_v:.5f}")

    print("\n--- Adaptive Summary ---")
    for k, v in attacker.summary().items():
        print(f"  {k}: {v}")
