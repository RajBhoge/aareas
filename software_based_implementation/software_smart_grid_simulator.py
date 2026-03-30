"""
Software-Based Smart Grid Simulator
100% Software Implementation - No Hardware Dependencies

This replaces physical smart grid infrastructure with realistic mathematical models
Based on research papers but implemented as pure software simulation
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import threading
import time
from typing import Dict, List, Any


class SoftwareSmartGridSimulator:
    """
    Complete software-based smart grid simulation
    Replaces physical infrastructure with realistic mathematical models
    """

    def __init__(self, n_consumers=1000, simulation_days=7):
        self.n_consumers = n_consumers
        self.simulation_days = simulation_days
        self.grid_state = {}
        self.attack_scenarios = []

        print(f"📊 Software Smart Grid Simulator Initialized")
        print(f"   Consumers: {n_consumers}")
        print(f"   Simulation Period: {simulation_days} days")
        print(f"   Expected Data Points: {n_consumers * simulation_days * 24:,}")

    def generate_realistic_grid_data(self) -> pd.DataFrame:
        """Generate mathematically realistic smart grid data"""

        print("🔧 Generating realistic smart grid data using mathematical models...")

        # Consumer load profiles (based on research patterns)
        consumer_profiles = {
            'residential': {
                'base_load': 3.5,      # kW average
                'peak_ratio': 2.0,     # Peak vs base load
                'variability': 0.3,    # Random variation
                'peak_hours': [18, 19, 20],  # Evening peak
                'low_hours': [2, 3, 4]       # Night low
            },
            'commercial': {
                'base_load': 15.0,
                'peak_ratio': 1.8,
                'variability': 0.2,
                'peak_hours': [10, 11, 14, 15],  # Business hours
                'low_hours': [22, 23, 0, 1]
            },
            'industrial': {
                'base_load': 50.0,
                'peak_ratio': 1.3,
                'variability': 0.1,
                'peak_hours': [8, 9, 13, 14],    # Shift patterns
                'low_hours': [0, 1, 2, 3]
            }
        }

        # Time-based patterns (research-validated)
        hours = np.arange(24)
        daily_pattern = 0.7 + 0.3 * np.sin(2 * np.pi * (hours - 6) / 24)  # Peak at 6 PM
        weekly_pattern = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 0.9, 0.85])  # Weekday vs weekend

        # Seasonal variation
        days_in_simulation = self.simulation_days
        seasonal_pattern = 1.0 + 0.2 * np.sin(2 * np.pi * np.arange(days_in_simulation) / 365)

        # Generate data for each consumer
        all_data = []
        np.random.seed(42)  # Reproducible for course project

        for consumer_id in range(self.n_consumers):
            if consumer_id % 100 == 0:
                print(f"   Processing consumer {consumer_id}/{self.n_consumers}")

            # Random consumer type assignment
            consumer_type = np.random.choice(
                ['residential', 'commercial', 'industrial'],
                p=[0.75, 0.20, 0.05]  # Realistic distribution
            )
            profile = consumer_profiles[consumer_type]

            # Consumer-specific characteristics
            consumer_base_load = profile['base_load'] * np.random.uniform(0.8, 1.2)
            consumer_variability = profile['variability'] * np.random.uniform(0.5, 1.5)

            # Generate time series for this consumer
            timestamps = pd.date_range(
                start='2024-01-01',
                periods=self.simulation_days * 24,
                freq='H'
            )

            for i, timestamp in enumerate(timestamps):
                hour_of_day = timestamp.hour
                day_of_week = timestamp.weekday()
                day_of_simulation = i // 24

                # Calculate realistic load using multiple factors
                base_load = consumer_base_load

                # Daily pattern
                daily_factor = daily_pattern[hour_of_day]

                # Weekly pattern
                weekly_factor = weekly_pattern[day_of_week]

                # Seasonal pattern
                seasonal_factor = seasonal_pattern[day_of_simulation % len(seasonal_pattern)]

                # Peak/low hour adjustments
                if hour_of_day in profile['peak_hours']:
                    peak_factor = profile['peak_ratio']
                elif hour_of_day in profile['low_hours']:
                    peak_factor = 0.6
                else:
                    peak_factor = 1.0

                # Random variations
                random_factor = 1.0 + np.random.normal(0, consumer_variability)

                # Calculate final load
                load = (base_load * daily_factor * weekly_factor *
                       seasonal_factor * peak_factor * random_factor)
                load = max(0.1, load)  # Ensure positive load

                # Grid parameters (realistic ranges)
                voltage = np.random.normal(230, 3)  # Grid voltage ±3V variation
                frequency = np.random.normal(50, 0.05)  # Frequency ±0.05Hz
                power_factor = np.random.uniform(0.85, 0.95)

                # Additional smart grid measurements
                reactive_power = load * np.tan(np.arccos(power_factor))
                apparent_power = load / power_factor

                all_data.append({
                    'timestamp': timestamp,
                    'consumer_id': f'consumer_{consumer_id:04d}',
                    'consumer_type': consumer_type,
                    'load_kw': load,
                    'voltage_v': voltage,
                    'frequency_hz': frequency,
                    'power_factor': power_factor,
                    'reactive_power_kvar': reactive_power,
                    'apparent_power_kva': apparent_power,
                    'daily_factor': daily_factor,
                    'weekly_factor': weekly_factor,
                    'seasonal_factor': seasonal_factor,
                    'is_attack': False,
                    'attack_type': None,
                    'anomaly_score': 0.0
                })

        df = pd.DataFrame(all_data)
        print(f"✅ Generated {len(df):,} realistic smart grid data points")
        return df

    def inject_software_based_attacks(self, data_df: pd.DataFrame, attack_ratio: float = 0.05) -> pd.DataFrame:
        """Inject realistic attack scenarios through software simulation"""

        print(f"⚔️ Injecting software-based attack scenarios (ratio: {attack_ratio:.1%})")

        attack_types = {
            'false_data_injection': {
                'description': 'Modify meter readings with false values',
                'target_columns': ['load_kw'],
                'impact': lambda x: x * np.random.uniform(0.1, 5.0),
                'frequency': 0.4,  # 40% of attacks
                'severity': 'high'
            },
            'load_altering_attack': {
                'description': 'Artificially increase/decrease reported load',
                'target_columns': ['load_kw'],
                'impact': lambda x: max(0.1, x + np.random.uniform(-x*0.8, x*2.0)),
                'frequency': 0.3,
                'severity': 'medium'
            },
            'voltage_manipulation': {
                'description': 'Manipulate voltage readings to dangerous levels',
                'target_columns': ['voltage_v'],
                'impact': lambda x: np.random.uniform(180, 280),  # Outside safe range
                'frequency': 0.15,
                'severity': 'critical'
            },
            'frequency_attack': {
                'description': 'Frequency instability attack',
                'target_columns': ['frequency_hz'],
                'impact': lambda x: np.random.uniform(47, 53),  # Outside normal range
                'frequency': 0.1,
                'severity': 'high'
            },
            'meter_tampering': {
                'description': 'Physical meter tampering simulation',
                'target_columns': ['load_kw', 'power_factor'],
                'impact': lambda x: np.random.uniform(0.01, x*0.1),  # Near zero readings
                'frequency': 0.05,
                'severity': 'medium'
            }
        }

        # Calculate number of attacks
        n_attacks = int(len(data_df) * attack_ratio)
        attack_indices = np.random.choice(data_df.index, n_attacks, replace=False)

        attack_df = data_df.copy()
        attack_statistics = {attack_type: 0 for attack_type in attack_types.keys()}

        print(f"   Injecting {n_attacks:,} attack scenarios...")

        for idx in attack_indices:
            # Select attack type based on frequency
            attack_probs = [info['frequency'] for info in attack_types.values()]
            attack_probs = np.array(attack_probs) / sum(attack_probs)  # Normalize

            attack_type = np.random.choice(list(attack_types.keys()), p=attack_probs)
            attack_info = attack_types[attack_type]

            # Apply attack to target columns
            for column in attack_info['target_columns']:
                if column in attack_df.columns:
                    original_value = attack_df.loc[idx, column]
                    attacked_value = attack_info['impact'](original_value)
                    attack_df.loc[idx, column] = attacked_value

            # Mark as attack and add metadata
            attack_df.loc[idx, 'is_attack'] = True
            attack_df.loc[idx, 'attack_type'] = attack_type
            attack_df.loc[idx, 'attack_severity'] = attack_info['severity']
            attack_df.loc[idx, 'anomaly_score'] = np.random.uniform(0.7, 1.0)  # High anomaly

            attack_statistics[attack_type] += 1

        # Calculate attack impact metrics
        self._calculate_attack_impact(data_df, attack_df)

        print("✅ Attack injection completed:")
        for attack_type, count in attack_statistics.items():
            if count > 0:
                print(f"   {attack_type}: {count} instances")

        print(f"   Total attack samples: {attack_df['is_attack'].sum():,}")
        print(f"   Total normal samples: {(~attack_df['is_attack']).sum():,}")

        return attack_df

    def _calculate_attack_impact(self, original_df: pd.DataFrame, attacked_df: pd.DataFrame):
        """Calculate the impact of attacks on grid stability metrics"""

        attack_mask = attacked_df['is_attack']

        if attack_mask.sum() == 0:
            return

        # Calculate grid stability metrics
        original_load_std = original_df['load_kw'].std()
        attacked_load_std = attacked_df['load_kw'].std()

        original_voltage_range = original_df['voltage_v'].max() - original_df['voltage_v'].min()
        attacked_voltage_range = attacked_df['voltage_v'].max() - attacked_df['voltage_v'].min()

        original_freq_std = original_df['frequency_hz'].std()
        attacked_freq_std = attacked_df['frequency_hz'].std()

        # Store impact metrics
        self.attack_impact_metrics = {
            'load_variability_increase': (attacked_load_std / original_load_std) - 1.0,
            'voltage_range_increase': (attacked_voltage_range / original_voltage_range) - 1.0,
            'frequency_instability_increase': (attacked_freq_std / original_freq_std) - 1.0,
            'grid_stability_score': self._calculate_stability_score(attacked_df)
        }

    def _calculate_stability_score(self, df: pd.DataFrame) -> float:
        """Calculate overall grid stability score (0-1, higher is better)"""

        # Voltage stability (ideal: 230V ± 5V)
        voltage_deviation = np.abs(df['voltage_v'] - 230).mean()
        voltage_stability = max(0, 1 - voltage_deviation / 20)  # Normalize

        # Frequency stability (ideal: 50Hz ± 0.2Hz)
        frequency_deviation = np.abs(df['frequency_hz'] - 50).mean()
        frequency_stability = max(0, 1 - frequency_deviation / 1)

        # Load balance (avoid extreme variations)
        load_cv = df['load_kw'].std() / df['load_kw'].mean()  # Coefficient of variation
        load_stability = max(0, 1 - load_cv)

        # Overall stability (weighted average)
        stability_score = (0.4 * voltage_stability +
                          0.3 * frequency_stability +
                          0.3 * load_stability)

        return stability_score

    def generate_multi_scenario_attacks(self, base_data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Generate multiple attack scenarios for comprehensive testing"""

        print("🎯 Generating multiple attack scenarios for comprehensive evaluation...")

        scenarios = {
            'low_intensity': {'ratio': 0.02, 'description': 'Low-intensity distributed attacks'},
            'medium_intensity': {'ratio': 0.05, 'description': 'Medium-intensity coordinated attacks'},
            'high_intensity': {'ratio': 0.10, 'description': 'High-intensity targeted attacks'},
            'coordinated_attack': {'ratio': 0.03, 'description': 'Coordinated multi-vector attacks'},
            'persistent_attack': {'ratio': 0.01, 'description': 'Long-duration persistent attacks'}
        }

        scenario_datasets = {}

        for scenario_name, config in scenarios.items():
            print(f"   Generating {scenario_name} scenario...")

            if scenario_name == 'coordinated_attack':
                # Special handling for coordinated attacks
                scenario_data = self._generate_coordinated_attacks(base_data, config['ratio'])
            elif scenario_name == 'persistent_attack':
                # Special handling for persistent attacks
                scenario_data = self._generate_persistent_attacks(base_data, config['ratio'])
            else:
                # Standard attack injection
                scenario_data = self.inject_software_based_attacks(base_data.copy(), config['ratio'])

            scenario_datasets[scenario_name] = scenario_data

            # Calculate scenario-specific metrics
            attack_count = scenario_data['is_attack'].sum()
            stability_score = self._calculate_stability_score(scenario_data)

            print(f"     Attacks: {attack_count:,}, Stability Score: {stability_score:.3f}")

        print("✅ Multi-scenario attack generation completed")
        return scenario_datasets

    def _generate_coordinated_attacks(self, base_data: pd.DataFrame, attack_ratio: float) -> pd.DataFrame:
        """Generate coordinated attacks targeting multiple consumers simultaneously"""

        coordinated_data = base_data.copy()
        n_attacks = int(len(base_data) * attack_ratio)

        # Select time windows for coordinated attacks
        unique_timestamps = base_data['timestamp'].unique()
        attack_timestamps = np.random.choice(unique_timestamps, n_attacks // 10, replace=False)

        for timestamp in attack_timestamps:
            # Select multiple consumers at the same time
            timestamp_data = coordinated_data[coordinated_data['timestamp'] == timestamp]
            target_consumers = np.random.choice(timestamp_data.index,
                                              min(10, len(timestamp_data)),
                                              replace=False)

            for idx in target_consumers:
                # Apply coordinated attack (typically load manipulation)
                multiplier = np.random.uniform(3.0, 8.0)  # Significant impact
                coordinated_data.loc[idx, 'load_kw'] *= multiplier
                coordinated_data.loc[idx, 'is_attack'] = True
                coordinated_data.loc[idx, 'attack_type'] = 'coordinated_load_attack'
                coordinated_data.loc[idx, 'attack_severity'] = 'critical'
                coordinated_data.loc[idx, 'anomaly_score'] = 0.9

        return coordinated_data

    def _generate_persistent_attacks(self, base_data: pd.DataFrame, attack_ratio: float) -> pd.DataFrame:
        """Generate persistent attacks that last for extended periods"""

        persistent_data = base_data.copy()

        # Select consumers for persistent attacks
        consumers = base_data['consumer_id'].unique()
        n_target_consumers = max(1, int(len(consumers) * attack_ratio))
        target_consumers = np.random.choice(consumers, n_target_consumers, replace=False)

        for consumer in target_consumers:
            consumer_data = persistent_data[persistent_data['consumer_id'] == consumer]

            # Select a continuous time period (e.g., 24-72 hours)
            attack_duration_hours = np.random.randint(24, 73)
            start_hour = np.random.randint(0, len(consumer_data) - attack_duration_hours)

            attack_indices = consumer_data.index[start_hour:start_hour + attack_duration_hours]

            # Apply persistent meter tampering
            for idx in attack_indices:
                persistent_data.loc[idx, 'load_kw'] *= 0.1  # Reduce to 10% (tampering)
                persistent_data.loc[idx, 'is_attack'] = True
                persistent_data.loc[idx, 'attack_type'] = 'persistent_tampering'
                persistent_data.loc[idx, 'attack_severity'] = 'medium'
                persistent_data.loc[idx, 'anomaly_score'] = 0.8

        return persistent_data

    def visualize_grid_data(self, data: pd.DataFrame, save_plots: bool = True):
        """Create visualizations of the smart grid data"""

        print("📊 Generating smart grid data visualizations...")

        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('Software-Based Smart Grid Simulation Results', fontsize=16)

        # Plot 1: Load patterns by consumer type
        for i, consumer_type in enumerate(['residential', 'commercial', 'industrial']):
            type_data = data[data['consumer_type'] == consumer_type]
            if not type_data.empty:
                hourly_avg = type_data.groupby(type_data['timestamp'].dt.hour)['load_kw'].mean()
                axes[0, i].plot(hourly_avg.index, hourly_avg.values, 'b-', linewidth=2)
                axes[0, i].set_title(f'{consumer_type.title()} Load Pattern')
                axes[0, i].set_xlabel('Hour of Day')
                axes[0, i].set_ylabel('Average Load (kW)')
                axes[0, i].grid(True)

        # Plot 2: Attack distribution
        if 'attack_type' in data.columns:
            attack_data = data[data['is_attack'] == True]
            if not attack_data.empty:
                attack_counts = attack_data['attack_type'].value_counts()
                axes[1, 0].bar(range(len(attack_counts)), attack_counts.values)
                axes[1, 0].set_title('Attack Type Distribution')
                axes[1, 0].set_xticks(range(len(attack_counts)))
                axes[1, 0].set_xticklabels(attack_counts.index, rotation=45, ha='right')
                axes[1, 0].set_ylabel('Number of Attacks')

        # Plot 3: Voltage stability
        axes[1, 1].hist(data['voltage_v'], bins=50, alpha=0.7, edgecolor='black')
        axes[1, 1].axvline(230, color='red', linestyle='--', label='Nominal Voltage')
        axes[1, 1].set_title('Voltage Distribution')
        axes[1, 1].set_xlabel('Voltage (V)')
        axes[1, 1].set_ylabel('Frequency')
        axes[1, 1].legend()

        # Plot 4: Frequency stability
        axes[1, 2].hist(data['frequency_hz'], bins=50, alpha=0.7, edgecolor='black')
        axes[1, 2].axvline(50, color='red', linestyle='--', label='Nominal Frequency')
        axes[1, 2].set_title('Frequency Distribution')
        axes[1, 2].set_xlabel('Frequency (Hz)')
        axes[1, 2].set_ylabel('Frequency')
        axes[1, 2].legend()

        plt.tight_layout()

        if save_plots:
            plt.savefig('/home/azureuser/aareas/software_grid_simulation.png', dpi=300, bbox_inches='tight')
            print("📁 Visualization saved to software_grid_simulation.png")

        plt.show()

# Demo execution
if __name__ == "__main__":
    print("🖥️ Software-Based Smart Grid Simulator Demo")
    print("=" * 60)

    # Initialize simulator with course-appropriate size
    simulator = SoftwareSmartGridSimulator(
        n_consumers=100,  # Reduced for demo
        simulation_days=7   # 1 week
    )

    # Generate baseline data
    grid_data = simulator.generate_realistic_grid_data()

    # Inject attacks
    grid_data_with_attacks = simulator.inject_software_based_attacks(grid_data, attack_ratio=0.05)

    # Generate multiple scenarios
    scenarios = simulator.generate_multi_scenario_attacks(grid_data)

    # Display results
    print(f"\n📊 Simulation Results Summary:")
    print(f"   Total Data Points: {len(grid_data_with_attacks):,}")
    print(f"   Consumer Types: {grid_data_with_attacks['consumer_type'].nunique()}")
    print(f"   Time Period: {grid_data_with_attacks['timestamp'].min()} to {grid_data_with_attacks['timestamp'].max()}")
    print(f"   Attack Scenarios Generated: {len(scenarios)}")

    if hasattr(simulator, 'attack_impact_metrics'):
        print(f"\n⚠️ Attack Impact Analysis:")
        for metric, value in simulator.attack_impact_metrics.items():
            print(f"   {metric}: {value:.3f}")

    # Save data
    grid_data_with_attacks.to_csv('/home/azureuser/aareas/software_smart_grid_data.csv', index=False)
    print(f"\n💾 Data saved to software_smart_grid_data.csv")

    # Create visualizations
    simulator.visualize_grid_data(grid_data_with_attacks)

    print("\n✅ Software-Based Smart Grid Simulation Complete!")