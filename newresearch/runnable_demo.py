"""
Runnable Demo: Adaptive FDI Attack Intelligence Framework
========================================================

This demo shows how the framework works without requiring external simulators.
Uses simulated power system responses for demonstration purposes.
"""

import numpy as np
import time
from typing import Dict, List, Any
import json
from datetime import datetime

# Import our framework classes
from adaptive_fdi_research_framework import (
    AttackParameterSpace, SystemResponseAnalyzer, AdaptiveAttackStrategy,
    SystemObservation, AttackLearningState
)

class DemoSimulator:
    """Simple power system simulator for demonstration"""

    def __init__(self):
        self.voltage_levels = {f"bus_{i}": 1.0 for i in range(1, 6)}  # 5-bus system
        self.detection_system_sensitivity = 0.05  # 5% voltage deviation triggers detection

    def simulate_attack(self, attack_params: Dict[str, Any]) -> tuple:
        """Simulate attack execution and system response"""

        # Pre-attack state
        pre_state = SystemObservation(
            voltage_measurements=self.voltage_levels.copy(),
            power_flows={"line_1_2": 25.0, "line_2_3": 15.0},
            frequency_measurement=50.0,
            protection_system_status={"relay_1": "normal", "relay_2": "normal"},
            detection_alerts=[],
            timestamp=time.time()
        )

        # Apply attack (simulate voltage change)
        target_bus = attack_params.get('target_buses', ['bus_1'])[0]
        voltage_change = attack_params.get('target_voltage', 1.0) - 1.0

        # Simulate system response
        new_voltages = self.voltage_levels.copy()
        if target_bus in new_voltages:
            new_voltages[target_bus] += voltage_change

        # Simulate detection
        detection_alerts = []
        if abs(voltage_change) > self.detection_system_sensitivity:
            detection_alerts.append({
                'id': f'alert_{int(time.time())}',
                'type': 'voltage_anomaly',
                'confidence': min(abs(voltage_change) * 10, 1.0),
                'timestamp': time.time()
            })

        # Post-attack state
        post_state = SystemObservation(
            voltage_measurements=new_voltages,
            power_flows={"line_1_2": 25.0 + voltage_change * 10, "line_2_3": 15.0},
            frequency_measurement=50.0 - voltage_change * 0.1,
            protection_system_status={"relay_1": "normal", "relay_2": "normal"},
            detection_alerts=detection_alerts,
            timestamp=time.time()
        )

        return pre_state, post_state

def run_adaptive_learning_demo():
    """Run a complete adaptive learning demonstration"""

    print("🚀 ADAPTIVE FDI ATTACK LEARNING DEMO")
    print("=" * 50)
    print()

    # Initialize components
    power_config = {
        'voltage_limits': {
            'lower_operational': 0.95,
            'upper_operational': 1.05,
            'lower_emergency': 0.9,
            'upper_emergency': 1.1
        },
        'bus_list': [f'bus_{i}' for i in range(1, 6)]
    }

    simulator = DemoSimulator()
    parameter_space = AttackParameterSpace(power_config)
    strategy = AdaptiveAttackStrategy(parameter_space)

    # Learning campaign
    print("📚 Starting Learning Campaign...")
    results = []

    for episode in range(10):  # 10 learning episodes
        print(f"\n🎯 Episode {episode + 1}/10")

        # Get current system state
        current_state = SystemObservation(
            voltage_measurements=simulator.voltage_levels,
            power_flows={"line_1_2": 25.0, "line_2_3": 15.0},
            frequency_measurement=50.0,
            protection_system_status={"relay_1": "normal", "relay_2": "normal"},
            detection_alerts=[],
            timestamp=time.time()
        )

        # Select attack parameters adaptively
        attack_params = strategy.select_attack_parameters(current_state)
        print(f"   Strategy: {strategy.learning_state.value}")
        print(f"   Attack: {attack_params.get('attack_type', 'voltage_manipulation')}")
        print(f"   Target Voltage: {attack_params.get('target_voltage', 1.0):.3f} pu")

        # Execute attack on simulator
        pre_state, post_state = simulator.simulate_attack(attack_params)

        # Analyze system response
        response_analysis = strategy.response_analyzer.analyze_system_response(
            pre_state, attack_params, post_state
        )

        # Learn from results
        strategy.update_strategy_based_on_response(attack_params, response_analysis)

        # Display results
        detected = response_analysis['detection_response']['attack_detected']
        effectiveness = response_analysis['voltage_response']['attack_effectiveness']

        print(f"   Detected: {'Yes' if detected else 'No'}")
        print(f"   Effectiveness: {effectiveness:.3f}")
        print(f"   Voltage Impact: {response_analysis['voltage_response']['max_deviation']:.3f} pu")

        results.append({
            'episode': episode + 1,
            'learning_state': strategy.learning_state.value,
            'detected': detected,
            'effectiveness': effectiveness,
            'voltage_impact': response_analysis['voltage_response']['max_deviation'],
            'knowledge_items': len(strategy.knowledge_base['effective_parameters'])
        })

        time.sleep(0.5)  # Brief pause for readability

    # Analysis
    print(f"\n📊 LEARNING ANALYSIS")
    print("=" * 30)

    detection_rate = sum([r['detected'] for r in results]) / len(results)
    avg_effectiveness = np.mean([r['effectiveness'] for r in results])
    final_knowledge = results[-1]['knowledge_items']

    print(f"   Detection Rate: {detection_rate:.1%}")
    print(f"   Average Effectiveness: {avg_effectiveness:.3f}")
    print(f"   Knowledge Acquired: {final_knowledge} parameter sets")
    print(f"   Learning States Explored: {len(set([r['learning_state'] for r in results]))}")

    # Show learning progression
    print(f"\n📈 LEARNING PROGRESSION:")
    for i, result in enumerate(results):
        status = "🔴" if result['detected'] else "🟢"
        print(f"   Episode {result['episode']:2d}: {status} {result['learning_state']:12s} "
              f"Eff:{result['effectiveness']:.2f} Impact:{result['voltage_impact']:.3f}")

    print(f"\n✅ DEMO COMPLETE!")
    print(f"   Framework successfully demonstrated adaptive learning")
    print(f"   Ready for integration with real power system simulators")

    return results

def main():
    """Main demo execution"""
    try:
        results = run_adaptive_learning_demo()

        # Save results
        with open('/home/azureuser/aareas/newresearch/demo_results.json', 'w') as f:
            # Convert any non-serializable objects
            serializable_results = []
            for r in results:
                serializable_results.append({
                    'episode': r['episode'],
                    'learning_state': r['learning_state'],
                    'detected': bool(r['detected']),
                    'effectiveness': float(r['effectiveness']),
                    'voltage_impact': float(r['voltage_impact']),
                    'knowledge_items': int(r['knowledge_items'])
                })

            json.dump({
                'demo_type': 'Adaptive FDI Attack Learning Demo',
                'timestamp': datetime.now().isoformat(),
                'results': serializable_results
            }, f, indent=2)

        print(f"\n💾 Results saved to: demo_results.json")
        return True

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
