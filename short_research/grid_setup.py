"""
Grid Setup: Load SimBench low-voltage grid into PandaPower.
Replicates the grid model used in Kaven et al. (4th KuVS FG NetSoft 2020).
"""

import pandapower as pp
import simbench as sb
import pandas as pd
import numpy as np


# SimBench grid code — 44-bus LV semi-urban grid, matches paper's 43 metering points
GRID_CODE = "1-LV-semiurb4--0-sw"


def load_grid(grid_code: str = GRID_CODE) -> tuple:
    """
    Load SimBench grid and its time-series load profiles.
    Returns (net, profiles) where profiles is a dict of DataFrames.
    """
    net = sb.get_simbench_net(grid_code)
    profiles = sb.get_absolute_values(net, profiles_instead_of_study_cases=True)
    return net, profiles


def apply_timestep(net, profiles: dict, t: int) -> None:
    """
    Apply load/generation values for timestep t to the network.
    Modifies net in-place.
    """
    for elm_type, profile_df in profiles.items():
        if elm_type not in net or profile_df.empty:
            continue
        elm_df = net[elm_type]
        for col in profile_df.columns:
            # col is (element_index, parameter) e.g. (0, 'p_mw')
            idx, param = col
            if idx in elm_df.index and param in elm_df.columns:
                elm_df.at[idx, param] = profile_df.at[t, col]


def get_measurements(net) -> dict:
    """
    Extract voltage magnitude, angle, active power, reactive power
    at all buses after a power flow run.
    Returns dict with arrays for each measurement type.
    """
    return {
        "vm_pu":    net.res_bus["vm_pu"].values.copy(),
        "va_deg":   net.res_bus["va_degree"].values.copy(),
        "p_mw":     net.res_bus["p_mw"].values.copy(),
        "q_mvar":   net.res_bus["q_mvar"].values.copy(),
    }


def run_powerflow(net) -> bool:
    """Run Newton-Raphson power flow. Returns True if converged."""
    try:
        pp.runpp(net, algorithm="nr", calculate_voltage_angles=True)
        return net["converged"]
    except Exception:
        return False


def print_grid_summary(net) -> None:
    print(f"Grid: {net['name'] if 'name' in net else GRID_CODE}")
    print(f"  Buses        : {len(net.bus)}")
    print(f"  Lines        : {len(net.line)}")
    print(f"  Loads        : {len(net.load)}")
    print(f"  Ext grids    : {len(net.ext_grid)}")
    sgen_count = len(net.sgen) if hasattr(net, 'sgen') else 0
    print(f"  Static gens  : {sgen_count}")
    print(f"  Metering pts : {len(net.bus)}  (one per bus, matching paper's setup)")


if __name__ == "__main__":
    print("Loading SimBench grid...")
    net, profiles = load_grid()
    print_grid_summary(net)

    # Test power flow at timestep 0
    apply_timestep(net, profiles, t=0)
    converged = run_powerflow(net)
    print(f"\nPower flow at t=0 converged: {converged}")

    if converged:
        meas = get_measurements(net)
        print(f"  Voltage range : {meas['vm_pu'].min():.4f} — {meas['vm_pu'].max():.4f} pu")
        print(f"  Active power  : {meas['p_mw'].sum():.4f} MW total")
        print("\nGrid setup verified successfully.")
