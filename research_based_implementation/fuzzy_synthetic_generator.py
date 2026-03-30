"""
NGIDS-DS Fuzzy Synthetic Data Generator
Based on: "Generating realistic intrusion detection system dataset based on fuzzy qualitative modeling"
Computer Networks 2017 Paper Analysis

This implementation follows the research paper's methodology:
- Sugeno fuzzy inference model for synthetic data generation
- Quality of realism metric using fuzzy logic quantification
- NGIDS-DS (Next-Generation IDS Dataset) approach
- Integration with IXIA Perfect Storm methodology (simulated)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import matplotlib.pyplot as plt


@dataclass
class FuzzyRule:
    """Fuzzy rule structure for Sugeno inference system"""
    antecedent: Dict[str, str]  # Variable -> linguistic term
    consequent: float           # Sugeno consequent value
    weight: float = 1.0


class SugenoFuzzyInferenceSystem:
    """
    Sugeno Fuzzy Inference Model implementation
    Based on research paper methodology for realistic data generation
    """

    def __init__(self):
        self.membership_functions = {}
        self.rules = []
        self.variables = []

    def add_membership_function(self, variable: str, term: str, mf_type: str, params: List[float]):
        """
        Add membership function for a variable

        Args:
            variable: Input variable name
            term: Linguistic term (e.g., 'low', 'medium', 'high')
            mf_type: Type of MF ('triangular', 'trapezoidal', 'gaussian')
            params: Parameters for the membership function
        """
        if variable not in self.membership_functions:
            self.membership_functions[variable] = {}
            self.variables.append(variable)

        self.membership_functions[variable][term] = {
            'type': mf_type,
            'params': params
        }

    def _triangular_mf(self, x: float, params: List[float]) -> float:
        """Triangular membership function"""
        a, b, c = params
        if x <= a or x >= c:
            return 0.0
        elif a < x <= b:
            return (x - a) / (b - a)
        else:
            return (c - x) / (c - b)

    def _trapezoidal_mf(self, x: float, params: List[float]) -> float:
        """Trapezoidal membership function"""
        a, b, c, d = params
        if x <= a or x >= d:
            return 0.0
        elif a < x <= b:
            return (x - a) / (b - a)
        elif b < x <= c:
            return 1.0
        else:
            return (d - x) / (d - c)

    def _gaussian_mf(self, x: float, params: List[float]) -> float:
        """Gaussian membership function"""
        mean, sigma = params
        return np.exp(-0.5 * ((x - mean) / sigma) ** 2)

    def evaluate_membership(self, variable: str, term: str, value: float) -> float:
        """Evaluate membership degree"""
        mf_info = self.membership_functions[variable][term]
        mf_type = mf_info['type']
        params = mf_info['params']

        if mf_type == 'triangular':
            return self._triangular_mf(value, params)
        elif mf_type == 'trapezoidal':
            return self._trapezoidal_mf(value, params)
        elif mf_type == 'gaussian':
            return self._gaussian_mf(value, params)
        else:
            raise ValueError(f"Unknown membership function type: {mf_type}")

    def add_rule(self, rule: FuzzyRule):
        """Add a Sugeno fuzzy rule"""
        self.rules.append(rule)

    def infer(self, inputs: Dict[str, float]) -> float:
        """
        Sugeno fuzzy inference
        Returns crisp output value
        """
        numerator = 0.0
        denominator = 0.0

        for rule in self.rules:
            # Calculate rule firing strength (minimum of antecedents)
            firing_strength = float('inf')

            for variable, term in rule.antecedent.items():
                if variable in inputs:
                    membership = self.evaluate_membership(variable, term, inputs[variable])
                    firing_strength = min(firing_strength, membership)

            if firing_strength == float('inf'):
                firing_strength = 0.0

            # Weighted contribution
            weighted_strength = firing_strength * rule.weight
            numerator += weighted_strength * rule.consequent
            denominator += weighted_strength

        if denominator == 0:
            return 0.0

        return numerator / denominator


class NGIDSDatasetGenerator:
    """
    Next-Generation IDS Dataset Generator
    Based on: Computer Networks 2017 research paper
    """

    def __init__(self, ixia_simulation_mode: bool = True):
        """
        Initialize NGIDS dataset generator

        Args:
            ixia_simulation_mode: Simulate IXIA Perfect Storm (True) or use synthetic approach
        """
        self.ixia_simulation_mode = ixia_simulation_mode
        self.fuzzy_systems = {}
        self.quality_evaluator = None
        self._initialize_fuzzy_systems()

    def _initialize_fuzzy_systems(self):
        """Initialize fuzzy inference systems for different attack types"""

        # Network traffic characteristics fuzzy system
        traffic_fuzzy = SugenoFuzzyInferenceSystem()

        # Membership functions for packet size
        traffic_fuzzy.add_membership_function('packet_size', 'small', 'triangular', [0, 64, 200])
        traffic_fuzzy.add_membership_function('packet_size', 'medium', 'triangular', [100, 500, 1000])
        traffic_fuzzy.add_membership_function('packet_size', 'large', 'triangular', [800, 1200, 1500])

        # Membership functions for packet rate
        traffic_fuzzy.add_membership_function('packet_rate', 'low', 'triangular', [0, 10, 50])
        traffic_fuzzy.add_membership_function('packet_rate', 'normal', 'triangular', [20, 100, 200])
        traffic_fuzzy.add_membership_function('packet_rate', 'high', 'triangular', [150, 500, 1000])

        # Membership functions for connection duration
        traffic_fuzzy.add_membership_function('duration', 'short', 'triangular', [0, 1, 5])
        traffic_fuzzy.add_membership_function('duration', 'medium', 'triangular', [2, 10, 30])
        traffic_fuzzy.add_membership_function('duration', 'long', 'triangular', [20, 60, 300])

        # Sugeno rules for normal traffic
        traffic_fuzzy.add_rule(FuzzyRule(
            {'packet_size': 'medium', 'packet_rate': 'normal', 'duration': 'medium'},
            0.8,  # High normality score
            1.0
        ))

        # Sugeno rules for attack patterns
        traffic_fuzzy.add_rule(FuzzyRule(
            {'packet_size': 'small', 'packet_rate': 'high', 'duration': 'short'},
            0.1,  # Low normality (high attack probability)
            1.0
        ))

        traffic_fuzzy.add_rule(FuzzyRule(
            {'packet_size': 'large', 'packet_rate': 'low', 'duration': 'long'},
            0.3,  # Medium suspicion level
            1.0
        ))

        self.fuzzy_systems['traffic'] = traffic_fuzzy

        # Initialize quality evaluator
        self.quality_evaluator = SugenoFuzzyInferenceSystem()
        self._initialize_quality_evaluator()

    def _initialize_quality_evaluator(self):
        """Initialize fuzzy system for quality of realism evaluation"""

        # Membership functions for statistical similarity
        self.quality_evaluator.add_membership_function('stat_similarity', 'low', 'triangular', [0.0, 0.0, 0.4])
        self.quality_evaluator.add_membership_function('stat_similarity', 'medium', 'triangular', [0.2, 0.5, 0.8])
        self.quality_evaluator.add_membership_function('stat_similarity', 'high', 'triangular', [0.6, 1.0, 1.0])

        # Membership functions for pattern preservation
        self.quality_evaluator.add_membership_function('pattern_preservation', 'poor', 'triangular', [0.0, 0.0, 0.3])
        self.quality_evaluator.add_membership_function('pattern_preservation', 'good', 'triangular', [0.2, 0.6, 0.9])
        self.quality_evaluator.add_membership_function('pattern_preservation', 'excellent', 'triangular', [0.7, 1.0, 1.0])

        # Membership functions for attack representation
        self.quality_evaluator.add_membership_function('attack_representation', 'incomplete', 'triangular', [0.0, 0.0, 0.4])
        self.quality_evaluator.add_membership_function('attack_representation', 'adequate', 'triangular', [0.3, 0.6, 0.9])
        self.quality_evaluator.add_membership_function('attack_representation', 'comprehensive', 'triangular', [0.8, 1.0, 1.0])

        # Rules for quality assessment
        self.quality_evaluator.add_rule(FuzzyRule(
            {'stat_similarity': 'high', 'pattern_preservation': 'excellent', 'attack_representation': 'comprehensive'},
            0.95,  # Excellent quality
            1.0
        ))

        self.quality_evaluator.add_rule(FuzzyRule(
            {'stat_similarity': 'medium', 'pattern_preservation': 'good', 'attack_representation': 'adequate'},
            0.7,   # Good quality
            1.0
        ))

        self.quality_evaluator.add_rule(FuzzyRule(
            {'stat_similarity': 'low', 'pattern_preservation': 'poor', 'attack_representation': 'incomplete'},
            0.3,   # Poor quality
            1.0
        ))

    def simulate_ixia_perfect_storm(self,
                                  attack_types: List[str],
                                  n_samples: int = 1000) -> pd.DataFrame:
        """
        Simulate IXIA Perfect Storm penetration testing platform
        Generate realistic attack and normal traffic patterns
        """
        print("🎯 Simulating IXIA Perfect Storm Penetration Testing Platform...")

        # Attack type configurations (based on research paper)
        attack_configs = {
            'dos_syn_flood': {
                'packet_size_range': (40, 100),
                'packet_rate_range': (500, 2000),
                'duration_range': (1, 10),
                'attack_probability': 0.9
            },
            'port_scan': {
                'packet_size_range': (64, 128),
                'packet_rate_range': (100, 500),
                'duration_range': (10, 60),
                'attack_probability': 0.8
            },
            'ddos': {
                'packet_size_range': (512, 1024),
                'packet_rate_range': (1000, 5000),
                'duration_range': (30, 300),
                'attack_probability': 0.95
            },
            'normal': {
                'packet_size_range': (200, 800),
                'packet_rate_range': (10, 100),
                'duration_range': (5, 120),
                'attack_probability': 0.1
            }
        }

        synthetic_data = []

        for i in range(n_samples):
            # Select attack type
            if 'normal' not in attack_types:
                attack_types.append('normal')

            attack_type = np.random.choice(attack_types)
            config = attack_configs.get(attack_type, attack_configs['normal'])

            # Generate network features using configuration
            packet_size = np.random.uniform(*config['packet_size_range'])
            packet_rate = np.random.uniform(*config['packet_rate_range'])
            duration = np.random.uniform(*config['duration_range'])

            # Use fuzzy inference to determine attack score
            fuzzy_inputs = {
                'packet_size': packet_size,
                'packet_rate': packet_rate,
                'duration': duration
            }

            normality_score = self.fuzzy_systems['traffic'].infer(fuzzy_inputs)
            attack_score = 1.0 - normality_score

            # Generate additional features
            bytes_transferred = packet_size * packet_rate * duration

            synthetic_data.append({
                'packet_size': packet_size,
                'packet_rate': packet_rate,
                'duration': duration,
                'bytes_transferred': bytes_transferred,
                'attack_score': attack_score,
                'attack_type': attack_type,
                'is_attack': attack_score > 0.5,
                'fuzzy_normality': normality_score
            })

        df = pd.DataFrame(synthetic_data)

        print(f"✅ Generated {len(df)} samples using IXIA simulation")
        print(f"📊 Attack samples: {df['is_attack'].sum()}")
        print(f"📊 Normal samples: {(~df['is_attack']).sum()}")

        return df

    def generate_ngids_dataset(self,
                              attack_types: List[str] = ['dos_syn_flood', 'port_scan', 'ddos'],
                              n_samples: int = 1000,
                              include_quality_analysis: bool = True) -> Dict[str, Any]:
        """
        Generate NGIDS-DS dataset using fuzzy qualitative modeling
        """
        print("🔬 NGIDS-DS: Starting Fuzzy Qualitative Dataset Generation")
        print(f"🎯 Attack Types: {attack_types}")
        print(f"📊 Target Samples: {n_samples}")

        # Step 1: Generate base dataset using IXIA simulation
        if self.ixia_simulation_mode:
            dataset = self.simulate_ixia_perfect_storm(attack_types, n_samples)
        else:
            # Alternative: Pure synthetic generation
            dataset = self._generate_pure_synthetic(attack_types, n_samples)

        # Step 2: Apply fuzzy enhancement
        print("🔧 Applying fuzzy qualitative modeling...")
        enhanced_dataset = self._apply_fuzzy_enhancement(dataset)

        # Step 3: Quality evaluation
        quality_results = {}
        if include_quality_analysis:
            print("📈 Evaluating quality of realism...")
            quality_results = self.evaluate_quality_of_realism(enhanced_dataset)

        # Step 4: Generate attack scenarios
        print("⚔️ Generating multi-stage attack scenarios...")
        attack_scenarios = self._generate_attack_scenarios(enhanced_dataset)

        results = {
            'dataset': enhanced_dataset,
            'attack_scenarios': attack_scenarios,
            'quality_analysis': quality_results,
            'generation_config': {
                'attack_types': attack_types,
                'n_samples': n_samples,
                'ixia_simulation': self.ixia_simulation_mode,
                'fuzzy_systems_used': list(self.fuzzy_systems.keys())
            }
        }

        print("✅ NGIDS-DS: Dataset generation completed!")
        return results

    def _apply_fuzzy_enhancement(self, dataset: pd.DataFrame) -> pd.DataFrame:
        """Apply additional fuzzy logic enhancements to the dataset"""
        enhanced = dataset.copy()

        # Apply fuzzy smoothing to numerical features
        for column in ['packet_size', 'packet_rate', 'duration']:
            if column in enhanced.columns:
                # Use fuzzy inference to smooth outliers
                smoothed_values = []
                for value in enhanced[column]:
                    fuzzy_input = {column: value}
                    # Apply fuzzy smoothing logic here
                    smoothed_value = value  # Simplified for demo
                    smoothed_values.append(smoothed_value)
                enhanced[f'{column}_fuzzy_enhanced'] = smoothed_values

        return enhanced

    def _generate_attack_scenarios(self, dataset: pd.DataFrame) -> List[Dict[str, Any]]:
        """Generate multi-stage attack scenarios"""
        scenarios = []

        attack_data = dataset[dataset['is_attack'] == True]
        attack_types = attack_data['attack_type'].unique()

        # Generate 5 multi-stage scenarios
        for i in range(5):
            scenario = {
                'scenario_id': f'attack_scenario_{i+1}',
                'stages': [],
                'total_duration': 0,
                'complexity': np.random.choice(['simple', 'moderate', 'complex'])
            }

            # 2-4 stages per scenario
            n_stages = np.random.randint(2, 5)

            for stage in range(n_stages):
                attack_type = np.random.choice(attack_types)
                stage_data = attack_data[attack_data['attack_type'] == attack_type].sample(1).iloc[0]

                scenario['stages'].append({
                    'stage': stage + 1,
                    'attack_type': attack_type,
                    'duration': stage_data['duration'],
                    'packet_rate': stage_data['packet_rate'],
                    'attack_score': stage_data['attack_score']
                })

                scenario['total_duration'] += stage_data['duration']

            scenarios.append(scenario)

        return scenarios

    def _generate_pure_synthetic(self, attack_types: List[str], n_samples: int) -> pd.DataFrame:
        """Generate pure synthetic data without IXIA simulation"""
        # Simplified synthetic generation for when IXIA is not available
        synthetic_data = []

        for i in range(n_samples):
            # Random feature generation
            packet_size = np.random.uniform(40, 1500)
            packet_rate = np.random.uniform(1, 1000)
            duration = np.random.uniform(1, 300)

            fuzzy_inputs = {
                'packet_size': packet_size,
                'packet_rate': packet_rate,
                'duration': duration
            }

            normality_score = self.fuzzy_systems['traffic'].infer(fuzzy_inputs)
            attack_score = 1.0 - normality_score

            synthetic_data.append({
                'packet_size': packet_size,
                'packet_rate': packet_rate,
                'duration': duration,
                'bytes_transferred': packet_size * packet_rate * duration,
                'attack_score': attack_score,
                'attack_type': 'synthetic_attack' if attack_score > 0.5 else 'normal',
                'is_attack': attack_score > 0.5,
                'fuzzy_normality': normality_score
            })

        return pd.DataFrame(synthetic_data)

    def evaluate_quality_of_realism(self, dataset: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluate quality of realism using fuzzy logic quantification
        Based on research paper methodology
        """
        # Calculate statistical similarity metrics
        stat_similarity = self._calculate_statistical_similarity(dataset)

        # Calculate pattern preservation
        pattern_preservation = self._calculate_pattern_preservation(dataset)

        # Calculate attack representation completeness
        attack_representation = self._calculate_attack_representation(dataset)

        # Use fuzzy evaluator to get overall quality score
        quality_inputs = {
            'stat_similarity': stat_similarity,
            'pattern_preservation': pattern_preservation,
            'attack_representation': attack_representation
        }

        overall_quality = self.quality_evaluator.infer(quality_inputs)

        return {
            'overall_quality_score': overall_quality,
            'statistical_similarity': stat_similarity,
            'pattern_preservation': pattern_preservation,
            'attack_representation': attack_representation,
            'quality_grade': self._get_quality_grade(overall_quality),
            'recommendations': self._get_quality_recommendations(quality_inputs)
        }

    def _calculate_statistical_similarity(self, dataset: pd.DataFrame) -> float:
        """Calculate statistical similarity to expected patterns"""
        # Simplified calculation
        numerical_cols = ['packet_size', 'packet_rate', 'duration']

        similarity_scores = []
        for col in numerical_cols:
            if col in dataset.columns:
                # Compare to expected statistical properties
                mean_val = dataset[col].mean()
                std_val = dataset[col].std()

                # Normalize and calculate similarity (simplified)
                normalized_score = min(1.0, max(0.0, 1.0 - abs(std_val - mean_val) / mean_val))
                similarity_scores.append(normalized_score)

        return np.mean(similarity_scores) if similarity_scores else 0.5

    def _calculate_pattern_preservation(self, dataset: pd.DataFrame) -> float:
        """Calculate how well attack patterns are preserved"""
        if 'attack_score' in dataset.columns:
            attack_data = dataset[dataset['is_attack'] == True]
            if len(attack_data) > 0:
                # Check if attack patterns show expected characteristics
                high_attack_scores = (attack_data['attack_score'] > 0.7).mean()
                return high_attack_scores

        return 0.5

    def _calculate_attack_representation(self, dataset: pd.DataFrame) -> float:
        """Calculate attack representation completeness"""
        if 'attack_type' in dataset.columns:
            attack_types = dataset[dataset['is_attack'] == True]['attack_type'].nunique()
            total_possible_types = 5  # Expected number of attack types
            return min(1.0, attack_types / total_possible_types)

        return 0.5

    def _get_quality_grade(self, quality_score: float) -> str:
        """Convert quality score to grade"""
        if quality_score >= 0.8:
            return 'Excellent'
        elif quality_score >= 0.6:
            return 'Good'
        elif quality_score >= 0.4:
            return 'Acceptable'
        else:
            return 'Needs Improvement'

    def _get_quality_recommendations(self, quality_inputs: Dict[str, float]) -> List[str]:
        """Generate recommendations for quality improvement"""
        recommendations = []

        if quality_inputs['stat_similarity'] < 0.6:
            recommendations.append("Improve statistical similarity by adjusting fuzzy membership functions")

        if quality_inputs['pattern_preservation'] < 0.6:
            recommendations.append("Enhance attack pattern preservation through refined fuzzy rules")

        if quality_inputs['attack_representation'] < 0.6:
            recommendations.append("Increase attack type diversity in the dataset")

        if not recommendations:
            recommendations.append("Dataset quality is satisfactory - ready for IDS training")

        return recommendations


# Example usage for course project
if __name__ == "__main__":
    print("🔬 NGIDS-DS Fuzzy Synthetic Generator - Research Implementation Demo")

    # Initialize generator with IXIA simulation
    generator = NGIDSDatasetGenerator(ixia_simulation_mode=True)

    # Generate NGIDS dataset
    results = generator.generate_ngids_dataset(
        attack_types=['dos_syn_flood', 'port_scan', 'ddos'],
        n_samples=500,
        include_quality_analysis=True
    )

    dataset = results['dataset']
    quality_analysis = results['quality_analysis']
    attack_scenarios = results['attack_scenarios']

    print("\n📈 Dataset Summary:")
    print(f"✅ Total Samples: {len(dataset)}")
    print(f"⚔️ Attack Samples: {dataset['is_attack'].sum()}")
    print(f"🛡️ Normal Samples: {(~dataset['is_attack']).sum()}")
    print(f"📊 Attack Types: {dataset['attack_type'].nunique()}")

    print("\n📊 Quality Analysis Results:")
    print(f"🎯 Overall Quality Score: {quality_analysis['overall_quality_score']:.3f}")
    print(f"📈 Quality Grade: {quality_analysis['quality_grade']}")
    print(f"📊 Statistical Similarity: {quality_analysis['statistical_similarity']:.3f}")
    print(f"🔍 Pattern Preservation: {quality_analysis['pattern_preservation']:.3f}")
    print(f"⚔️ Attack Representation: {quality_analysis['attack_representation']:.3f}")

    print(f"\n🎯 Generated {len(attack_scenarios)} Multi-Stage Attack Scenarios")
    for i, scenario in enumerate(attack_scenarios[:2]):  # Show first 2
        print(f"   Scenario {i+1}: {len(scenario['stages'])} stages, {scenario['complexity']} complexity")

    print("\n🎓 Research-Based NGIDS-DS Generation Complete!")
    print("📄 Based on: Computer Networks 2017 - Fuzzy Qualitative Modeling Research")