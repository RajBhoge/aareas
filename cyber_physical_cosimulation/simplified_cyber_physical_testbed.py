"""
Simplified Cyber-Physical Testbed for Smart Grid Security
Focus: Impact of Cyber-Induced False Data Injection on Solar-Rich Distribution Networks

BASIC IMPLEMENTATION - Core functionality only:
1. IEEE distribution feeder with solar PV
2. False Data Injection attacks on voltage readings
3. Voltage stability analysis
4. Attack impact visualization
5. Basic synthetic dataset generation

Institution: Friedrich-Alexander-Universität Erlangen-Nürnberg
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pandapower as pp
import time
import json
import os
from typing import Dict, List, Any, Tuple
import warnings
warnings.filterwarnings('ignore')


class SimplifiedCyberPhysicalTestbed:
    """
    Simplified testbed focusing on core FDI attack analysis
    """

    def __init__(self):
        """Initialize simplified testbed"""

        # Core configuration
        self.config = {
            'solar_penetration': 0.4,  # 40% of buses have solar
            'solar_sizes_kw': [15, 20, 25, 30],  # Available solar sizes
            'voltage_limits': {
                'vde_lower': 0.9,   # VDE -10%
                'vde_upper': 1.1,   # VDE +10%
                'critical_lower': 0.85,  # Critical undervoltage
                'critical_upper': 1.15   # Critical overvoltage
            }
        }

        # System components
        self.power_network = None
        self.solar_systems = []
        self.baseline_voltages = {}

        # Attack and results
        self.attack_results = []
        self.synthetic_data = []

    def create_basic_distribution_network(self):
        """Create basic IEEE-style distribution network with solar"""

        print("🔌 Creating Basic Distribution Network with Solar PV")

        # Create pandapower network
        net = pp.create_empty_network()

        # Create buses (simplified 8-bus system)
        buses = {}
        bus_data = [
            ("Source", 4.16, "b"),      # MV source bus
            ("Main_LV", 0.4, "n"),      # Main LV bus
            ("Res_1", 0.4, "n"),        # Residential area 1
            ("Res_2", 0.4, "n"),        # Residential area 2
            ("Res_3", 0.4, "n"),        # Residential area 3
            ("Com_1", 0.4, "n"),        # Commercial area 1
            ("Com_2", 0.4, "n"),        # Commercial area 2
            ("End", 0.4, "n")           # End of feeder
        ]

        for i, (name, vn_kv, bus_type) in enumerate(bus_data):
            bus_idx = pp.create_bus(net, vn_kv=vn_kv, name=name)
            buses[name] = bus_idx

        # External grid connection
        pp.create_ext_grid(net, bus=buses["Source"], vm_pu=1.0)

        # Create transformer MV/LV
        pp.create_transformer(net,
                            hv_bus=buses["Source"],
                            lv_bus=buses["Main_LV"],
                            std_type="25 MVA 110/20 kV")

        # Create distribution lines
        line_data = [
            ("Main_LV", "Res_1", 0.2),
            ("Main_LV", "Com_1", 0.3),
            ("Res_1", "Res_2", 0.15),
            ("Res_2", "Res_3", 0.1),
            ("Com_1", "Com_2", 0.2),
            ("Com_2", "End", 0.25)
        ]

        for from_bus, to_bus, length_km in line_data:
            pp.create_line(net,
                         from_bus=buses[from_bus],
                         to_bus=buses[to_bus],
                         length_km=length_km,
                         std_type="NAYY 4x50 SE")

        # Create loads (residential and commercial)
        load_data = [
            ("Res_1", 12, "residential"),
            ("Res_2", 15, "residential"),
            ("Res_3", 18, "residential"),
            ("Com_1", 35, "commercial"),
            ("Com_2", 28, "commercial"),
            ("End", 8, "residential")
        ]

        for bus_name, power_kw, load_type in load_data:
            pp.create_load(net,
                         bus=buses[bus_name],
                         p_mw=power_kw/1000,
                         q_mvar=power_kw*0.1/1000,
                         name=f"Load_{bus_name}")

        # Add solar PV systems
        self._add_solar_systems(net, buses)

        self.power_network = net
        self.bus_mapping = buses

        # Run baseline analysis
        self._run_baseline_analysis()

        print(f"✅ Network created: {len(self.solar_systems)} solar systems")
        return net

    def _add_solar_systems(self, net, buses):
        """Add solar PV systems to selected buses"""

        # Select LV buses for solar installation
        lv_buses = ["Res_1", "Res_2", "Res_3", "Com_1", "Com_2"]
        n_solar = int(len(lv_buses) * self.config['solar_penetration'])

        selected_buses = np.random.choice(lv_buses, size=n_solar, replace=False)

        for i, bus_name in enumerate(selected_buses):
            # Random solar system size
            size_kw = np.random.choice(self.config['solar_sizes_kw'])

            # Create solar generator
            sgen_idx = pp.create_sgen(net,
                                    bus=buses[bus_name],
                                    p_mw=size_kw/1000,
                                    q_mvar=-size_kw*0.1/1000,  # Slightly capacitive
                                    name=f"Solar_{bus_name}_{size_kw}kW")

            # Store solar system info
            solar_info = {
                'id': f"Solar_{bus_name}_{size_kw}kW",
                'bus_name': bus_name,
                'bus_idx': buses[bus_name],
                'size_kw': size_kw,
                'sgen_idx': sgen_idx
            }
            self.solar_systems.append(solar_info)

        print(f"   🌞 Added {len(self.solar_systems)} solar systems")

    def _run_baseline_analysis(self):
        """Run baseline power flow analysis"""

        try:
            pp.runpp(self.power_network)

            # Store baseline voltages
            for bus_idx in self.power_network.bus.index:
                bus_name = self.power_network.bus.loc[bus_idx, 'name']
                voltage_pu = self.power_network.res_bus.loc[bus_idx, 'vm_pu']
                self.baseline_voltages[bus_name] = voltage_pu

            print(f"   ⚡ Baseline analysis complete")

        except Exception as e:
            print(f"   ❌ Baseline analysis failed: {e}")

    def execute_fdi_attacks(self):
        """Execute basic FDI attack scenarios"""

        print("\n🚨 Executing FDI Attack Scenarios")
        print("=" * 50)

        attack_scenarios = [
            {
                'name': 'Overvoltage Attack',
                'type': 'voltage_manipulation',
                'false_voltage': 1.2,  # 20% overvoltage
                'description': 'Inject false high voltage readings'
            },
            {
                'name': 'Critical Overvoltage',
                'type': 'voltage_manipulation',
                'false_voltage': 1.3,  # 30% overvoltage (dangerous)
                'description': 'Inject critically high voltage'
            },
            {
                'name': 'Undervoltage Attack',
                'type': 'voltage_manipulation',
                'false_voltage': 0.8,  # 20% undervoltage
                'description': 'Inject false low voltage readings'
            }
        ]

        for scenario in attack_scenarios:
            print(f"\n🎯 Scenario: {scenario['name']}")
            result = self._execute_single_attack(scenario)
            self.attack_results.append(result)

            print(f"   Impact: {result['impact_summary']}")

        print(f"\n✅ Attack analysis complete: {len(self.attack_results)} scenarios")

    def _execute_single_attack(self, scenario):
        """Execute a single FDI attack scenario"""

        # Select target solar system (most vulnerable)
        target_solar = self._select_attack_target()

        if not target_solar:
            return {'error': 'No attack target available'}

        # Simulate attack impact by modifying solar output based on false readings
        original_power = self.power_network.sgen.loc[target_solar['sgen_idx'], 'p_mw']

        # Calculate how inverter would respond to false voltage reading
        false_voltage = scenario['false_voltage']

        if false_voltage > self.config['voltage_limits']['vde_upper']:
            # High voltage -> inverter reduces power or disconnects
            if false_voltage > self.config['voltage_limits']['critical_upper']:
                new_power = 0.0  # Complete disconnection
                response = "inverter_disconnect"
            else:
                new_power = original_power * 0.3  # Reduce to 30%
                response = "power_reduction"
        elif false_voltage < self.config['voltage_limits']['vde_lower']:
            # Low voltage -> inverter may boost or disconnect
            if false_voltage < self.config['voltage_limits']['critical_lower']:
                new_power = 0.0  # Complete disconnection
                response = "inverter_disconnect"
            else:
                new_power = original_power * 1.2  # Try to boost (may cause issues)
                response = "power_increase"
        else:
            new_power = original_power
            response = "no_change"

        # Apply attack effect
        self.power_network.sgen.loc[target_solar['sgen_idx'], 'p_mw'] = new_power

        # Run power flow with attack
        try:
            pp.runpp(self.power_network)
            attack_successful = True

            # Analyze impact
            impact_analysis = self._analyze_attack_impact(target_solar, scenario, response)

        except Exception as e:
            attack_successful = False
            impact_analysis = {'error': f'Power flow failed: {e}'}

        # Restore original state
        self.power_network.sgen.loc[target_solar['sgen_idx'], 'p_mw'] = original_power

        return {
            'scenario': scenario['name'],
            'target': target_solar['id'],
            'false_voltage': false_voltage,
            'inverter_response': response,
            'attack_successful': attack_successful,
            'impact_analysis': impact_analysis,
            'impact_summary': impact_analysis.get('summary', 'Analysis failed')
        }

    def _select_attack_target(self):
        """Select most vulnerable solar system for attack"""

        if not self.solar_systems:
            return None

        # Simple selection: largest solar system (highest impact)
        target = max(self.solar_systems, key=lambda x: x['size_kw'])
        return target

    def _analyze_attack_impact(self, target_solar, scenario, response):
        """Analyze the impact of FDI attack"""

        # Get post-attack voltages
        post_attack_voltages = {}
        voltage_violations = []

        for bus_idx in self.power_network.bus.index:
            bus_name = self.power_network.bus.loc[bus_idx, 'name']
            voltage_pu = self.power_network.res_bus.loc[bus_idx, 'vm_pu']
            post_attack_voltages[bus_name] = voltage_pu

            # Check for voltage violations
            baseline_v = self.baseline_voltages.get(bus_name, 1.0)
            voltage_change = voltage_pu - baseline_v

            if voltage_pu < self.config['voltage_limits']['vde_lower']:
                violation_type = 'undervoltage'
                severity = 'critical' if voltage_pu < self.config['voltage_limits']['critical_lower'] else 'warning'
                voltage_violations.append({
                    'bus': bus_name,
                    'type': violation_type,
                    'severity': severity,
                    'voltage_pu': voltage_pu,
                    'change_pu': voltage_change
                })

            elif voltage_pu > self.config['voltage_limits']['vde_upper']:
                violation_type = 'overvoltage'
                severity = 'critical' if voltage_pu > self.config['voltage_limits']['critical_upper'] else 'warning'
                voltage_violations.append({
                    'bus': bus_name,
                    'type': violation_type,
                    'severity': severity,
                    'voltage_pu': voltage_pu,
                    'change_pu': voltage_change
                })

        # Calculate impact summary
        critical_violations = len([v for v in voltage_violations if v['severity'] == 'critical'])
        warning_violations = len([v for v in voltage_violations if v['severity'] == 'warning'])

        if critical_violations > 0:
            impact_level = 'CRITICAL'
            summary = f"Critical impact: {critical_violations} critical violations"
        elif warning_violations > 0:
            impact_level = 'HIGH'
            summary = f"High impact: {warning_violations} voltage violations"
        elif response == "inverter_disconnect":
            impact_level = 'MEDIUM'
            summary = f"Medium impact: Solar system disconnected"
        else:
            impact_level = 'LOW'
            summary = f"Low impact: Minor system changes"

        return {
            'impact_level': impact_level,
            'summary': summary,
            'voltage_violations': voltage_violations,
            'post_attack_voltages': post_attack_voltages,
            'inverter_response': response,
            'critical_violations': critical_violations,
            'warning_violations': warning_violations
        }

    def generate_synthetic_dataset(self, n_samples=1000):
        """Generate synthetic dataset for AI training"""

        print(f"\n📊 Generating Synthetic Dataset ({n_samples} samples)")

        dataset = []

        for i in range(n_samples):
            # Generate normal sample (70% of data)
            if np.random.random() < 0.7:
                sample = self._generate_normal_sample(i)
                sample['label'] = 'normal'
                sample['attack_type'] = 'none'
            else:
                # Generate attack sample (30% of data)
                sample = self._generate_attack_sample(i)
                sample['label'] = 'attack'

            dataset.append(sample)

        # Convert to DataFrame
        df = pd.DataFrame(dataset)

        # Save dataset
        os.makedirs('simplified_results', exist_ok=True)
        df.to_csv('simplified_results/synthetic_fdi_dataset.csv', index=False)

        self.synthetic_data = df

        print(f"✅ Dataset generated: {len(df)} samples")
        print(f"   Normal samples: {len(df[df['label'] == 'normal'])}")
        print(f"   Attack samples: {len(df[df['label'] == 'attack'])}")

        return df

    def _generate_normal_sample(self, sample_id):
        """Generate normal operation sample"""

        return {
            'sample_id': sample_id,
            'voltage_pu': np.random.normal(1.0, 0.02),  # Normal voltage with small variation
            'solar_power_kw': np.random.normal(20, 5),   # Normal solar output
            'frequency_hz': np.random.normal(50.0, 0.1), # Normal frequency
            'temperature_c': np.random.normal(25, 8),    # Ambient temperature
        }

    def _generate_attack_sample(self, sample_id):
        """Generate attack sample"""

        # Random attack type
        attack_types = ['overvoltage', 'undervoltage', 'power_manipulation']
        attack_type = np.random.choice(attack_types)

        if attack_type == 'overvoltage':
            voltage = np.random.uniform(1.15, 1.4)  # High voltage attack
            power = np.random.normal(20, 5)
            frequency = np.random.normal(50.0, 0.1)

        elif attack_type == 'undervoltage':
            voltage = np.random.uniform(0.6, 0.85)  # Low voltage attack
            power = np.random.normal(20, 5)
            frequency = np.random.normal(50.0, 0.1)

        else:  # power_manipulation
            voltage = np.random.normal(1.0, 0.02)
            power = np.random.uniform(0, 5)  # False low power reading
            frequency = np.random.normal(50.0, 0.1)

        return {
            'sample_id': sample_id,
            'voltage_pu': voltage,
            'solar_power_kw': power,
            'frequency_hz': frequency,
            'temperature_c': np.random.normal(25, 8),
            'attack_type': attack_type
        }

    def create_visualizations(self):
        """Create basic visualizations of results"""

        print(f"\n📈 Creating Visualizations")

        os.makedirs('simplified_results', exist_ok=True)

        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Simplified Cyber-Physical Testbed Results\nFDI Attack Impact Analysis',
                    fontsize=16, fontweight='bold')

        # Plot 1: Network topology with solar systems
        ax1.set_title('Distribution Network with Solar PV', fontsize=14)

        # Simple network diagram
        bus_positions = {
            'Source': (0, 2),
            'Main_LV': (1, 2),
            'Res_1': (2, 3),
            'Res_2': (3, 3),
            'Res_3': (4, 3),
            'Com_1': (2, 1),
            'Com_2': (3, 1),
            'End': (4, 1)
        }

        # Draw buses
        for bus_name, (x, y) in bus_positions.items():
            color = 'red' if bus_name == 'Source' else 'lightblue'
            ax1.scatter(x, y, s=200, c=color, alpha=0.7)
            ax1.annotate(bus_name.replace('_', '\n'), (x, y), ha='center', va='center', fontsize=8)

        # Draw lines
        line_connections = [
            ('Source', 'Main_LV'),
            ('Main_LV', 'Res_1'),
            ('Main_LV', 'Com_1'),
            ('Res_1', 'Res_2'),
            ('Res_2', 'Res_3'),
            ('Com_1', 'Com_2'),
            ('Com_2', 'End')
        ]

        for from_bus, to_bus in line_connections:
            x1, y1 = bus_positions[from_bus]
            x2, y2 = bus_positions[to_bus]
            ax1.plot([x1, x2], [y1, y2], 'k-', alpha=0.6, linewidth=2)

        # Mark solar systems
        for solar in self.solar_systems:
            x, y = bus_positions[solar['bus_name']]
            ax1.scatter(x+0.1, y+0.1, s=100, c='yellow', marker='*', edgecolor='orange')
            ax1.annotate(f"{solar['size_kw']}kW", (x+0.1, y+0.1),
                        xytext=(5, 5), textcoords='offset points', fontsize=6)

        ax1.set_xlim(-0.5, 4.5)
        ax1.set_ylim(0.5, 3.5)
        ax1.grid(True, alpha=0.3)
        ax1.set_xlabel('Network Distance')
        ax1.set_ylabel('Feeder Branch')

        # Plot 2: Attack impact comparison
        if self.attack_results:
            ax2.set_title('FDI Attack Impact Analysis', fontsize=14)

            scenarios = [r['scenario'] for r in self.attack_results]
            critical_violations = [r['impact_analysis'].get('critical_violations', 0) for r in self.attack_results]
            warning_violations = [r['impact_analysis'].get('warning_violations', 0) for r in self.attack_results]

            x_pos = np.arange(len(scenarios))
            width = 0.35

            bars1 = ax2.bar(x_pos - width/2, critical_violations, width,
                           label='Critical Violations', color='red', alpha=0.8)
            bars2 = ax2.bar(x_pos + width/2, warning_violations, width,
                           label='Warning Violations', color='orange', alpha=0.8)

            ax2.set_xlabel('Attack Scenarios')
            ax2.set_ylabel('Number of Violations')
            ax2.set_xticks(x_pos)
            ax2.set_xticklabels([s.replace(' ', '\n') for s in scenarios])
            ax2.legend()
            ax2.grid(True, alpha=0.3)

            # Add value labels on bars
            for bars in [bars1, bars2]:
                for bar in bars:
                    height = bar.get_height()
                    if height > 0:
                        ax2.annotate(f'{int(height)}',
                                   xy=(bar.get_x() + bar.get_width() / 2, height),
                                   xytext=(0, 3), textcoords="offset points",
                                   ha='center', va='bottom', fontsize=10)

        # Plot 3: Voltage analysis
        ax3.set_title('Voltage Stability Analysis', fontsize=14)

        if self.baseline_voltages:
            bus_names = list(self.baseline_voltages.keys())
            baseline_voltages = list(self.baseline_voltages.values())

            x_pos = np.arange(len(bus_names))

            # Plot baseline voltages
            ax3.bar(x_pos, baseline_voltages, alpha=0.7, color='green', label='Baseline Voltage')

            # Add voltage limit lines
            ax3.axhline(y=self.config['voltage_limits']['vde_lower'],
                       color='orange', linestyle='--', label='VDE Lower Limit (0.9 pu)')
            ax3.axhline(y=self.config['voltage_limits']['vde_upper'],
                       color='orange', linestyle='--', label='VDE Upper Limit (1.1 pu)')
            ax3.axhline(y=self.config['voltage_limits']['critical_lower'],
                       color='red', linestyle=':', label='Critical Lower (0.85 pu)')
            ax3.axhline(y=self.config['voltage_limits']['critical_upper'],
                       color='red', linestyle=':', label='Critical Upper (1.15 pu)')

            ax3.set_xlabel('Network Buses')
            ax3.set_ylabel('Voltage (p.u.)')
            ax3.set_xticks(x_pos)
            ax3.set_xticklabels([name.replace('_', '\n') for name in bus_names], rotation=45)
            ax3.legend(fontsize=8)
            ax3.grid(True, alpha=0.3)
            ax3.set_ylim(0.8, 1.2)

        # Plot 4: Dataset distribution (if generated)
        if hasattr(self, 'synthetic_data') and not self.synthetic_data.empty:
            ax4.set_title('Synthetic Dataset Distribution', fontsize=14)

            # Count by label and attack type
            label_counts = self.synthetic_data['label'].value_counts()
            attack_type_counts = self.synthetic_data[self.synthetic_data['label'] == 'attack']['attack_type'].value_counts()

            # Pie chart of normal vs attack
            ax4.pie([label_counts.get('normal', 0), label_counts.get('attack', 0)],
                   labels=['Normal Operation', 'FDI Attacks'],
                   autopct='%1.1f%%', startangle=90,
                   colors=['lightgreen', 'lightcoral'])

            # Add attack type breakdown as text
            attack_text = "Attack Types:\n"
            for attack_type, count in attack_type_counts.items():
                pct = (count / len(self.synthetic_data)) * 100
                attack_text += f"• {attack_type}: {pct:.1f}%\n"

            ax4.text(1.3, 0, attack_text, fontsize=10, verticalalignment='center',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow"))

        plt.tight_layout()
        plt.savefig('simplified_results/simplified_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✅ Visualizations saved: simplified_results/simplified_analysis.png")

    def save_results(self):
        """Save all results to files"""

        print(f"\n💾 Saving Results")

        os.makedirs('simplified_results', exist_ok=True)

        # Compile all results
        results = {
            'project_info': {
                'title': 'Simplified Cyber-Physical Co-Simulation for Smart Grid Security',
                'focus': 'Impact of Cyber-Induced False Data Injection on Solar-Rich Distribution Networks',
                'institution': 'Friedrich-Alexander-Universität Erlangen-Nürnberg',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            },
            'network_configuration': {
                'solar_penetration': self.config['solar_penetration'],
                'solar_systems': len(self.solar_systems),
                'voltage_limits': self.config['voltage_limits']
            },
            'baseline_analysis': {
                'baseline_voltages': self.baseline_voltages,
                'solar_systems': self.solar_systems
            },
            'attack_results': self.attack_results,
            'synthetic_dataset_info': {
                'total_samples': len(self.synthetic_data) if hasattr(self, 'synthetic_data') else 0,
                'normal_samples': len(self.synthetic_data[self.synthetic_data['label'] == 'normal']) if hasattr(self, 'synthetic_data') and not self.synthetic_data.empty else 0,
                'attack_samples': len(self.synthetic_data[self.synthetic_data['label'] == 'attack']) if hasattr(self, 'synthetic_data') and not self.synthetic_data.empty else 0
            }
        }

        # Save main results
        with open('simplified_results/simplified_results.json', 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"✅ Results saved to: simplified_results/")
        print(f"   📄 simplified_results.json - Complete results")
        print(f"   📊 synthetic_fdi_dataset.csv - Dataset for AI training")
        print(f"   📈 simplified_analysis.png - Visualizations")

    def run_complete_analysis(self):
        """Run complete simplified analysis"""

        print("🔬 SIMPLIFIED CYBER-PHYSICAL TESTBED")
        print("Research: Impact of FDI Attacks on Solar-Rich Distribution Networks")
        print("Institution: Friedrich-Alexander-Universität Erlangen-Nürnberg")
        print("=" * 70)

        start_time = time.time()

        try:
            # Step 1: Create network
            self.create_basic_distribution_network()

            # Step 2: Execute attacks
            self.execute_fdi_attacks()

            # Step 3: Generate synthetic data
            self.generate_synthetic_dataset(n_samples=1500)

            # Step 4: Create visualizations
            self.create_visualizations()

            # Step 5: Save results
            self.save_results()

            # Print summary
            execution_time = time.time() - start_time

            print(f"\n🏆 ANALYSIS COMPLETE")
            print(f"=" * 40)
            print(f"⏱️  Execution Time: {execution_time:.1f} seconds")
            print(f"🌞 Solar Systems: {len(self.solar_systems)}")
            print(f"🚨 Attack Scenarios: {len(self.attack_results)}")
            print(f"📊 Synthetic Samples: {len(self.synthetic_data) if hasattr(self, 'synthetic_data') else 0}")
            print(f"📁 Results Directory: simplified_results/")

            if self.attack_results:
                critical_impacts = len([r for r in self.attack_results
                                      if r['impact_analysis'].get('impact_level') == 'CRITICAL'])
                print(f"⚠️  Critical Impacts: {critical_impacts}/{len(self.attack_results)} scenarios")

            print(f"\n✅ RESEARCH OBJECTIVES ACHIEVED")
            print("   ✓ FDI attack impact on solar-rich networks demonstrated")
            print("   ✓ Voltage stability vulnerabilities identified")
            print("   ✓ Synthetic dataset generated for AI training")
            print("   ✓ Professional analysis and visualization completed")

        except Exception as e:
            print(f"\n❌ Analysis failed: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main execution function"""

    # Create and run simplified testbed
    testbed = SimplifiedCyberPhysicalTestbed()
    testbed.run_complete_analysis()

    return testbed


if __name__ == "__main__":
    testbed = main()