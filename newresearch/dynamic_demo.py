"""
Dynamic Adaptive FDI Demo - More Varied Learning Behavior
=========================================================

This version shows more dynamic learning progression by:
1. Using more aggressive exploration
2. Varying detection sensitivity over time
3. Adding randomness to system responses
"""

import numpy as np
import time
import random
from typing import Dict, List, Any
import json
from datetime import datetime

# Import our framework classes
from adaptive_fdi_research_framework import (
    AttackParameterSpace, SystemResponseAnalyzer, AdaptiveAttackStrategy,
    SystemObservation, AttackLearningState
)

class DynamicDemoSimulator:
    """Enhanced power system simulator with more dynamic responses"""

    def __init__(self):
        self.voltage_levels = {f"bus_{i}": 1.0 + random.uniform(-0.01, 0.01) for i in range(1, 6)}
        self.base_detection_sensitivity = 0.04  # 4% base sensitivity
        self.episode_count = 0

    def simulate_attack(self, attack_params: Dict[str, Any]) -> tuple:
        """Simulate attack with dynamic system responses"""

        self.episode_count += 1

        # Pre-attack state (with some natural variation)
        pre_voltages = {}
        for bus in self.voltage_levels:
            # Add natural voltage fluctuation
            pre_voltages[bus] = self.voltage_levels[bus] + random.uniform(-0.005, 0.005)

        pre_state = SystemObservation(
            voltage_measurements=pre_voltages,
            power_flows={"line_1_2": 25.0 + random.uniform(-2, 2), "line_2_3": 15.0 + random.uniform(-1, 1)},
            frequency_measurement=50.0 + random.uniform(-0.01, 0.01),
            protection_system_status={"relay_1": "normal", "relay_2": "normal"},
            detection_alerts=[],
            timestamp=time.time()
        )

        # Apply attack with system response variation
        target_bus = attack_params.get('target_buses', ['bus_1'])[0]
        intended_voltage_change = attack_params.get('target_voltage', 1.0) - 1.0

        # System doesn't always respond exactly as intended
        response_factor = random.uniform(0.8, 1.2)  # 80-120% response
        actual_voltage_change = intended_voltage_change * response_factor

        # Simulate cascading effects on other buses
        new_voltages = pre_voltages.copy()
        if target_bus in new_voltages:
            new_voltages[target_bus] += actual_voltage_change

            # Cascading effects on neighboring buses (realistic power system behavior)
            for bus in new_voltages:
                if bus != target_bus:
                    cascade_effect = actual_voltage_change * random.uniform(0.1, 0.3)
                    new_voltages[bus] += cascade_effect

        # Dynamic detection system (gets more sensitive over time)
        detection_sensitivity = self.base_detection_sensitivity * (1 - self.episode_count * 0.005)
        detection_sensitivity = max(detection_sensitivity, 0.02)  # Minimum 2% threshold

        # Detection probability based on multiple factors
        max_voltage_change = max([abs(new_voltages[bus] - pre_voltages[bus]) for bus in new_voltages])
        detection_probability = max_voltage_change / detection_sensitivity

        # Add some randomness to detection (realistic system behavior)
        detection_probability *= random.uniform(0.8, 1.2)

        detection_alerts = []
        if random.random() < min(detection_probability, 0.9):  # Max 90% detection probability
            confidence = min(detection_probability, 1.0)
            detection_alerts.append({
                'id': f'alert_{int(time.time())}_{self.episode_count}',
                'type': 'voltage_anomaly',
                'confidence': confidence,
                'timestamp': time.time(),
                'severity': 'high' if confidence > 0.8 else 'medium' if confidence > 0.5 else 'low'
            })

        # Update system state for next episode
        self.voltage_levels = {bus: v + random.uniform(-0.002, 0.002) for bus, v in new_voltages.items()}

        # Post-attack state
        post_state = SystemObservation(
            voltage_measurements=new_voltages,
            power_flows={"line_1_2": 25.0 + actual_voltage_change * 15, "line_2_3": 15.0 + actual_voltage_change * 8},
            frequency_measurement=50.0 - actual_voltage_change * 0.2 + random.uniform(-0.005, 0.005),
            protection_system_status={"relay_1": "normal", "relay_2": "normal"},
            detection_alerts=detection_alerts,
            timestamp=time.time()
        )

        return pre_state, post_state

class EnhancedAdaptiveStrategy(AdaptiveAttackStrategy):
    """Enhanced strategy with more dynamic exploration"""

    def _exploration_strategy(self, system_state: SystemObservation) -> Dict[str, Any]:
        """More dynamic exploration strategy"""

        # Progressive exploration - start small, gradually increase
        episode_factor = len(self.knowledge_base['effective_parameters']) + 1
        base_voltage_change = 0.02 + (episode_factor * 0.01)  # 2% to 8% progression

        # Random exploration within safe bounds
        exploration_range = random.uniform(0.8, 1.2)
        target_voltage = 1.0 + (base_voltage_change * exploration_range)

        return {
            'attack_type': 'voltage_manipulation',
            'target_voltage': target_voltage,
            'attack_duration': random.randint(20, 60),
            'injection_rate': random.uniform(0.001, 0.008),
            'target_buses': [random.choice([f'bus_{i}' for i in range(1, 6)])]
        }

    def _exploitation_strategy(self, system_state: SystemObservation) -> Dict[str, Any]:
        """Use learned effective parameters with some variation"""

        if not self.knowledge_base['effective_parameters']:
            return self._exploration_strategy(system_state)

        # Get best performing parameters
        best_params = max(
            self.knowledge_base['effective_parameters'].items(),
            key=lambda x: x[1]['effectiveness'] * (0.5 if x[1]['detected'] else 1.0)
        )[1]

        # Add some variation to avoid detection patterns
        variation_factor = random.uniform(0.9, 1.1)

        return {
            'attack_type': 'voltage_manipulation',
            'target_voltage': 1.0 + (0.06 * variation_factor),  # Around 6% with variation
            'attack_duration': random.randint(40, 80),
            'injection_rate': random.uniform(0.005, 0.01),
            'target_buses': [random.choice([f'bus_{i}' for i in range(1, 6)])]
        }

    def _evasion_strategy(self, system_state: SystemObservation) -> Dict[str, Any]:
        """Stealth strategy when detection rate is high"""

        return {
            'attack_type': 'stealth_voltage_manipulation',
            'target_voltage': 1.0 + random.uniform(0.01, 0.025),  # Very small changes
            'attack_duration': random.randint(60, 120),  # Longer duration
            'injection_rate': 0.001,  # Very slow injection
            'target_buses': [random.choice([f'bus_{i}' for i in range(1, 6)])]
        }

def run_dynamic_learning_demo():
    """Run enhanced learning demonstration"""

    print("🚀 DYNAMIC ADAPTIVE FDI ATTACK LEARNING DEMO")
    print("=" * 55)
    print()

    # Initialize components
    power_config = {
        'voltage_limits': {
            'lower_operational': 0.95, 'upper_operational': 1.05,
            'lower_emergency': 0.9, 'upper_emergency': 1.1
        },
        'bus_list': [f'bus_{i}' for i in range(1, 6)]
    }

    simulator = DynamicDemoSimulator()
    parameter_space = AttackParameterSpace(power_config)
    strategy = EnhancedAdaptiveStrategy(parameter_space)

    print("📚 Starting Enhanced Learning Campaign...")
    print("   • More aggressive exploration")
    print("   • Dynamic system responses")
    print("   • Adaptive detection system")
    print()

    results = []

    for episode in range(20):  # More episodes to show progression
        print(f"🎯 Episode {episode + 1}/20")

        # Get current system state
        current_voltages = simulator.voltage_levels
        current_state = SystemObservation(
            voltage_measurements=current_voltages,
            power_flows={"line_1_2": 25.0, "line_2_3": 15.0},
            frequency_measurement=50.0,
            protection_system_status={"relay_1": "normal", "relay_2": "normal"},
            detection_alerts=[],
            timestamp=time.time()
        )

        # Select attack parameters
        attack_params = strategy.select_attack_parameters(current_state)

        print(f"   Strategy: {strategy.learning_state.value}")
        print(f"   Target Voltage: {attack_params.get('target_voltage', 1.0):.3f} pu")
        print(f"   Target Bus: {attack_params.get('target_buses', ['bus_1'])[0]}")

        # Execute attack
        pre_state, post_state = simulator.simulate_attack(attack_params)

        # Analyze response
        response_analysis = strategy.response_analyzer.analyze_system_response(
            pre_state, attack_params, post_state
        )

        # Learn from results
        strategy.update_strategy_based_on_response(attack_params, response_analysis)

        # Display results
        detected = response_analysis['detection_response']['attack_detected']
        effectiveness = response_analysis['voltage_response']['attack_effectiveness']
        max_impact = response_analysis['voltage_response']['max_deviation']

        status_icon = "🔴" if detected else "🟢"
        print(f"   {status_icon} Detected: {'Yes' if detected else 'No'}")
        print(f"   📈 Effectiveness: {effectiveness:.3f}")
        print(f"   ⚡ Max Voltage Impact: {max_impact:.3f} pu")
        print(f"   🧠 Knowledge Items: {len(strategy.knowledge_base['effective_parameters'])}")
        print()

        results.append({
            'episode': episode + 1,
            'learning_state': strategy.learning_state.value,
            'target_voltage': attack_params.get('target_voltage', 1.0),
            'target_bus': attack_params.get('target_buses', ['bus_1'])[0],
            'detected': detected,
            'effectiveness': effectiveness,
            'voltage_impact': max_impact,
            'knowledge_items': len(strategy.knowledge_base['effective_parameters'])
        })

        time.sleep(0.3)  # Brief pause

    # Enhanced Analysis
    print("📊 ENHANCED LEARNING ANALYSIS")
    print("=" * 35)

    detection_rate = sum([r['detected'] for r in results]) / len(results)
    avg_effectiveness = np.mean([r['effectiveness'] for r in results])
    final_knowledge = results[-1]['knowledge_items']
    states_used = len(set([r['learning_state'] for r in results]))

    print(f"   Overall Detection Rate: {detection_rate:.1%}")
    print(f"   Average Effectiveness: {avg_effectiveness:.3f}")
    print(f"   Knowledge Acquired: {final_knowledge} parameter sets")
    print(f"   Learning States Used: {states_used}")
    print()

    # Show learning state transitions
    print("🔄 LEARNING STATE EVOLUTION:")
    current_state = None
    for result in results:
        if result['learning_state'] != current_state:
            current_state = result['learning_state']
            print(f"   Episode {result['episode']:2d}: Switched to {current_state}")
    print()

    # Show most effective attacks
    effective_attacks = sorted([r for r in results if r['effectiveness'] > 0.05],
                              key=lambda x: x['effectiveness'], reverse=True)

    if effective_attacks:
        print("🏆 TOP PERFORMING ATTACKS:")
        for i, attack in enumerate(effective_attacks[:3]):
            detection_status = "🔴 DETECTED" if attack['detected'] else "🟢 STEALTH"
            print(f"   #{i+1}: Episode {attack['episode']} - "
                  f"Eff:{attack['effectiveness']:.3f} "
                  f"Impact:{attack['voltage_impact']:.3f} "
                  f"{detection_status}")
    print()

    print("✅ ENHANCED DEMO COMPLETE!")
    print("   Framework demonstrated dynamic learning and adaptation")

    return results

def main():
    """Main enhanced demo execution"""
    try:
        results = run_dynamic_learning_demo()

        # Save enhanced results
        with open('/home/azureuser/aareas/newresearch/dynamic_demo_results.json', 'w') as f:
            serializable_results = []
            for r in results:
                serializable_results.append({
                    k: (float(v) if isinstance(v, (np.float64, np.float32)) else
                        bool(v) if isinstance(v, (np.bool_,)) else
                        int(v) if isinstance(v, (np.int64, np.int32)) else v)
                    for k, v in r.items()
                })

            json.dump({
                'demo_type': 'Dynamic Adaptive FDI Attack Learning Demo',
                'timestamp': datetime.now().isoformat(),
                'total_episodes': len(results),
                'results': serializable_results
            }, f, indent=2)

        print(f"💾 Enhanced results saved to: dynamic_demo_results.json")
        return True

    except Exception as e:
        print(f"❌ Enhanced demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
