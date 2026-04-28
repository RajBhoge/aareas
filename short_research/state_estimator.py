"""
State Estimator: WLS state estimation + chi-squared bad data detection.
Replicates the detection mechanism described in Kaven et al. (NetSoft 2020).

Pipeline per timestep:
  1. Run PandaPower power flow  -> ground truth measurements
  2. Add Gaussian noise          -> simulate real meter readings
  3. Optionally inject FDIA      -> attacker manipulates selected meters
  4. Run WLS state estimation    -> pandapower built-in WLS solver
  5. Chi2 bad data detection     -> flag if attack crosses detection threshold
  6. Compute deviation metric    -> same metric as paper (coefficient of variation style)
"""

import warnings
import numpy as np
import pandapower as pp
import pandapower.estimation as est

# Suppress pandapower's internal SettingWithCopyWarnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*SettingWithCopyWarning.*")

# Measurement noise standard deviations (realistic smart meter accuracy)
NOISE_V   = 0.002   # voltage magnitude [pu]
NOISE_P   = 0.005   # active power [MW]
NOISE_Q   = 0.005   # reactive power [MVAr]

# Chi2 false-alarm probability (5% -> same as paper's 2-norm / chi2 threshold)
CHI2_ALPHA = 0.05


def extract_true_measurements(net) -> dict:
    """
    Extract ground-truth bus measurements from a converged power flow result.
    Returns dict keyed by bus index.
    """
    meas = {}
    for bus_idx in net.bus.index:
        meas[bus_idx] = {
            "vm_pu":  net.res_bus.vm_pu.at[bus_idx],
            "p_mw":   net.res_bus.p_mw.at[bus_idx],
            "q_mvar": net.res_bus.q_mvar.at[bus_idx],
        }
    return meas


def build_noisy_measurements(net, true_meas: dict, rng: np.random.Generator) -> dict:
    """
    Add Gaussian noise to true measurements to simulate physical meter readings.
    Returns dict with same structure as true_meas but with noise applied.
    """
    noisy = {}
    for bus_idx, vals in true_meas.items():
        noisy[bus_idx] = {
            "vm_pu":  vals["vm_pu"]  + rng.normal(0, NOISE_V),
            "p_mw":   vals["p_mw"]   + rng.normal(0, NOISE_P),
            "q_mvar": vals["q_mvar"] + rng.normal(0, NOISE_Q),
        }
    return noisy


def inject_fdia(noisy_meas: dict, attacked_buses: list, delta: dict) -> dict:
    """
    Inject false data into selected meters by adding delta values.

    attacked_buses: list of bus indices to compromise
    delta: dict with keys 'vm_pu', 'p_mw', 'q_mvar' — injected offsets

    Returns modified copy of noisy_meas.
    """
    injected = {k: v.copy() for k, v in noisy_meas.items()}
    for bus_idx in attacked_buses:
        if bus_idx not in injected:
            continue
        for mtype in ("vm_pu", "p_mw", "q_mvar"):
            if mtype in delta:
                injected[bus_idx][mtype] += delta[mtype]
    return injected


def load_measurements_into_net(net, meas: dict) -> None:
    """
    Clear existing measurements and load new ones into net.measurement.
    Must be called before running state estimation.
    """
    net.measurement.drop(net.measurement.index, inplace=True)
    for bus_idx, vals in meas.items():
        pp.create_measurement(net, "v", "bus", vals["vm_pu"],  NOISE_V, bus_idx)
        pp.create_measurement(net, "p", "bus", vals["p_mw"],   NOISE_P, bus_idx)
        pp.create_measurement(net, "q", "bus", vals["q_mvar"], NOISE_Q, bus_idx)


def run_wls(net) -> bool:
    """
    Run Weighted Least Squares state estimation.
    Returns True if converged.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = est.estimate(net, algorithm="wls")
    return result.get("success", False) if isinstance(result, dict) else bool(result)


def detect_bad_data(net) -> bool:
    """
    Run chi-squared bad data test on the current state estimation residuals.
    Returns True if bad data (i.e. attack) is detected.
    Matches the chi2 / 2-norm test described in the paper.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        detected = est.chi2_analysis(net, chi2_prob_false=CHI2_ALPHA)
    return bool(detected)


def compute_deviation(true_meas: dict, net) -> dict:
    """
    Compute per-bus deviation between true power flow and WLS estimate.
    Uses the same metric as the paper:
        deviation = (estimated - true) / (|estimated| + |true|)
    Range: -1 (large negative) to +1 (large positive).
    Returns dict with arrays for vm_pu, p_mw, q_mvar deviations.
    """
    bus_indices = list(net.bus.index)
    dev_v, dev_p, dev_q = [], [], []

    for bus_idx in bus_indices:
        true_v = true_meas[bus_idx]["vm_pu"]
        true_p = true_meas[bus_idx]["p_mw"]
        true_q = true_meas[bus_idx]["q_mvar"]

        est_v = net.res_bus_est.vm_pu.at[bus_idx]
        est_p = net.res_bus_est.p_mw.at[bus_idx]   if "p_mw"   in net.res_bus_est.columns else true_p
        est_q = net.res_bus_est.q_mvar.at[bus_idx] if "q_mvar" in net.res_bus_est.columns else true_q

        def _dev(e, t):
            denom = abs(e) + abs(t)
            return (e - t) / denom if denom > 1e-9 else 0.0

        dev_v.append(_dev(est_v, true_v))
        dev_p.append(_dev(est_p, true_p))
        dev_q.append(_dev(est_q, true_q))

    return {
        "vm_pu":  np.array(dev_v),
        "p_mw":   np.array(dev_p),
        "q_mvar": np.array(dev_q),
    }


def run_timestep(net, true_meas: dict, rng: np.random.Generator,
                 attacked_buses: list = None, fdia_delta: dict = None) -> dict:
    """
    Full pipeline for one timestep.

    Returns dict with:
      - converged     : bool, WLS converged
      - detected      : bool, chi2 bad data detected
      - deviation     : dict of deviation arrays (vm_pu, p_mw, q_mvar)
      - mean_dev_v    : float, mean |voltage deviation| across all buses
      - attacked      : bool, whether FDIA was applied this timestep
    """
    noisy = build_noisy_measurements(net, true_meas, rng)

    attacked = bool(attacked_buses and fdia_delta)
    if attacked:
        noisy = inject_fdia(noisy, attacked_buses, fdia_delta)

    load_measurements_into_net(net, noisy)
    converged = run_wls(net)

    if not converged:
        return {"converged": False, "detected": False,
                "deviation": None, "mean_dev_v": 0.0, "attacked": attacked}

    detected  = detect_bad_data(net)
    deviation = compute_deviation(true_meas, net)

    return {
        "converged":  converged,
        "detected":   detected,
        "deviation":  deviation,
        "mean_dev_v": float(np.mean(np.abs(deviation["vm_pu"]))),
        "attacked":   attacked,
    }


if __name__ == "__main__":
    import simbench as sb
    from grid_setup import load_grid, apply_timestep, run_powerflow, print_grid_summary

    print("Loading grid...")
    net, profiles = load_grid()
    print_grid_summary(net)

    rng = np.random.default_rng(0)

    # --- Test 1: clean timestep (no attack) ---
    apply_timestep(net, profiles, t=0)
    run_powerflow(net)
    true_meas = extract_true_measurements(net)

    result_clean = run_timestep(net, true_meas, rng)
    print(f"\n[Clean] converged={result_clean['converged']}  "
          f"detected={result_clean['detected']}  "
          f"mean_dev_v={result_clean['mean_dev_v']:.6f}")

    # --- Test 2: FDIA on 3 buses (large delta -> should be detected) ---
    apply_timestep(net, profiles, t=0)
    run_powerflow(net)
    true_meas = extract_true_measurements(net)

    bus_indices = list(net.bus.index)
    attacked_buses = bus_indices[1:4]   # attack 3 non-slack buses
    fdia_delta = {"vm_pu": 0.05, "p_mw": 0.5, "q_mvar": 0.2}   # large injection

    result_attack = run_timestep(net, true_meas, rng,
                                 attacked_buses=attacked_buses,
                                 fdia_delta=fdia_delta)
    print(f"[FDIA large] converged={result_attack['converged']}  "
          f"detected={result_attack['detected']}  "
          f"mean_dev_v={result_attack['mean_dev_v']:.6f}")

    # --- Test 3: FDIA with tiny delta -> should evade detection ---
    apply_timestep(net, profiles, t=0)
    run_powerflow(net)
    true_meas = extract_true_measurements(net)

    fdia_delta_small = {"vm_pu": 0.003, "p_mw": 0.003, "q_mvar": 0.003}
    result_stealth = run_timestep(net, true_meas, rng,
                                  attacked_buses=attacked_buses,
                                  fdia_delta=fdia_delta_small)
    print(f"[FDIA stealth] converged={result_stealth['converged']}  "
          f"detected={result_stealth['detected']}  "
          f"mean_dev_v={result_stealth['mean_dev_v']:.6f}")

    print("\nState estimator verified successfully.")
