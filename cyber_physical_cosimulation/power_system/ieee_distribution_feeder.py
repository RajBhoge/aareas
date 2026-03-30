"""
IEEE Distribution Feeder Model for Cyber-Physical Co-Simulation
Implementation of IEEE 13-node and IEEE 34-node distribution feeders
with integrated solar PV systems for cyber-attack testing

Based on research proposal: "Cyber-Physical Co-Simulation for Smart Grid Security"
Target: Impact of Cyber-Induced False Data Injection on Solar-Rich Distribution Networks
"""

import pandapower as pp
import pandapower.networks as nw
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')


class IEEEDistributionFeeder:
    """
    IEEE Distribution Feeder model with solar PV integration
    Supports IEEE 13-node and IEEE 34-node test feeders
    """

    def __init__(self, feeder_type: str = "ieee13", solar_penetration: float = 0.3):
        """
        Initialize IEEE distribution feeder

        Args:
            feeder_type: Either "ieee13" or "ieee34"
            solar_penetration: Percentage of buses with solar PV (0.0-1.0)
        """
        self.feeder_type = feeder_type
        self.solar_penetration = solar_penetration
        self.net = None
        self.solar_systems = []
        self.baseline_results = {}
        self.attack_vulnerable_buses = []

        # VDE standard voltage limits (European standard)
        self.vde_voltage_limits = {
            'nominal_kv': 0.4,  # 400V European LV standard
            'lower_limit': 0.9,  # -10% (360V)
            'upper_limit': 1.1,  # +10% (440V)
            'critical_lower': 0.85,  # -15% critical
            'critical_upper': 1.15   # +15% critical
        }

    def create_ieee_feeder(self) -> pp.pandapowerNet:
        """Create IEEE distribution feeder network"""

        print(f"🔌 Creating {self.feeder_type.upper()} Distribution Feeder")

        if self.feeder_type == "ieee13":
            self.net = self._create_ieee13_feeder()
        elif self.feeder_type == "ieee34":
            self.net = self._create_ieee34_feeder()
        else:
            raise ValueError("Feeder type must be 'ieee13' or 'ieee34'")

        # Add solar PV systems to selected buses
        self._add_solar_pv_systems()

        # Run baseline power flow
        self._run_baseline_analysis()

        print(f"✅ {self.feeder_type.upper()} feeder created with {len(self.solar_systems)} solar PV systems")
        return self.net

    def _create_ieee13_feeder(self) -> pp.pandapowerNet:
        """Create IEEE 13-node test feeder with European voltage levels"""

        # Create empty network
        net = pp.create_empty_network()

        # Create buses (13 nodes) - European LV standard 400V
        bus_data = [
            (650, 4.16, "b"),   # Source bus - MV side
            (632, 4.16, "b"),   # Primary distribution
            (633, 0.4, "n"),    # European LV 400V
            (634, 0.4, "n"),    # European LV 400V
            (645, 0.4, "n"),    # European LV 400V
            (646, 0.4, "n"),    # European LV 400V
            (671, 4.16, "b"),   # MV distribution
            (680, 4.16, "b"),   # MV distribution
            (684, 0.4, "n"),    # European LV 400V
            (611, 0.4, "n"),    # European LV 400V
            (652, 0.4, "n"),    # European LV 400V
            (675, 0.4, "n"),    # European LV 400V
            (692, 0.4, "n"),    # European LV 400V
        ]

        bus_mapping = {}
        for i, (bus_id, vn_kv, bus_type) in enumerate(bus_data):
            pp_bus = pp.create_bus(net, vn_kv=vn_kv, name=f"Bus_{bus_id}")
            bus_mapping[bus_id] = pp_bus

        # External grid (utility connection)
        pp.create_ext_grid(net, bus=bus_mapping[650], vm_pu=1.0,
                          name="Utility_Grid")

        # Create distribution lines (typical European cable parameters)
        line_data = [
            (650, 632, 0.5, "NAYY_4x150"),    # MV feeder
            (632, 633, 0.2, "NAYY_4x95"),     # MV to LV
            (632, 645, 0.3, "NAYY_4x95"),     # MV to LV
            (632, 671, 0.4, "NAYY_4x150"),    # MV backbone
            (671, 680, 0.3, "NAYY_4x150"),    # MV backbone
            (671, 684, 0.2, "NAYY_4x50"),     # LV distribution
            (633, 634, 0.1, "NAYY_4x50"),     # LV local
            (645, 646, 0.08, "NAYY_4x35"),    # LV local
            (680, 611, 0.15, "NAYY_4x50"),    # LV distribution
            (684, 652, 0.25, "NAYY_4x35"),    # LV distribution
            (684, 675, 0.18, "NAYY_4x50"),    # LV distribution
            (675, 692, 0.12, "NAYY_4x35"),    # LV local
        ]

        # European standard cable types
        if "NAYY_4x150" not in net.std_types["line"]:
            pp.create_std_type(net, {"r_ohm_per_km": 0.208, "x_ohm_per_km": 0.080,
                               "c_nf_per_km": 250, "max_i_ka": 0.275},
                               name="NAYY_4x150", element="line")
        if "NAYY_4x95" not in net.std_types["line"]:
            pp.create_std_type(net, {"r_ohm_per_km": 0.320, "x_ohm_per_km": 0.085,
                               "c_nf_per_km": 210, "max_i_ka": 0.230},
                               name="NAYY_4x95", element="line")
        if "NAYY_4x50" not in net.std_types["line"]:
            pp.create_std_type(net, {"r_ohm_per_km": 0.640, "x_ohm_per_km": 0.090,
                               "c_nf_per_km": 180, "max_i_ka": 0.160},
                               name="NAYY_4x50", element="line")
        if "NAYY_4x35" not in net.std_types["line"]:
            pp.create_std_type(net, {"r_ohm_per_km": 0.868, "x_ohm_per_km": 0.095,
                               "c_nf_per_km": 165, "max_i_ka": 0.125},
                               name="NAYY_4x35", element="line")

        for from_bus, to_bus, length_km, std_type in line_data:
            pp.create_line(net,
                          from_bus=bus_mapping[from_bus],
                          to_bus=bus_mapping[to_bus],
                          length_km=length_km,
                          std_type=std_type,
                          name=f"Line_{from_bus}_{to_bus}")

        # Create European residential and commercial loads
        load_data = [
            (633, 15, 7.5, "Residential"),      # European residential: 15kW
            (634, 20, 10, "Residential"),       # European residential: 20kW
            (645, 25, 12, "Commercial"),        # Small commercial: 25kW
            (646, 18, 9, "Residential"),        # European residential: 18kW
            (684, 30, 15, "Commercial"),        # Commercial: 30kW
            (611, 12, 6, "Residential"),        # Small residential: 12kW
            (652, 22, 11, "Residential"),       # European residential: 22kW
            (675, 35, 17, "Commercial"),        # Commercial: 35kW
            (692, 28, 14, "Residential"),       # Large residential: 28kW
        ]

        for bus_id, p_kw, q_kvar, load_type in load_data:
            pp.create_load(net,
                          bus=bus_mapping[bus_id],
                          p_mw=p_kw/1000,  # Convert kW to MW
                          q_mvar=q_kvar/1000,  # Convert kVAR to MVAR
                          name=f"Load_{bus_id}_{load_type}")

        # Add step-down transformers for MV/LV connections (European standard)
        transformer_data = [
            (632, 633, 0.1, 4.16, 0.4),  # MV/LV transformer 100kVA
            (632, 645, 0.08, 4.16, 0.4), # MV/LV transformer 80kVA
            (671, 684, 0.12, 4.16, 0.4), # MV/LV transformer 120kVA
            (680, 611, 0.06, 4.16, 0.4), # MV/LV transformer 60kVA
        ]

        for hv_bus, lv_bus, sn_mva, vn_hv_kv, vn_lv_kv in transformer_data:
            pp.create_transformer(net,
                                hv_bus=bus_mapping[hv_bus],
                                lv_bus=bus_mapping[lv_bus],
                                std_type="25 MVA 110/20 kV",  # Will be adapted
                                name=f"Trafo_{hv_bus}_{lv_bus}")

        self.bus_mapping = bus_mapping
        return net

    def _create_ieee34_feeder(self) -> pp.pandapowerNet:
        """Create IEEE 34-node test feeder (simplified version)"""
        # For now, use the IEEE13 as baseline - can be extended later
        print("⚠️ IEEE34 feeder - using IEEE13 as baseline for initial implementation")
        return self._create_ieee13_feeder()

    def _add_solar_pv_systems(self):
        """Add solar PV systems to selected LV buses based on penetration level"""

        print(f"🌞 Adding Solar PV Systems (penetration: {self.solar_penetration:.1%})")

        # Get LV buses (400V buses suitable for solar connection)
        lv_buses = [bus for bus in self.net.bus.index
                    if self.net.bus.loc[bus, 'vn_kv'] == 0.4]

        # Select buses for solar installation
        n_solar = int(len(lv_buses) * self.solar_penetration)
        solar_buses = np.random.choice(lv_buses, size=min(n_solar, len(lv_buses)),
                                     replace=False)

        # European residential/commercial solar system sizes (10-50 kW as per proposal)
        solar_sizes_kw = [10, 15, 20, 25, 30, 35, 40, 45, 50]

        for bus in solar_buses:
            # Random solar system size in the specified range
            pv_size_kw = np.random.choice(solar_sizes_kw)

            # European solar PV typical specs
            # Power factor around 0.95 (slightly capacitive)
            pv_p_mw = pv_size_kw / 1000  # Convert to MW
            pv_q_mvar = -pv_p_mw * 0.33  # Capacitive reactive power

            # Create static generator (solar PV)
            sgen_idx = pp.create_sgen(self.net,
                                    bus=bus,
                                    p_mw=pv_p_mw,
                                    q_mvar=pv_q_mvar,
                                    name=f"Solar_PV_{pv_size_kw}kW_Bus{bus}",
                                    type="PV")

            # Store solar system info
            solar_info = {
                'bus': bus,
                'sgen_idx': sgen_idx,
                'size_kw': pv_size_kw,
                'p_mw': pv_p_mw,
                'q_mvar': pv_q_mvar,
                'inverter_id': f"INV_{bus}_{pv_size_kw}"
            }
            self.solar_systems.append(solar_info)

        print(f"✅ Added {len(self.solar_systems)} solar PV systems")
        for solar in self.solar_systems:
            print(f"   • Bus {solar['bus']}: {solar['size_kw']}kW PV (ID: {solar['inverter_id']})")

    def _run_baseline_analysis(self):
        """Run baseline power flow analysis and voltage stability check"""

        print("📊 Running Baseline Power Flow Analysis")

        try:
            # Run power flow
            pp.runpp(self.net, algorithm="nr", calculate_voltage_angles=True)

            # Extract results
            self.baseline_results = {
                'bus_voltages_pu': self.net.res_bus.vm_pu.copy(),
                'bus_voltages_kv': self.net.res_bus.vm_pu * self.net.bus.vn_kv,
                'bus_angles_deg': self.net.res_bus.va_degree.copy(),
                'line_loading_percent': self.net.res_line.loading_percent.copy(),
                'pf_converged': True
            }

            # Voltage stability analysis
            self._analyze_voltage_stability()

            print("✅ Baseline power flow completed successfully")

        except Exception as e:
            print(f"❌ Power flow failed: {e}")
            self.baseline_results['pf_converged'] = False

    def _analyze_voltage_stability(self):
        """Analyze voltage stability according to VDE standards"""

        print("⚡ Analyzing Voltage Stability (VDE Standards)")

        # Voltage analysis for LV buses (400V)
        lv_buses = self.net.bus[self.net.bus.vn_kv == 0.4].index

        voltage_analysis = {
            'within_limits': [],
            'warning_low': [],  # Between 0.85-0.9 pu
            'warning_high': [], # Between 1.1-1.15 pu
            'critical_low': [], # Below 0.85 pu
            'critical_high': [], # Above 1.15 pu
            'vulnerable_to_fdi': []
        }

        for bus in lv_buses:
            v_pu = self.baseline_results['bus_voltages_pu'][bus]

            # Categorize voltage levels
            if self.vde_voltage_limits['lower_limit'] <= v_pu <= self.vde_voltage_limits['upper_limit']:
                voltage_analysis['within_limits'].append(bus)
            elif self.vde_voltage_limits['critical_lower'] <= v_pu < self.vde_voltage_limits['lower_limit']:
                voltage_analysis['warning_low'].append(bus)
            elif self.vde_voltage_limits['upper_limit'] < v_pu <= self.vde_voltage_limits['critical_upper']:
                voltage_analysis['warning_high'].append(bus)
            elif v_pu < self.vde_voltage_limits['critical_lower']:
                voltage_analysis['critical_low'].append(bus)
            else:
                voltage_analysis['critical_high'].append(bus)

            # Identify buses vulnerable to FDI attacks
            # Buses close to voltage limits are more vulnerable
            voltage_margin = min(abs(v_pu - self.vde_voltage_limits['lower_limit']),
                               abs(v_pu - self.vde_voltage_limits['upper_limit']))

            if voltage_margin < 0.05:  # Within 5% of voltage limits
                voltage_analysis['vulnerable_to_fdi'].append(bus)

        self.baseline_results['voltage_analysis'] = voltage_analysis
        self.attack_vulnerable_buses = voltage_analysis['vulnerable_to_fdi']

        # Print analysis results
        print(f"   • Buses within VDE limits (0.9-1.1 pu): {len(voltage_analysis['within_limits'])}")
        print(f"   • Buses with voltage warnings: {len(voltage_analysis['warning_low']) + len(voltage_analysis['warning_high'])}")
        print(f"   • Buses vulnerable to FDI attacks: {len(voltage_analysis['vulnerable_to_fdi'])}")

        if voltage_analysis['vulnerable_to_fdi']:
            print(f"   ⚠️ FDI-vulnerable buses: {voltage_analysis['vulnerable_to_fdi']}")

    def get_solar_inverter_targets(self) -> List[Dict]:
        """Get list of solar inverters that can be targeted by FDI attacks"""

        targets = []
        for solar in self.solar_systems:
            target_info = {
                'inverter_id': solar['inverter_id'],
                'bus': solar['bus'],
                'size_kw': solar['size_kw'],
                'baseline_voltage_pu': self.baseline_results['bus_voltages_pu'][solar['bus']],
                'is_vulnerable': solar['bus'] in self.attack_vulnerable_buses,
                'attack_potential': self._calculate_attack_potential(solar['bus'])
            }
            targets.append(target_info)

        return targets

    def _calculate_attack_potential(self, bus: int) -> float:
        """Calculate attack potential for a bus (0-1 scale)"""

        if bus not in self.baseline_results['bus_voltages_pu']:
            return 0.0

        v_pu = self.baseline_results['bus_voltages_pu'][bus]

        # Distance from voltage center (1.0 pu)
        voltage_deviation = abs(v_pu - 1.0)

        # Distance from voltage limits
        lower_margin = v_pu - self.vde_voltage_limits['lower_limit']
        upper_margin = self.vde_voltage_limits['upper_limit'] - v_pu
        min_margin = min(lower_margin, upper_margin)

        # Attack potential: higher when voltage is already stressed
        # and margins to limits are small
        attack_potential = (voltage_deviation * 2) + (1 / (min_margin + 0.1))
        attack_potential = min(attack_potential / 5, 1.0)  # Normalize to 0-1

        return attack_potential

    def visualize_network(self, save_path: str = None):
        """Visualize the distribution network with solar PV systems"""

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

        # Plot 1: Network topology
        try:
            pp.plotting.simple_plot(self.net, ax=ax1, plot_loads=True,
                                   plot_gens=True, plot_sgens=True)
            ax1.set_title(f"IEEE Distribution Feeder - Network Topology\n"
                         f"{len(self.solar_systems)} Solar PV Systems", fontsize=12)
        except:
            ax1.text(0.5, 0.5, "Network plot not available", ha='center', va='center')
            ax1.set_title("Network Topology")

        # Plot 2: Voltage profile
        if 'bus_voltages_pu' in self.baseline_results:
            buses = self.net.bus.index
            voltages = [self.baseline_results['bus_voltages_pu'][b] for b in buses]

            # Color code by voltage level
            colors = []
            for v in voltages:
                if v < 0.9:
                    colors.append('red')    # Low voltage
                elif v > 1.1:
                    colors.append('orange') # High voltage
                elif 0.95 <= v <= 1.05:
                    colors.append('green')  # Good voltage
                else:
                    colors.append('yellow') # Acceptable voltage

            ax2.scatter(buses, voltages, c=colors, s=60, alpha=0.7)
            ax2.axhline(y=0.9, color='red', linestyle='--', alpha=0.7, label='VDE Lower Limit')
            ax2.axhline(y=1.1, color='red', linestyle='--', alpha=0.7, label='VDE Upper Limit')
            ax2.axhline(y=1.0, color='blue', linestyle='-', alpha=0.5, label='Nominal')

            ax2.set_xlabel('Bus Number')
            ax2.set_ylabel('Voltage (p.u.)')
            ax2.set_title('Voltage Profile - Baseline Conditions')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            ax2.set_ylim([0.85, 1.15])

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📈 Network visualization saved to {save_path}")

        return fig

    def export_network_data(self) -> Dict[str, Any]:
        """Export network data for co-simulation integration"""

        export_data = {
            'feeder_type': self.feeder_type,
            'solar_penetration': self.solar_penetration,
            'network_summary': {
                'total_buses': len(self.net.bus),
                'total_lines': len(self.net.line),
                'total_loads': len(self.net.load),
                'total_solar_systems': len(self.solar_systems),
                'lv_buses': len(self.net.bus[self.net.bus.vn_kv == 0.4])
            },
            'solar_systems': self.solar_systems,
            'inverter_targets': self.get_solar_inverter_targets(),
            'vulnerable_buses': self.attack_vulnerable_buses,
            'baseline_results': self.baseline_results,
            'vde_voltage_limits': self.vde_voltage_limits
        }

        return export_data


def main():
    """Test the IEEE distribution feeder implementation"""

    print("🔌 Testing IEEE Distribution Feeder for Cyber-Physical Co-Simulation")
    print("=" * 70)

    # Create IEEE 13-node feeder with 30% solar penetration
    feeder = IEEEDistributionFeeder(feeder_type="ieee13", solar_penetration=0.3)

    # Build the network
    net = feeder.create_ieee_feeder()

    # Get attack targets
    targets = feeder.get_solar_inverter_targets()

    print("\n🎯 Solar Inverter Attack Targets:")
    for target in targets:
        vuln_status = "🔴 HIGH" if target['is_vulnerable'] else "🟡 LOW"
        print(f"   • {target['inverter_id']} - Bus {target['bus']}: "
              f"{target['size_kw']}kW, V={target['baseline_voltage_pu']:.3f}pu, "
              f"Attack Risk: {vuln_status}")

    # Visualize network
    feeder.visualize_network(save_path="ieee_distribution_feeder.png")

    # Export data for co-simulation
    export_data = feeder.export_network_data()

    print(f"\n📊 Network Summary:")
    for key, value in export_data['network_summary'].items():
        print(f"   • {key.replace('_', ' ').title()}: {value}")

    print(f"\n⚡ Voltage Analysis:")
    va = export_data['baseline_results']['voltage_analysis']
    print(f"   • Buses within VDE limits: {len(va['within_limits'])}")
    print(f"   • Vulnerable to FDI attacks: {len(va['vulnerable_to_fdi'])}")

    print("\n🏆 IEEE Distribution Feeder Setup Complete!")
    print("    Ready for cyber-physical co-simulation integration")

    return feeder


if __name__ == "__main__":
    main()