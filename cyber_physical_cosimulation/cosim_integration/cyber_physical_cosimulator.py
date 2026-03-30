"""
Cyber-Physical Co-Simulation Framework
Integrates pandapower power system simulation with MQTT network simulation
Replaces HELICS with Python-based co-simulation framework

Based on research proposal: "Cyber-Physical Co-Simulation for Smart Grid Security"
Focus: Impact of Cyber-Induced False Data Injection on Solar-Rich Distribution Networks
"""

import asyncio
import time
import threading
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
import json
import logging

# Import our custom modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'power_system'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'network_simulation'))

from ieee_distribution_feeder import IEEEDistributionFeeder
from mqtt_network_simulator import MQTTNetworkSimulator, CyberPhysicalCoSimulator
import pandapower as pp


class CyberPhysicalCoSimulationFramework:
    """
    Complete Cyber-Physical Co-Simulation Framework
    Synchronizes power system and network simulations for FDI attack analysis
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the cyber-physical co-simulation framework

        Args:
            config: Co-simulation configuration parameters
        """
        self.config = config or self._get_default_config()

        # Initialize subsystems
        self.power_system: Optional[IEEEDistributionFeeder] = None
        self.network_simulator: Optional[MQTTNetworkSimulator] = None

        # Co-simulation synchronization
        self.simulation_time = 0.0
        self.time_step = self.config['cosimulation']['time_step_s']
        self.max_simulation_time = self.config['cosimulation']['max_time_s']
        self.is_running = False

        # Data exchange
        self.power_to_network_data = {}
        self.network_to_power_data = {}

        # Attack simulation
        self.active_attacks = []
        self.attack_log = []

        # Results collection
        self.simulation_results = {
            'timestamps': [],
            'voltage_profiles': [],
            'power_flows': [],
            'network_delays': [],
            'attack_events': [],
            'stability_metrics': []
        }

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default co-simulation configuration"""
        return {
            'power_system': {
                'feeder_type': 'ieee13',
                'solar_penetration': 0.3,
                'voltage_limits': {'lower': 0.9, 'upper': 1.1}
            },
            'network': {
                'base_delay_ms': 15,
                'max_delay_ms': 50,
                'packet_loss_rate': 0.01,
                'telemetry_interval_s': 1.0
            },
            'cosimulation': {
                'time_step_s': 0.1,  # 100ms co-simulation step
                'max_time_s': 300,   # 5 minutes simulation
                'sync_tolerance_ms': 10  # 10ms synchronization tolerance
            },
            'attack_scenarios': {
                'voltage_manipulation': {
                    'target_voltage_pu': 1.15,
                    'target_power_kw': 0,
                    'duration_s': 30
                },
                'power_manipulation': {
                    'target_power_kw': 100,
                    'target_reactive_kvar': 50,
                    'duration_s': 45
                },
                'frequency_attack': {
                    'target_frequency_hz': 52.5,
                    'target_voltage_pu': 0.85,
                    'duration_s': 20
                }
            }
        }

    def initialize_power_system(self):
        """Initialize the power system simulation"""

        print("🔌 Initializing Power System Simulation")

        self.power_system = IEEEDistributionFeeder(
            feeder_type=self.config['power_system']['feeder_type'],
            solar_penetration=self.config['power_system']['solar_penetration']
        )

        # Create the network
        net = self.power_system.create_ieee_feeder()

        print(f"✅ Power system initialized with {len(self.power_system.solar_systems)} solar systems")

        return net

    def initialize_network_simulator(self):
        """Initialize the network simulation"""

        print("🌐 Initializing Network Simulation")

        if not self.power_system:
            raise RuntimeError("Power system must be initialized first")

        # Create network simulator with configuration
        network_config = {
            'network': {
                'min_delay_ms': 5,
                'max_delay_ms': self.config['network']['max_delay_ms'],
                'avg_delay_ms': self.config['network']['base_delay_ms'],
                'jitter_ms': 5,
                'packet_loss_rate': self.config['network']['packet_loss_rate'],
                'burst_loss': False,
                'burst_length': 3
            },
            'simulation': {
                'time_step_ms': self.config['cosimulation']['time_step_s'] * 1000,
                'telemetry_interval_s': self.config['network']['telemetry_interval_s']
            }
        }

        self.network_simulator = MQTTNetworkSimulator(network_config)

        # Register inverters from power system
        for solar in self.power_system.solar_systems:
            self.network_simulator.register_inverter(
                inverter_id=solar['inverter_id'],
                bus_id=solar['bus'],
                rated_power_kw=solar['size_kw']
            )

        print(f"✅ Network simulation initialized with {len(self.network_simulator.inverters)} inverters")

    def start_cosimulation(self):
        """Start the cyber-physical co-simulation"""

        if self.is_running:
            print("⚠️ Co-simulation already running")
            return

        print("🚀 Starting Cyber-Physical Co-Simulation")
        print("=" * 60)

        # Initialize subsystems
        self.initialize_power_system()
        self.initialize_network_simulator()

        # Initialize network simulation (without async start)
        print("✅ Network simulation ready")

        # Start co-simulation loop
        self.is_running = True
        self._run_cosimulation_loop()

    def _run_cosimulation_loop(self):
        """Run the main co-simulation synchronization loop"""

        print(f"🔄 Running co-simulation for {self.max_simulation_time}s")
        print(f"   Time step: {self.time_step}s")

        start_time = time.time()

        while self.is_running and self.simulation_time < self.max_simulation_time:
            loop_start = time.time()

            # Execute one co-simulation step
            self._execute_cosimulation_step()

            # Update simulation time
            self.simulation_time += self.time_step

            # Maintain real-time synchronization
            elapsed = time.time() - loop_start
            if elapsed < self.time_step:
                time.sleep(self.time_step - elapsed)

            # Progress reporting
            if int(self.simulation_time) % 30 == 0:  # Every 30 seconds
                self._print_progress()

        total_time = time.time() - start_time
        print(f"✅ Co-simulation completed in {total_time:.2f}s (simulated {self.simulation_time:.1f}s)")

        # Stop network simulation
        if self.network_simulator:
            self.network_simulator.simulation_running = False
        self.is_running = False

    def _execute_cosimulation_step(self):
        """Execute one step of co-simulation"""

        try:
            # 1. Run power system analysis
            power_results = self._update_power_system()

            # 2. Exchange data with network simulation
            network_results = self._update_network_system(power_results)

            # 3. Check for stability violations
            stability_metrics = self._analyze_system_stability(power_results)

            # 4. Record results
            self._record_simulation_step(power_results, network_results, stability_metrics)

        except Exception as e:
            logging.error(f"Error in co-simulation step: {e}")
            self.is_running = False

    def _update_power_system(self) -> Dict[str, Any]:
        """Update power system simulation"""

        try:
            # Run power flow
            pp.runpp(self.power_system.net, algorithm="nr", calculate_voltage_angles=True)

            # Extract results
            results = {
                'bus_voltages_pu': self.power_system.net.res_bus.vm_pu.copy(),
                'bus_voltages_kv': self.power_system.net.res_bus.vm_pu * self.power_system.net.bus.vn_kv,
                'bus_angles_deg': self.power_system.net.res_bus.va_degree.copy(),
                'line_loading_percent': self.power_system.net.res_line.loading_percent.copy(),
                'solar_generation': self._get_solar_generation(),
                'total_load': self.power_system.net.load.p_mw.sum(),
                'converged': True
            }

            return results

        except Exception as e:
            logging.error(f"Power flow failed: {e}")
            return {'converged': False, 'error': str(e)}

    def _get_solar_generation(self) -> Dict[str, float]:
        """Get current solar generation from all inverters"""

        solar_gen = {}
        for solar in self.power_system.solar_systems:
            bus = solar['bus']
            sgen_idx = solar['sgen_idx']

            # Get generation from pandapower results
            if sgen_idx < len(self.power_system.net.res_sgen):
                p_mw = self.power_system.net.res_sgen.loc[sgen_idx, 'p_mw']
                q_mvar = self.power_system.net.res_sgen.loc[sgen_idx, 'q_mvar']

                solar_gen[solar['inverter_id']] = {
                    'bus': bus,
                    'p_mw': p_mw,
                    'q_mvar': q_mvar,
                    'p_kw': p_mw * 1000,
                    'q_kvar': q_mvar * 1000
                }

        return solar_gen

    def _update_network_system(self, power_results: Dict[str, Any]) -> Dict[str, Any]:
        """Update network simulation with power system data"""

        # Update inverter setpoints based on power system results
        if 'solar_generation' in power_results:
            for inverter_id, gen_data in power_results['solar_generation'].items():
                if inverter_id in self.network_simulator.inverters:
                    inverter = self.network_simulator.inverters[inverter_id]
                    inverter.current_power_kw = gen_data['p_kw']

        # Get network statistics
        network_stats = self.network_simulator.get_network_statistics()

        return network_stats

    def _analyze_system_stability(self, power_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze system stability and detect violations"""

        stability_metrics = {
            'voltage_violations': [],
            'overload_violations': [],
            'stability_index': 1.0,
            'critical_buses': [],
            'max_voltage_deviation': 0.0
        }

        if not power_results.get('converged', False):
            stability_metrics['stability_index'] = 0.0
            return stability_metrics

        # Voltage stability analysis
        voltage_limits = self.config['power_system']['voltage_limits']
        lv_buses = self.power_system.net.bus[self.power_system.net.bus.vn_kv == 0.4].index

        max_deviation = 0.0
        for bus in lv_buses:
            if bus in power_results['bus_voltages_pu']:
                v_pu = power_results['bus_voltages_pu'][bus]

                # Check voltage violations
                if v_pu < voltage_limits['lower']:
                    stability_metrics['voltage_violations'].append({
                        'bus': bus,
                        'voltage_pu': v_pu,
                        'violation_type': 'undervoltage',
                        'severity': (voltage_limits['lower'] - v_pu) / voltage_limits['lower']
                    })
                elif v_pu > voltage_limits['upper']:
                    stability_metrics['voltage_violations'].append({
                        'bus': bus,
                        'voltage_pu': v_pu,
                        'violation_type': 'overvoltage',
                        'severity': (v_pu - voltage_limits['upper']) / voltage_limits['upper']
                    })

                # Track maximum deviation from nominal
                deviation = abs(v_pu - 1.0)
                max_deviation = max(max_deviation, deviation)

                # Identify critical buses (close to limits)
                margin = min(abs(v_pu - voltage_limits['lower']),
                           abs(v_pu - voltage_limits['upper']))
                if margin < 0.05:  # Within 5% of limits
                    stability_metrics['critical_buses'].append(bus)

        stability_metrics['max_voltage_deviation'] = max_deviation

        # Calculate overall stability index
        if stability_metrics['voltage_violations']:
            # Reduce stability index based on violations
            violation_penalty = len(stability_metrics['voltage_violations']) * 0.1
            stability_metrics['stability_index'] = max(0.0, 1.0 - violation_penalty)

        return stability_metrics

    def _record_simulation_step(self, power_results: Dict[str, Any],
                               network_results: Dict[str, Any],
                               stability_metrics: Dict[str, Any]):
        """Record results from current simulation step"""

        self.simulation_results['timestamps'].append(self.simulation_time)
        self.simulation_results['voltage_profiles'].append(power_results.get('bus_voltages_pu', {}))
        self.simulation_results['power_flows'].append(power_results.get('solar_generation', {}))
        self.simulation_results['network_delays'].append(network_results.get('avg_delay_ms', 0))
        self.simulation_results['stability_metrics'].append(stability_metrics)

    def _print_progress(self):
        """Print simulation progress"""

        progress = (self.simulation_time / self.max_simulation_time) * 100

        # Get latest stability info
        if self.simulation_results['stability_metrics']:
            latest_stability = self.simulation_results['stability_metrics'][-1]
            stability_index = latest_stability['stability_index']
            voltage_violations = len(latest_stability['voltage_violations'])
        else:
            stability_index = 1.0
            voltage_violations = 0

        print(f"⏱️  Progress: {progress:.1f}% | "
              f"Time: {self.simulation_time:.1f}s | "
              f"Stability: {stability_index:.3f} | "
              f"Violations: {voltage_violations}")

    def launch_fdi_attack(self, attack_type: str, target_inverter: str = None,
                         start_time: float = None) -> bool:
        """Launch False Data Injection attack during simulation"""

        if not self.network_simulator:
            print("❌ Network simulator not initialized")
            return False

        # Use default target if not specified
        if not target_inverter and self.network_simulator.inverters:
            target_inverter = list(self.network_simulator.inverters.keys())[0]

        if target_inverter not in self.network_simulator.inverters:
            print(f"❌ Target inverter {target_inverter} not found")
            return False

        # Get attack parameters
        if attack_type not in self.config['attack_scenarios']:
            print(f"❌ Unknown attack type: {attack_type}")
            return False

        attack_params = self.config['attack_scenarios'][attack_type].copy()
        duration = attack_params.pop('duration_s', 30)

        # Schedule attack
        attack_start_time = start_time or self.simulation_time

        attack_info = {
            'attack_type': attack_type,
            'target_inverter': target_inverter,
            'start_time': attack_start_time,
            'duration': duration,
            'parameters': attack_params
        }

        self.active_attacks.append(attack_info)

        print(f"🚨 FDI Attack Scheduled:")
        print(f"   Type: {attack_type}")
        print(f"   Target: {target_inverter}")
        print(f"   Start: {attack_start_time:.1f}s")
        print(f"   Duration: {duration}s")

        # Launch attack if it should start now
        if attack_start_time <= self.simulation_time:
            return self._execute_fdi_attack(attack_info)

        return True

    def _execute_fdi_attack(self, attack_info: Dict[str, Any]) -> bool:
        """Execute FDI attack"""

        success = self.network_simulator.launch_fdi_attack(
            target_inverter=attack_info['target_inverter'],
            attack_params=attack_info['parameters'],
            duration_seconds=attack_info['duration']
        )

        if success:
            # Record attack in log
            self.attack_log.append({
                'timestamp': self.simulation_time,
                'attack_type': attack_info['attack_type'],
                'target': attack_info['target_inverter'],
                'parameters': attack_info['parameters']
            })

            # Record in simulation results
            self.simulation_results['attack_events'].append({
                'time': self.simulation_time,
                'type': attack_info['attack_type'],
                'target': attack_info['target_inverter']
            })

        return success

    def get_simulation_results(self) -> Dict[str, Any]:
        """Get complete simulation results"""

        results = {
            'configuration': self.config,
            'simulation_summary': {
                'total_time': self.simulation_time,
                'time_step': self.time_step,
                'power_system': {
                    'feeder_type': self.config['power_system']['feeder_type'],
                    'solar_systems': len(self.power_system.solar_systems) if self.power_system else 0,
                    'total_buses': len(self.power_system.net.bus) if self.power_system else 0
                },
                'network_system': self.network_simulator.get_network_statistics() if self.network_simulator else {},
                'attacks_executed': len(self.attack_log)
            },
            'time_series_data': self.simulation_results,
            'attack_log': self.attack_log
        }

        return results

    def export_results(self, filepath: str):
        """Export simulation results to JSON file"""

        results = self.get_simulation_results()

        # Convert numpy arrays to lists for JSON serialization
        def convert_numpy(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            return obj

        # Recursive conversion
        def clean_for_json(data):
            if isinstance(data, dict):
                return {k: clean_for_json(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [clean_for_json(item) for item in data]
            else:
                return convert_numpy(data)

        clean_results = clean_for_json(results)

        with open(filepath, 'w') as f:
            json.dump(clean_results, f, indent=2)

        print(f"📄 Results exported to {filepath}")

    def stop_simulation(self):
        """Stop the co-simulation"""

        self.is_running = False
        if self.network_simulator:
            self.network_simulator.stop_simulation()

        print("🛑 Co-simulation stopped")


def main():
    """Test the complete cyber-physical co-simulation framework"""

    print("🔗 Testing Complete Cyber-Physical Co-Simulation Framework")
    print("=" * 70)

    # Create co-simulation framework
    cosim = CyberPhysicalCoSimulationFramework()

    # Test configuration
    print("📋 Configuration:")
    print(f"   • Power System: {cosim.config['power_system']['feeder_type'].upper()} feeder")
    print(f"   • Solar Penetration: {cosim.config['power_system']['solar_penetration']:.0%}")
    print(f"   • Simulation Time: {cosim.config['cosimulation']['max_time_s']}s")
    print(f"   • Time Step: {cosim.config['cosimulation']['time_step_s']}s")

    # Initialize and run short test
    cosim.config['cosimulation']['max_time_s'] = 30  # Short test

    try:
        # Schedule FDI attack
        attack_scheduled = cosim.launch_fdi_attack(
            attack_type='voltage_manipulation',
            start_time=10  # Attack starts at 10 seconds
        )

        if attack_scheduled:
            print("✅ FDI attack scheduled successfully")

        # Start co-simulation
        cosim.start_cosimulation()

        # Get results
        results = cosim.get_simulation_results()

        print(f"\n📊 Simulation Summary:")
        summary = results['simulation_summary']
        print(f"   • Total Simulation Time: {summary['total_time']:.1f}s")
        print(f"   • Power System Buses: {summary['power_system']['total_buses']}")
        print(f"   • Solar Systems: {summary['power_system']['solar_systems']}")
        print(f"   • Network Messages: {summary['network_system'].get('messages_sent', 0)}")
        print(f"   • Attacks Executed: {summary['attacks_executed']}")

        # Export results
        cosim.export_results('cosimulation_test_results.json')

        print(f"\n🏆 Cyber-Physical Co-Simulation Test Complete!")

    except KeyboardInterrupt:
        print(f"\n🛑 Simulation interrupted by user")
        cosim.stop_simulation()

    except Exception as e:
        print(f"\n❌ Simulation error: {e}")
        cosim.stop_simulation()

    return cosim


if __name__ == "__main__":
    cosim = main()