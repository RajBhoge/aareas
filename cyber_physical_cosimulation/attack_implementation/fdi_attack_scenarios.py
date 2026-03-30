"""
False Data Injection (FDI) Attack Implementation for Smart Grid Security Research
Implements sophisticated FDI attacks targeting solar inverter controllers

Based on research proposal: "Cyber-Physical Co-Simulation for Smart Grid Security"
Focus: Impact of Cyber-Induced False Data Injection on Solar-Rich Distribution Networks
Objective: Cause voltage instability leading to blackouts or equipment damage
"""

import numpy as np
import pandas as pd
import time
import random
import threading
from typing import Dict, List, Tuple, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import json
from datetime import datetime, timedelta

# Import power system modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'power_system'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'network_simulation'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'cosim_integration'))

import pandapower as pp


class AttackSeverity(Enum):
    """Attack severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AttackTarget(Enum):
    """Attack target types"""
    VOLTAGE_CONTROL = "voltage_control"
    POWER_CONTROL = "power_control"
    FREQUENCY_CONTROL = "frequency_control"
    PROTECTION_SYSTEM = "protection_system"


@dataclass
class FDIAttackVector:
    """False Data Injection attack vector definition"""
    attack_id: str
    target_parameter: str  # 'voltage_pu', 'active_power_kw', 'frequency_hz', etc.
    false_value: float     # The false value to inject
    original_value: float  # The actual/correct value
    injection_method: str  # 'constant', 'ramp', 'oscillating', 'random'
    severity: AttackSeverity
    target_type: AttackTarget
    duration_s: float
    start_time: float
    description: str


@dataclass
class AttackResult:
    """Results from FDI attack execution"""
    attack_vector: FDIAttackVector
    execution_successful: bool
    voltage_violations: List[Dict[str, Any]]
    power_system_impact: Dict[str, Any]
    detection_latency_s: float
    max_voltage_deviation: float
    system_stability_lost: bool
    recovery_time_s: Optional[float]
    damage_assessment: Dict[str, Any]


class VoltageFDIAttackGenerator:
    """Generates sophisticated voltage-based FDI attacks"""

    def __init__(self, vde_voltage_limits: Dict[str, float]):
        """
        Initialize voltage FDI attack generator

        Args:
            vde_voltage_limits: VDE voltage limits (0.9-1.1 pu normally)
        """
        self.voltage_limits = vde_voltage_limits

        # Attack patterns for different severities
        self.attack_patterns = {
            AttackSeverity.LOW: {
                'voltage_deviation': 0.03,  # 3% deviation
                'duration_range': (10, 30),  # 10-30 seconds
                'ramp_rate': 0.01            # 1% per second
            },
            AttackSeverity.MEDIUM: {
                'voltage_deviation': 0.08,  # 8% deviation
                'duration_range': (30, 60), # 30-60 seconds
                'ramp_rate': 0.02           # 2% per second
            },
            AttackSeverity.HIGH: {
                'voltage_deviation': 0.15,  # 15% deviation (outside VDE limits)
                'duration_range': (60, 120), # 1-2 minutes
                'ramp_rate': 0.05            # 5% per second
            },
            AttackSeverity.CRITICAL: {
                'voltage_deviation': 0.25,  # 25% deviation (dangerous)
                'duration_range': (120, 300), # 2-5 minutes
                'ramp_rate': 0.1             # 10% per second
            }
        }

    def generate_overvoltage_attack(self, target_inverter: str, severity: AttackSeverity,
                                   baseline_voltage: float = 1.0) -> FDIAttackVector:
        """Generate overvoltage FDI attack (causes equipment damage risk)"""

        pattern = self.attack_patterns[severity]

        # Calculate target overvoltage
        if severity == AttackSeverity.CRITICAL:
            # Dangerous overvoltage - above critical limit
            target_voltage = self.voltage_limits['critical_upper'] + pattern['voltage_deviation']
        elif severity == AttackSeverity.HIGH:
            # Above VDE upper limit
            target_voltage = self.voltage_limits['upper_limit'] + pattern['voltage_deviation']
        else:
            # Elevated but within limits (harder to detect)
            target_voltage = baseline_voltage + pattern['voltage_deviation']

        duration = random.uniform(*pattern['duration_range'])

        return FDIAttackVector(
            attack_id=f"OV_{target_inverter}_{severity.value}_{int(time.time())}",
            target_parameter="voltage_pu",
            false_value=target_voltage,
            original_value=baseline_voltage,
            injection_method="ramp",
            severity=severity,
            target_type=AttackTarget.VOLTAGE_CONTROL,
            duration_s=duration,
            start_time=time.time(),
            description=f"Overvoltage attack targeting {target_inverter} - "
                       f"Inject {target_voltage:.3f}pu (vs {baseline_voltage:.3f}pu normal)"
        )

    def generate_undervoltage_attack(self, target_inverter: str, severity: AttackSeverity,
                                    baseline_voltage: float = 1.0) -> FDIAttackVector:
        """Generate undervoltage FDI attack (causes blackout risk)"""

        pattern = self.attack_patterns[severity]

        # Calculate target undervoltage
        if severity == AttackSeverity.CRITICAL:
            # Dangerous undervoltage - below critical limit
            target_voltage = self.voltage_limits['critical_lower'] - pattern['voltage_deviation']
        elif severity == AttackSeverity.HIGH:
            # Below VDE lower limit
            target_voltage = self.voltage_limits['lower_limit'] - pattern['voltage_deviation']
        else:
            # Reduced but within limits
            target_voltage = baseline_voltage - pattern['voltage_deviation']

        duration = random.uniform(*pattern['duration_range'])

        return FDIAttackVector(
            attack_id=f"UV_{target_inverter}_{severity.value}_{int(time.time())}",
            target_parameter="voltage_pu",
            false_value=target_voltage,
            original_value=baseline_voltage,
            injection_method="ramp",
            severity=severity,
            target_type=AttackTarget.VOLTAGE_CONTROL,
            duration_s=duration,
            start_time=time.time(),
            description=f"Undervoltage attack targeting {target_inverter} - "
                       f"Inject {target_voltage:.3f}pu (vs {baseline_voltage:.3f}pu normal)"
        )

    def generate_voltage_oscillation_attack(self, target_inverter: str,
                                          frequency_hz: float = 0.1) -> FDIAttackVector:
        """Generate voltage oscillation attack (causes instability)"""

        # Oscillate around dangerous voltage levels
        amplitude = 0.12  # 12% oscillation amplitude
        base_voltage = 1.0

        return FDIAttackVector(
            attack_id=f"VO_{target_inverter}_{frequency_hz}Hz_{int(time.time())}",
            target_parameter="voltage_pu_oscillating",
            false_value=amplitude,  # Use amplitude as false value
            original_value=base_voltage,
            injection_method="oscillating",
            severity=AttackSeverity.HIGH,
            target_type=AttackTarget.VOLTAGE_CONTROL,
            duration_s=180,  # 3 minutes of oscillation
            start_time=time.time(),
            description=f"Voltage oscillation attack on {target_inverter} - "
                       f"{amplitude:.1%} amplitude at {frequency_hz}Hz"
        )


class PowerFDIAttackGenerator:
    """Generates power-based FDI attacks"""

    def generate_false_high_generation_attack(self, target_inverter: str,
                                            rated_power_kw: float) -> FDIAttackVector:
        """Generate false high power generation attack"""

        # Report falsely high power generation (150-300% of rated)
        false_power = rated_power_kw * random.uniform(1.5, 3.0)

        return FDIAttackVector(
            attack_id=f"FHG_{target_inverter}_{int(time.time())}",
            target_parameter="active_power_kw",
            false_value=false_power,
            original_value=rated_power_kw * 0.8,  # Assume 80% normal generation
            injection_method="constant",
            severity=AttackSeverity.MEDIUM,
            target_type=AttackTarget.POWER_CONTROL,
            duration_s=120,
            start_time=time.time(),
            description=f"False high generation attack on {target_inverter} - "
                       f"Report {false_power:.1f}kW vs actual {rated_power_kw*0.8:.1f}kW"
        )

    def generate_zero_power_attack(self, target_inverter: str,
                                 actual_power_kw: float) -> FDIAttackVector:
        """Generate false zero power attack (hide solar generation)"""

        return FDIAttackVector(
            attack_id=f"ZP_{target_inverter}_{int(time.time())}",
            target_parameter="active_power_kw",
            false_value=0.0,
            original_value=actual_power_kw,
            injection_method="constant",
            severity=AttackSeverity.LOW,
            target_type=AttackTarget.POWER_CONTROL,
            duration_s=90,
            start_time=time.time(),
            description=f"Zero power attack on {target_inverter} - "
                       f"Hide {actual_power_kw:.1f}kW generation"
        )

    def generate_power_ramping_attack(self, target_inverter: str,
                                    rated_power_kw: float) -> FDIAttackVector:
        """Generate rapid power ramping attack (grid instability)"""

        # Fake rapid power changes
        target_power = rated_power_kw * 1.2  # 120% of rated

        return FDIAttackVector(
            attack_id=f"PR_{target_inverter}_{int(time.time())}",
            target_parameter="active_power_kw",
            false_value=target_power,
            original_value=rated_power_kw * 0.8,
            injection_method="ramp",
            severity=AttackSeverity.HIGH,
            target_type=AttackTarget.POWER_CONTROL,
            duration_s=60,
            start_time=time.time(),
            description=f"Power ramping attack on {target_inverter} - "
                       f"Fake rapid ramp to {target_power:.1f}kW"
        )


class FrequencyFDIAttackGenerator:
    """Generates frequency-based FDI attacks"""

    def generate_high_frequency_attack(self, target_inverter: str) -> FDIAttackVector:
        """Generate high frequency FDI attack (52-55 Hz)"""

        # European grid: 50Hz nominal, 52Hz+ is dangerous
        false_frequency = random.uniform(52.0, 55.0)

        return FDIAttackVector(
            attack_id=f"HF_{target_inverter}_{int(time.time())}",
            target_parameter="frequency_hz",
            false_value=false_frequency,
            original_value=50.0,  # European nominal frequency
            injection_method="constant",
            severity=AttackSeverity.CRITICAL,
            target_type=AttackTarget.FREQUENCY_CONTROL,
            duration_s=45,
            start_time=time.time(),
            description=f"High frequency attack on {target_inverter} - "
                       f"Inject {false_frequency:.1f}Hz (vs 50.0Hz normal)"
        )

    def generate_low_frequency_attack(self, target_inverter: str) -> FDIAttackVector:
        """Generate low frequency FDI attack (45-48 Hz)"""

        # Low frequency triggers load shedding
        false_frequency = random.uniform(45.0, 48.0)

        return FDIAttackVector(
            attack_id=f"LF_{target_inverter}_{int(time.time())}",
            target_parameter="frequency_hz",
            false_value=false_frequency,
            original_value=50.0,
            injection_method="constant",
            severity=AttackSeverity.CRITICAL,
            target_type=AttackTarget.FREQUENCY_CONTROL,
            duration_s=30,
            start_time=time.time(),
            description=f"Low frequency attack on {target_inverter} - "
                       f"Inject {false_frequency:.1f}Hz (vs 50.0Hz normal)"
        )


class FDIAttackOrchestrator:
    """Orchestrates and executes FDI attack scenarios"""

    def __init__(self, power_system_data: Dict[str, Any],
                 network_simulator: Any = None):
        """
        Initialize FDI attack orchestrator

        Args:
            power_system_data: Power system configuration and state data
            network_simulator: Network simulation instance for attack injection
        """
        self.power_data = power_system_data
        self.network_sim = network_simulator

        # Attack generators
        self.voltage_generator = VoltageFDIAttackGenerator(
            power_system_data.get('vde_voltage_limits', {
                'lower_limit': 0.9, 'upper_limit': 1.1,
                'critical_lower': 0.85, 'critical_upper': 1.15
            })
        )
        self.power_generator = PowerFDIAttackGenerator()
        self.frequency_generator = FrequencyFDIAttackGenerator()

        # Attack execution state
        self.active_attacks = {}
        self.attack_history = []
        self.detection_callbacks = []

        # System monitoring
        self.baseline_state = {}
        self.current_state = {}
        self.voltage_violations = []

    def register_detection_callback(self, callback: Callable):
        """Register callback for attack detection simulation"""
        self.detection_callbacks.append(callback)

    def update_system_state(self, power_results: Dict[str, Any]):
        """Update current system state for attack impact assessment"""
        self.current_state = power_results.copy()

        if not self.baseline_state:
            self.baseline_state = power_results.copy()

    def execute_coordinated_attack_scenario(self, scenario_name: str) -> List[AttackResult]:
        """Execute coordinated FDI attack scenario"""

        print(f"🚨 Executing Coordinated FDI Attack Scenario: {scenario_name}")

        attack_scenarios = {
            'voltage_destabilization': self._scenario_voltage_destabilization,
            'solar_generation_manipulation': self._scenario_solar_manipulation,
            'frequency_deviation_attack': self._scenario_frequency_deviation,
            'cascading_failure_induction': self._scenario_cascading_failure,
            'multi_vector_assault': self._scenario_multi_vector_attack
        }

        if scenario_name not in attack_scenarios:
            print(f"❌ Unknown attack scenario: {scenario_name}")
            return []

        return attack_scenarios[scenario_name]()

    def _scenario_voltage_destabilization(self) -> List[AttackResult]:
        """Scenario 1: Voltage Destabilization Attack"""

        print("   🎯 Target: Voltage destabilization across multiple inverters")

        results = []
        target_inverters = self._select_vulnerable_inverters(max_targets=3)

        for i, inverter_id in enumerate(target_inverters):
            # Stagger attacks for maximum impact
            delay = i * 15  # 15 second delays between attacks

            if i % 2 == 0:
                # Overvoltage attacks on even indices
                attack_vector = self.voltage_generator.generate_overvoltage_attack(
                    inverter_id, AttackSeverity.HIGH
                )
            else:
                # Undervoltage attacks on odd indices
                attack_vector = self.voltage_generator.generate_undervoltage_attack(
                    inverter_id, AttackSeverity.HIGH
                )

            # Execute attack with delay
            result = self._execute_attack_vector(attack_vector, delay_s=delay)
            results.append(result)

        return results

    def _scenario_solar_manipulation(self) -> List[AttackResult]:
        """Scenario 2: Solar Generation Manipulation"""

        print("   🎯 Target: Solar generation data manipulation")

        results = []
        target_inverters = self._select_vulnerable_inverters(max_targets=2)

        for inverter_id in target_inverters:
            # Get inverter info
            inverter_info = self._get_inverter_info(inverter_id)
            if not inverter_info:
                continue

            # Mix of false high generation and zero power attacks
            if random.choice([True, False]):
                attack_vector = self.power_generator.generate_false_high_generation_attack(
                    inverter_id, inverter_info['size_kw']
                )
            else:
                attack_vector = self.power_generator.generate_zero_power_attack(
                    inverter_id, inverter_info['size_kw'] * 0.8
                )

            result = self._execute_attack_vector(attack_vector)
            results.append(result)

        return results

    def _scenario_frequency_deviation(self) -> List[AttackResult]:
        """Scenario 3: Frequency Deviation Attack"""

        print("   🎯 Target: Grid frequency manipulation")

        results = []
        target_inverters = self._select_vulnerable_inverters(max_targets=2)

        for inverter_id in target_inverters:
            # Random high or low frequency attack
            if random.choice([True, False]):
                attack_vector = self.frequency_generator.generate_high_frequency_attack(inverter_id)
            else:
                attack_vector = self.frequency_generator.generate_low_frequency_attack(inverter_id)

            result = self._execute_attack_vector(attack_vector)
            results.append(result)

        return results

    def _scenario_cascading_failure(self) -> List[AttackResult]:
        """Scenario 4: Cascading Failure Induction"""

        print("   🎯 Target: Induce cascading system failures")

        results = []

        # Step 1: Start with voltage attack on most vulnerable inverter
        vulnerable_inverters = self._select_vulnerable_inverters(max_targets=1)
        if vulnerable_inverters:
            primary_target = vulnerable_inverters[0]
            attack1 = self.voltage_generator.generate_overvoltage_attack(
                primary_target, AttackSeverity.CRITICAL
            )
            result1 = self._execute_attack_vector(attack1)
            results.append(result1)

            # Step 2: Follow up with power manipulation on other inverters
            other_targets = self._select_vulnerable_inverters(max_targets=2,
                                                            exclude=[primary_target])
            for target in other_targets:
                inverter_info = self._get_inverter_info(target)
                if inverter_info:
                    attack2 = self.power_generator.generate_power_ramping_attack(
                        target, inverter_info['size_kw']
                    )
                    result2 = self._execute_attack_vector(attack2, delay_s=30)
                    results.append(result2)

        return results

    def _scenario_multi_vector_attack(self) -> List[AttackResult]:
        """Scenario 5: Multi-Vector Simultaneous Attack"""

        print("   🎯 Target: Simultaneous multi-vector attack")

        results = []
        target_inverters = self._select_vulnerable_inverters(max_targets=3)

        attack_types = ['voltage', 'power', 'frequency']

        for i, inverter_id in enumerate(target_inverters):
            attack_type = attack_types[i % len(attack_types)]
            inverter_info = self._get_inverter_info(inverter_id)

            if attack_type == 'voltage':
                attack_vector = self.voltage_generator.generate_overvoltage_attack(
                    inverter_id, AttackSeverity.HIGH
                )
            elif attack_type == 'power' and inverter_info:
                attack_vector = self.power_generator.generate_false_high_generation_attack(
                    inverter_id, inverter_info['size_kw']
                )
            elif attack_type == 'frequency':
                attack_vector = self.frequency_generator.generate_high_frequency_attack(inverter_id)
            else:
                continue

            # Execute all attacks simultaneously (no delay)
            result = self._execute_attack_vector(attack_vector, delay_s=0)
            results.append(result)

        return results

    def _select_vulnerable_inverters(self, max_targets: int = 3,
                                   exclude: List[str] = None) -> List[str]:
        """Select vulnerable inverters for attack targeting"""

        if not self.power_data.get('inverter_targets'):
            # Fallback to any available solar systems
            available = [s['inverter_id'] for s in self.power_data.get('solar_systems', [])]
        else:
            # Select based on vulnerability assessment
            targets = self.power_data['inverter_targets']
            available = [t['inverter_id'] for t in targets if t.get('is_vulnerable', False)]

            if not available:
                # If no vulnerable ones, use any available
                available = [t['inverter_id'] for t in targets]

        # Remove excluded inverters
        if exclude:
            available = [inv for inv in available if inv not in exclude]

        # Select random subset
        num_targets = min(max_targets, len(available))
        return random.sample(available, num_targets) if available else []

    def _get_inverter_info(self, inverter_id: str) -> Optional[Dict[str, Any]]:
        """Get inverter information"""

        for solar in self.power_data.get('solar_systems', []):
            if solar['inverter_id'] == inverter_id:
                return solar

        return None

    def _execute_attack_vector(self, attack_vector: FDIAttackVector,
                              delay_s: float = 0) -> AttackResult:
        """Execute a single FDI attack vector"""

        print(f"   ⚡ Executing: {attack_vector.description}")

        if delay_s > 0:
            time.sleep(delay_s)

        # Record attack start
        attack_start_time = time.time()

        # Execute the attack via network simulator
        attack_success = False
        if self.network_sim:
            attack_params = {
                attack_vector.target_parameter: attack_vector.false_value
            }

            # Extract target inverter from attack_id
            target_inverter = self._extract_target_from_attack_id(attack_vector.attack_id)
            if target_inverter:
                attack_success = self.network_sim.launch_fdi_attack(
                    target_inverter=target_inverter,
                    attack_params=attack_params,
                    duration_seconds=attack_vector.duration_s
                )

        # Simulate attack impact assessment
        impact_assessment = self._assess_attack_impact(attack_vector)

        # Simulate detection latency
        detection_latency = self._simulate_detection_latency(attack_vector)

        # Create attack result
        result = AttackResult(
            attack_vector=attack_vector,
            execution_successful=attack_success,
            voltage_violations=impact_assessment['voltage_violations'],
            power_system_impact=impact_assessment['power_impact'],
            detection_latency_s=detection_latency,
            max_voltage_deviation=impact_assessment['max_voltage_deviation'],
            system_stability_lost=impact_assessment['stability_lost'],
            recovery_time_s=impact_assessment.get('recovery_time_s'),
            damage_assessment=impact_assessment['damage_assessment']
        )

        # Record attack
        self.attack_history.append(result)

        # Trigger detection callbacks
        for callback in self.detection_callbacks:
            try:
                callback(result)
            except Exception as e:
                logging.error(f"Detection callback error: {e}")

        print(f"     ✅ Attack executed - Impact: {impact_assessment['impact_level']}")

        return result

    def _extract_target_from_attack_id(self, attack_id: str) -> Optional[str]:
        """Extract target inverter from attack ID"""
        # Attack ID format: "OV_INV_11_50_high_timestamp"
        parts = attack_id.split('_')
        if len(parts) >= 4:
            return f"{parts[1]}_{parts[2]}_{parts[3]}"  # INV_11_50
        return None

    def _assess_attack_impact(self, attack_vector: FDIAttackVector) -> Dict[str, Any]:
        """Assess the impact of FDI attack on power system"""

        impact_assessment = {
            'voltage_violations': [],
            'power_impact': {},
            'max_voltage_deviation': 0.0,
            'stability_lost': False,
            'damage_assessment': {},
            'impact_level': 'low',
            'recovery_time_s': None
        }

        # Voltage impact assessment
        if attack_vector.target_type == AttackTarget.VOLTAGE_CONTROL:
            deviation = abs(attack_vector.false_value - attack_vector.original_value)
            impact_assessment['max_voltage_deviation'] = deviation

            # Determine impact severity
            if attack_vector.false_value > 1.15:  # Critical overvoltage
                impact_assessment['voltage_violations'].append({
                    'type': 'critical_overvoltage',
                    'value': attack_vector.false_value,
                    'risk': 'equipment_damage'
                })
                impact_assessment['stability_lost'] = True
                impact_assessment['impact_level'] = 'critical'
                impact_assessment['recovery_time_s'] = random.uniform(60, 300)

            elif attack_vector.false_value < 0.85:  # Critical undervoltage
                impact_assessment['voltage_violations'].append({
                    'type': 'critical_undervoltage',
                    'value': attack_vector.false_value,
                    'risk': 'blackout'
                })
                impact_assessment['stability_lost'] = True
                impact_assessment['impact_level'] = 'critical'
                impact_assessment['recovery_time_s'] = random.uniform(30, 180)

            elif deviation > 0.1:  # Outside VDE limits
                impact_assessment['impact_level'] = 'high'
                impact_assessment['recovery_time_s'] = random.uniform(10, 60)

        # Power impact assessment
        elif attack_vector.target_type == AttackTarget.POWER_CONTROL:
            power_deviation = abs(attack_vector.false_value - attack_vector.original_value)
            impact_assessment['power_impact'] = {
                'deviation_kw': power_deviation,
                'type': 'generation_manipulation'
            }

            if power_deviation > 50:  # Large power deviation
                impact_assessment['impact_level'] = 'high'
            elif power_deviation > 20:
                impact_assessment['impact_level'] = 'medium'

        # Frequency impact assessment
        elif attack_vector.target_type == AttackTarget.FREQUENCY_CONTROL:
            freq_deviation = abs(attack_vector.false_value - 50.0)

            if freq_deviation > 2.0:  # >52Hz or <48Hz
                impact_assessment['stability_lost'] = True
                impact_assessment['impact_level'] = 'critical'
                impact_assessment['damage_assessment'] = {
                    'protection_triggered': True,
                    'load_shedding': freq_deviation > 2.5
                }

        return impact_assessment

    def _simulate_detection_latency(self, attack_vector: FDIAttackVector) -> float:
        """Simulate attack detection latency"""

        # Detection latency depends on attack type and severity
        base_latency = {
            AttackSeverity.LOW: random.uniform(30, 120),      # 30s-2min (hard to detect)
            AttackSeverity.MEDIUM: random.uniform(15, 60),    # 15s-1min
            AttackSeverity.HIGH: random.uniform(5, 30),       # 5s-30s
            AttackSeverity.CRITICAL: random.uniform(1, 10)    # 1s-10s (obvious)
        }

        return base_latency.get(attack_vector.severity, 30.0)

    def get_attack_statistics(self) -> Dict[str, Any]:
        """Get comprehensive attack execution statistics"""

        if not self.attack_history:
            return {'total_attacks': 0}

        stats = {
            'total_attacks': len(self.attack_history),
            'successful_attacks': sum(1 for a in self.attack_history if a.execution_successful),
            'attacks_by_severity': {},
            'attacks_by_type': {},
            'average_detection_latency_s': 0,
            'system_stability_compromised': 0,
            'total_voltage_violations': 0,
            'max_voltage_deviation': 0,
            'recovery_times': []
        }

        for attack_result in self.attack_history:
            # Count by severity
            severity = attack_result.attack_vector.severity.value
            stats['attacks_by_severity'][severity] = stats['attacks_by_severity'].get(severity, 0) + 1

            # Count by type
            attack_type = attack_result.attack_vector.target_type.value
            stats['attacks_by_type'][attack_type] = stats['attacks_by_type'].get(attack_type, 0) + 1

            # Aggregate metrics
            stats['average_detection_latency_s'] += attack_result.detection_latency_s
            stats['total_voltage_violations'] += len(attack_result.voltage_violations)
            stats['max_voltage_deviation'] = max(stats['max_voltage_deviation'],
                                                attack_result.max_voltage_deviation)

            if attack_result.system_stability_lost:
                stats['system_stability_compromised'] += 1

            if attack_result.recovery_time_s:
                stats['recovery_times'].append(attack_result.recovery_time_s)

        # Calculate averages
        stats['average_detection_latency_s'] /= len(self.attack_history)
        stats['success_rate'] = stats['successful_attacks'] / stats['total_attacks']
        stats['stability_compromise_rate'] = stats['system_stability_compromised'] / stats['total_attacks']

        if stats['recovery_times']:
            stats['average_recovery_time_s'] = sum(stats['recovery_times']) / len(stats['recovery_times'])
            stats['max_recovery_time_s'] = max(stats['recovery_times'])

        return stats


def main():
    """Test FDI Attack Implementation"""

    print("🚨 Testing False Data Injection Attack Implementation")
    print("=" * 70)

    # Mock power system data (would come from actual power system)
    mock_power_data = {
        'solar_systems': [
            {'inverter_id': 'INV_5_30', 'bus': 5, 'size_kw': 30},
            {'inverter_id': 'INV_10_20', 'bus': 10, 'size_kw': 20},
            {'inverter_id': 'INV_7_25', 'bus': 7, 'size_kw': 25}
        ],
        'inverter_targets': [
            {'inverter_id': 'INV_5_30', 'is_vulnerable': True, 'attack_potential': 0.8},
            {'inverter_id': 'INV_10_20', 'is_vulnerable': False, 'attack_potential': 0.3},
            {'inverter_id': 'INV_7_25', 'is_vulnerable': True, 'attack_potential': 0.6}
        ],
        'vde_voltage_limits': {
            'lower_limit': 0.9, 'upper_limit': 1.1,
            'critical_lower': 0.85, 'critical_upper': 1.15
        }
    }

    # Initialize FDI attack orchestrator
    orchestrator = FDIAttackOrchestrator(mock_power_data)

    print("🎯 Available Attack Scenarios:")
    scenarios = [
        'voltage_destabilization',
        'solar_generation_manipulation',
        'frequency_deviation_attack',
        'cascading_failure_induction',
        'multi_vector_assault'
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"   {i}. {scenario.replace('_', ' ').title()}")

    # Test multiple attack scenarios
    all_results = []

    print(f"\n🚨 Executing Attack Test Scenarios:")

    for scenario in scenarios[:3]:  # Test first 3 scenarios
        print(f"\n--- Testing {scenario.replace('_', ' ').title()} ---")

        results = orchestrator.execute_coordinated_attack_scenario(scenario)
        all_results.extend(results)

        print(f"   ✅ Scenario completed with {len(results)} attack vectors")

        # Brief pause between scenarios
        time.sleep(2)

    # Get comprehensive statistics
    stats = orchestrator.get_attack_statistics()

    print(f"\n📊 FDI Attack Test Results:")
    print(f"   • Total Attacks Executed: {stats['total_attacks']}")
    print(f"   • Success Rate: {stats.get('success_rate', 0):.1%}")
    print(f"   • Average Detection Latency: {stats.get('average_detection_latency_s', 0):.1f}s")
    print(f"   • System Stability Compromised: {stats.get('stability_compromise_rate', 0):.1%}")
    print(f"   • Maximum Voltage Deviation: {stats.get('max_voltage_deviation', 0):.3f}pu")
    print(f"   • Total Voltage Violations: {stats.get('total_voltage_violations', 0)}")

    if stats.get('recovery_times'):
        print(f"   • Average Recovery Time: {stats.get('average_recovery_time_s', 0):.1f}s")
        print(f"   • Maximum Recovery Time: {stats.get('max_recovery_time_s', 0):.1f}s")

    print(f"\n🎯 Attack Distribution:")
    for attack_type, count in stats.get('attacks_by_type', {}).items():
        print(f"   • {attack_type.replace('_', ' ').title()}: {count}")

    print(f"\n⚡ Severity Distribution:")
    for severity, count in stats.get('attacks_by_severity', {}).items():
        print(f"   • {severity.title()}: {count}")

    print(f"\n🏆 FDI Attack Implementation Test Complete!")
    print("    Ready for integration with cyber-physical co-simulation")

    return orchestrator


if __name__ == "__main__":
    orchestrator = main()