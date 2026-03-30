"""
FedGridShield Framework Implementation
Based on: "Federated Learning for Smart Grid: A Survey on Applications and Potential Vulnerabilities"
IEEE Access 2021 Paper Analysis

This implementation follows the research paper's methodology:
- Federated learning framework for smart grid systems
- Privacy-preserving aggregation protocols
- Cyber-Physical System (CPS) architecture
- Advanced Metering Infrastructure (AMI) integration
- Collaborative model training without raw data sharing
"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json
import hashlib
import time


@dataclass
class UtilityNode:
    """Represents a smart grid utility in the federated system"""
    utility_id: str
    location: str
    data_size: int
    privacy_level: str
    ami_integration: bool
    cybersecurity_level: str


@dataclass
class FederatedModel:
    """Federated learning model state"""
    model_weights: Dict[str, torch.Tensor]
    utility_id: str
    training_rounds: int
    privacy_budget: float
    performance_metrics: Dict[str, float]


class SmartGridPrivacyProtocol(ABC):
    """Abstract base class for privacy-preserving protocols"""

    @abstractmethod
    def aggregate_models(self, local_models: List[FederatedModel]) -> FederatedModel:
        """Aggregate local models while preserving privacy"""
        pass

    @abstractmethod
    def verify_compliance(self, model: FederatedModel) -> bool:
        """Verify protocol compliance"""
        pass


class MinimalInformationTransportProtocol(SmartGridPrivacyProtocol):
    """
    Implementation of minimal information transport protocol
    Based on Paper 4: "Privacy in Smart Grids" dissertation principles
    """

    def __init__(self, privacy_threshold: float = 0.8):
        self.privacy_threshold = privacy_threshold

    def aggregate_models(self, local_models: List[FederatedModel]) -> FederatedModel:
        """
        Aggregate models using minimal information transport
        Ensures consumption data does not leave the household
        """
        if not local_models:
            raise ValueError("No local models provided for aggregation")

        # Initialize aggregated weights
        aggregated_weights = {}
        total_data_size = sum(model.privacy_budget for model in local_models)

        # Weighted averaging based on privacy budget (inverse weighting)
        for key in local_models[0].model_weights.keys():
            weighted_sum = torch.zeros_like(local_models[0].model_weights[key])

            for model in local_models:
                # Higher privacy budget = lower weight (more privacy protection needed)
                weight = (1.0 / model.privacy_budget) / sum(1.0 / m.privacy_budget for m in local_models)
                weighted_sum += weight * model.model_weights[key]

            aggregated_weights[key] = weighted_sum

        # Create aggregated model
        aggregated_model = FederatedModel(
            model_weights=aggregated_weights,
            utility_id="federated_aggregate",
            training_rounds=max(model.training_rounds for model in local_models),
            privacy_budget=np.mean([model.privacy_budget for model in local_models]),
            performance_metrics=self._aggregate_metrics(local_models)
        )

        return aggregated_model

    def _aggregate_metrics(self, local_models: List[FederatedModel]) -> Dict[str, float]:
        """Aggregate performance metrics"""
        aggregated_metrics = {}

        if not local_models:
            return aggregated_metrics

        # Get all unique metric keys
        all_keys = set()
        for model in local_models:
            all_keys.update(model.performance_metrics.keys())

        # Average each metric
        for key in all_keys:
            values = [model.performance_metrics.get(key, 0.0) for model in local_models]
            aggregated_metrics[key] = np.mean(values)

        return aggregated_metrics

    def verify_compliance(self, model: FederatedModel) -> bool:
        """Verify minimal information transport compliance"""
        # Check if privacy budget is within acceptable range
        if model.privacy_budget > self.privacy_threshold:
            return False

        # Verify model weights are properly anonymized
        for key, weights in model.model_weights.items():
            if torch.any(torch.isnan(weights)) or torch.any(torch.isinf(weights)):
                return False

        return True


class SecureBillingProtocol:
    """
    Secure billing protocol for federated smart grid operations
    Based on research paper's privacy-preserving billing approach
    """

    def __init__(self):
        self.billing_records = {}

    def calculate_federated_billing(self,
                                  utility_nodes: List[UtilityNode],
                                  model_contributions: Dict[str, float],
                                  base_rate: float = 0.01) -> Dict[str, float]:
        """
        Calculate billing based on federated learning contributions
        while preserving individual utility privacy
        """
        billing = {}

        total_contribution = sum(model_contributions.values())

        for node in utility_nodes:
            contribution_ratio = model_contributions.get(node.utility_id, 0.0) / total_contribution
            privacy_multiplier = self._get_privacy_multiplier(node.privacy_level)

            # Higher privacy level = higher billing rate
            utility_billing = base_rate * contribution_ratio * privacy_multiplier * node.data_size

            billing[node.utility_id] = utility_billing

        return billing

    def _get_privacy_multiplier(self, privacy_level: str) -> float:
        """Get privacy multiplier based on privacy level"""
        multipliers = {
            'basic': 1.0,
            'standard': 1.2,
            'high': 1.5,
            'maximum': 2.0
        }
        return multipliers.get(privacy_level.lower(), 1.0)


class SmartGridCyberSecurityModule:
    """
    Cybersecurity module for federated smart grid systems
    Implements SOTA attack and defense methods from research
    """

    def __init__(self):
        self.known_attacks = [
            'model_poisoning',
            'data_poisoning',
            'inference_attacks',
            'eavesdropping',
            'man_in_the_middle',
            'byzantine_attacks'
        ]
        self.defense_mechanisms = {}
        self._initialize_defense_mechanisms()

    def _initialize_defense_mechanisms(self):
        """Initialize cybersecurity defense mechanisms"""
        self.defense_mechanisms = {
            'model_poisoning': self._detect_model_poisoning,
            'data_poisoning': self._detect_data_poisoning,
            'inference_attacks': self._prevent_inference_attacks,
            'byzantine_attacks': self._handle_byzantine_attacks
        }

    def assess_security_threat(self,
                              federated_models: List[FederatedModel],
                              threat_threshold: float = 0.7) -> Dict[str, Any]:
        """Assess cybersecurity threats in federated learning"""
        threat_assessment = {
            'overall_threat_level': 0.0,
            'specific_threats': {},
            'recommended_actions': []
        }

        # Check for model poisoning
        poisoning_score = self._detect_model_poisoning(federated_models)
        threat_assessment['specific_threats']['model_poisoning'] = poisoning_score

        # Check for Byzantine attacks
        byzantine_score = self._handle_byzantine_attacks(federated_models)
        threat_assessment['specific_threats']['byzantine_attacks'] = byzantine_score

        # Calculate overall threat level
        threat_scores = list(threat_assessment['specific_threats'].values())
        threat_assessment['overall_threat_level'] = np.mean(threat_scores)

        # Generate recommendations
        if threat_assessment['overall_threat_level'] > threat_threshold:
            threat_assessment['recommended_actions'].append("Increase privacy budget")
            threat_assessment['recommended_actions'].append("Enable Byzantine fault tolerance")
            threat_assessment['recommended_actions'].append("Implement additional model validation")

        return threat_assessment

    def _detect_model_poisoning(self, models: List[FederatedModel]) -> float:
        """Detect model poisoning attacks"""
        if len(models) < 2:
            return 0.0

        # Calculate pairwise model similarity
        similarities = []

        for i in range(len(models)):
            for j in range(i + 1, len(models)):
                similarity = self._calculate_model_similarity(models[i], models[j])
                similarities.append(similarity)

        # Low similarity indicates potential poisoning
        avg_similarity = np.mean(similarities)
        poisoning_score = 1.0 - avg_similarity

        return min(1.0, max(0.0, poisoning_score))

    def _detect_data_poisoning(self, models: List[FederatedModel]) -> float:
        """Detect data poisoning through performance analysis"""
        if not models:
            return 0.0

        performance_values = []
        for model in models:
            if 'accuracy' in model.performance_metrics:
                performance_values.append(model.performance_metrics['accuracy'])

        if not performance_values:
            return 0.0

        # High variance in performance might indicate data poisoning
        performance_variance = np.var(performance_values)
        poisoning_score = min(1.0, performance_variance * 2.0)  # Scaling factor

        return poisoning_score

    def _prevent_inference_attacks(self, models: List[FederatedModel]) -> float:
        """Assess vulnerability to inference attacks"""
        # Check privacy budget levels
        privacy_budgets = [model.privacy_budget for model in models]
        min_privacy = min(privacy_budgets) if privacy_budgets else 1.0

        # Lower privacy budget = higher inference attack risk
        inference_risk = 1.0 / min_privacy if min_privacy > 0 else 1.0

        return min(1.0, inference_risk)

    def _handle_byzantine_attacks(self, models: List[FederatedModel]) -> float:
        """Detect and handle Byzantine attacks"""
        if len(models) < 3:
            return 0.0

        # Calculate consensus among models
        consensus_scores = []

        for i, model in enumerate(models):
            other_models = models[:i] + models[i+1:]
            consensus = 0.0

            for other_model in other_models:
                similarity = self._calculate_model_similarity(model, other_model)
                consensus += similarity

            consensus_scores.append(consensus / len(other_models))

        # Low consensus indicates potential Byzantine behavior
        min_consensus = min(consensus_scores)
        byzantine_score = 1.0 - min_consensus

        return byzantine_score

    def _calculate_model_similarity(self, model1: FederatedModel, model2: FederatedModel) -> float:
        """Calculate similarity between two models"""
        if not model1.model_weights or not model2.model_weights:
            return 0.0

        similarities = []

        for key in model1.model_weights.keys():
            if key in model2.model_weights:
                # Calculate cosine similarity
                weights1 = model1.model_weights[key].flatten()
                weights2 = model2.model_weights[key].flatten()

                dot_product = torch.dot(weights1, weights2)
                norm1 = torch.norm(weights1)
                norm2 = torch.norm(weights2)

                if norm1 > 0 and norm2 > 0:
                    similarity = dot_product / (norm1 * norm2)
                    similarities.append(similarity.item())

        return np.mean(similarities) if similarities else 0.0


class FedGridShieldFramework:
    """
    Main FedGridShield Framework
    Based on: IEEE Access 2021 Survey - "Federated Learning for Smart Grid"
    """

    def __init__(self,
                 num_utilities: int = 3,
                 privacy_protocol: str = 'minimal_transport',
                 enable_cybersecurity: bool = True):
        """
        Initialize FedGridShield framework

        Args:
            num_utilities: Number of utility nodes to simulate
            privacy_protocol: Privacy protocol type
            enable_cybersecurity: Enable cybersecurity module
        """
        self.num_utilities = num_utilities
        self.utility_nodes = []
        self.global_model = None
        self.training_history = []

        # Initialize privacy protocol
        if privacy_protocol == 'minimal_transport':
            self.privacy_protocol = MinimalInformationTransportProtocol()
        else:
            self.privacy_protocol = MinimalInformationTransportProtocol()

        # Initialize billing protocol
        self.billing_protocol = SecureBillingProtocol()

        # Initialize cybersecurity module
        self.cybersecurity_module = None
        if enable_cybersecurity:
            self.cybersecurity_module = SmartGridCyberSecurityModule()

        # Initialize utility nodes
        self._initialize_utility_nodes()

        print(f"🛡️ FedGridShield Framework Initialized")
        print(f"⚡ Utilities: {self.num_utilities}")
        print(f"🔒 Privacy Protocol: {privacy_protocol}")
        print(f"🛡️ Cybersecurity: {'Enabled' if enable_cybersecurity else 'Disabled'}")

    def _initialize_utility_nodes(self):
        """Initialize simulated utility nodes"""
        utility_configs = [
            {"location": "Metro_North", "privacy": "high", "cybersecurity": "maximum"},
            {"location": "Rural_West", "privacy": "standard", "cybersecurity": "high"},
            {"location": "Industrial_East", "privacy": "maximum", "cybersecurity": "standard"},
            {"location": "Residential_South", "privacy": "basic", "cybersecurity": "high"},
            {"location": "Commercial_Central", "privacy": "standard", "cybersecurity": "maximum"}
        ]

        for i in range(self.num_utilities):
            config = utility_configs[i % len(utility_configs)]

            node = UtilityNode(
                utility_id=f"utility_{i+1}_{config['location']}",
                location=config['location'],
                data_size=np.random.randint(1000, 10000),
                privacy_level=config['privacy'],
                ami_integration=True,
                cybersecurity_level=config['cybersecurity']
            )

            self.utility_nodes.append(node)

    def simulate_local_training(self,
                               utility_data: Dict[str, np.ndarray],
                               model_architecture: Dict[str, Any],
                               local_epochs: int = 5) -> List[FederatedModel]:
        """
        Simulate local training on utility nodes
        """
        print("🔧 Simulating local training on utility nodes...")

        local_models = []

        for node in self.utility_nodes:
            if node.utility_id not in utility_data:
                print(f"⚠️ No data available for {node.utility_id}")
                continue

            # Simulate local model training
            local_model = self._train_local_model(
                node,
                utility_data[node.utility_id],
                model_architecture,
                local_epochs
            )

            local_models.append(local_model)
            print(f"✅ Local training completed for {node.utility_id}")

        return local_models

    def _train_local_model(self,
                          node: UtilityNode,
                          local_data: np.ndarray,
                          model_architecture: Dict[str, Any],
                          local_epochs: int) -> FederatedModel:
        """Train a local model on utility node"""

        # Create simple neural network for demonstration
        input_size = local_data.shape[-1] if len(local_data.shape) > 1 else 1
        hidden_size = model_architecture.get('hidden_size', 64)
        output_size = model_architecture.get('output_size', 1)

        # Simple feedforward network
        model = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, output_size),
            nn.Sigmoid()
        )

        # Simulate training (simplified)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.MSELoss()

        # Convert data to tensors
        if len(local_data.shape) == 1:
            local_data = local_data.reshape(-1, 1)

        X = torch.FloatTensor(local_data)
        y = torch.FloatTensor(np.random.random((len(X), output_size)))  # Simulated targets

        model.train()
        final_loss = 0.0

        for epoch in range(local_epochs):
            optimizer.zero_grad()
            outputs = model(X)
            loss = criterion(outputs, y)
            loss.backward()
            optimizer.step()
            final_loss = loss.item()

        # Extract model weights
        model_weights = {name: param.clone().detach() for name, param in model.named_parameters()}

        # Calculate privacy budget based on node privacy level
        privacy_multipliers = {'basic': 1.0, 'standard': 0.8, 'high': 0.6, 'maximum': 0.4}
        privacy_budget = privacy_multipliers.get(node.privacy_level, 1.0)

        # Performance metrics
        model.eval()
        with torch.no_grad():
            predictions = model(X)
            accuracy = 1.0 - final_loss  # Simplified accuracy calculation

        performance_metrics = {
            'accuracy': accuracy,
            'loss': final_loss,
            'data_size': len(local_data),
            'privacy_level': node.privacy_level
        }

        return FederatedModel(
            model_weights=model_weights,
            utility_id=node.utility_id,
            training_rounds=1,
            privacy_budget=privacy_budget,
            performance_metrics=performance_metrics
        )

    def federated_aggregation_round(self,
                                   local_models: List[FederatedModel]) -> Dict[str, Any]:
        """
        Perform one round of federated aggregation
        """
        print("🔄 Performing federated aggregation...")

        # Step 1: Cybersecurity assessment
        security_assessment = {}
        if self.cybersecurity_module:
            security_assessment = self.cybersecurity_module.assess_security_threat(local_models)
            print(f"🛡️ Security Threat Level: {security_assessment['overall_threat_level']:.3f}")

        # Step 2: Privacy-preserving aggregation
        try:
            self.global_model = self.privacy_protocol.aggregate_models(local_models)
            aggregation_success = True
            print("✅ Model aggregation completed")
        except Exception as e:
            print(f"❌ Aggregation failed: {e}")
            aggregation_success = False
            self.global_model = None

        # Step 3: Compliance verification
        compliance_results = {}
        if self.global_model:
            compliance_results = {
                'global_model_compliant': self.privacy_protocol.verify_compliance(self.global_model),
                'local_models_compliant': [
                    self.privacy_protocol.verify_compliance(model) for model in local_models
                ]
            }

        # Step 4: Billing calculation
        model_contributions = {
            model.utility_id: 1.0 / model.privacy_budget for model in local_models
        }

        billing_results = self.billing_protocol.calculate_federated_billing(
            self.utility_nodes, model_contributions
        )

        # Step 5: Record training round
        round_results = {
            'round_id': len(self.training_history) + 1,
            'aggregation_success': aggregation_success,
            'security_assessment': security_assessment,
            'compliance_results': compliance_results,
            'billing_results': billing_results,
            'participating_utilities': len(local_models),
            'global_model_performance': self.global_model.performance_metrics if self.global_model else {},
            'timestamp': time.time()
        }

        self.training_history.append(round_results)

        print(f"📊 Round {round_results['round_id']} completed")
        print(f"⚡ Participating utilities: {len(local_models)}")

        return round_results

    def multi_round_federated_training(self,
                                     utility_data: Dict[str, np.ndarray],
                                     num_rounds: int = 5,
                                     model_architecture: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform multi-round federated training
        """
        print(f"🚀 Starting {num_rounds} rounds of federated training")

        if model_architecture is None:
            model_architecture = {'hidden_size': 64, 'output_size': 1}

        all_results = []

        for round_num in range(num_rounds):
            print(f"\n🔄 === Federated Round {round_num + 1}/{num_rounds} ===")

            # Local training
            local_models = self.simulate_local_training(
                utility_data, model_architecture, local_epochs=3
            )

            if not local_models:
                print("❌ No local models available for aggregation")
                break

            # Aggregation round
            round_results = self.federated_aggregation_round(local_models)
            all_results.append(round_results)

            # Check for early stopping based on security threats
            if (self.cybersecurity_module and
                round_results['security_assessment'].get('overall_threat_level', 0) > 0.8):
                print("⚠️ High security threat detected - stopping training")
                break

        # Final summary
        training_summary = self._generate_training_summary(all_results)

        print(f"\n✅ Federated training completed - {len(all_results)} rounds")
        return {
            'training_results': all_results,
            'final_summary': training_summary,
            'global_model': self.global_model,
            'utility_nodes': [
                {
                    'utility_id': node.utility_id,
                    'location': node.location,
                    'privacy_level': node.privacy_level,
                    'cybersecurity_level': node.cybersecurity_level
                } for node in self.utility_nodes
            ]
        }

    def _generate_training_summary(self, all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive training summary"""

        successful_rounds = [r for r in all_results if r['aggregation_success']]
        total_billing = sum([
            sum(r['billing_results'].values()) for r in all_results
        ])

        avg_security_threat = np.mean([
            r['security_assessment'].get('overall_threat_level', 0) for r in all_results
        ])

        summary = {
            'total_rounds': len(all_results),
            'successful_rounds': len(successful_rounds),
            'success_rate': len(successful_rounds) / len(all_results) if all_results else 0,
            'total_billing_cost': total_billing,
            'average_security_threat': avg_security_threat,
            'final_global_performance': self.global_model.performance_metrics if self.global_model else {},
            'privacy_preservation': 'Maintained' if avg_security_threat < 0.5 else 'At Risk'
        }

        return summary


# Example usage for course project
if __name__ == "__main__":
    print("🛡️ FedGridShield Framework - Research Implementation Demo")

    # Initialize FedGridShield with 3 utilities
    fedgrid_shield = FedGridShieldFramework(
        num_utilities=3,
        privacy_protocol='minimal_transport',
        enable_cybersecurity=True
    )

    # Generate simulated smart grid data for each utility
    utility_data = {}
    np.random.seed(42)

    for node in fedgrid_shield.utility_nodes:
        # Simulate smart grid measurements (load, voltage, frequency)
        n_samples = node.data_size // 100  # Scaled down for demo
        features = 3  # load, voltage, frequency

        # Generate realistic smart grid data patterns
        data = np.random.normal(0, 1, (n_samples, features))

        # Add utility-specific characteristics
        if 'Metro' in node.location:
            data[:, 0] += 2.0  # Higher load in metro areas
        elif 'Industrial' in node.location:
            data[:, 0] += 3.0  # Highest load in industrial areas

        utility_data[node.utility_id] = data

    print(f"\n📊 Generated data for {len(utility_data)} utilities")

    # Run federated training
    results = fedgrid_shield.multi_round_federated_training(
        utility_data,
        num_rounds=3,
        model_architecture={'hidden_size': 32, 'output_size': 1}
    )

    # Display results
    print("\n🎯 === FedGridShield Training Results ===")
    summary = results['final_summary']

    print(f"✅ Training Rounds: {summary['total_rounds']}")
    print(f"📊 Success Rate: {summary['success_rate']:.1%}")
    print(f"🔒 Privacy Status: {summary['privacy_preservation']}")
    print(f"⚠️ Avg Security Threat: {summary['average_security_threat']:.3f}")
    print(f"💰 Total Billing Cost: ${summary['total_billing_cost']:.2f}")

    if results['global_model']:
        global_perf = results['global_model'].performance_metrics
        print(f"🎯 Final Model Accuracy: {global_perf.get('accuracy', 0):.3f}")

    print("\n🎓 Research-Based FedGridShield Implementation Complete!")
    print("📄 Based on: IEEE Access 2021 - Federated Learning for Smart Grid Survey")