"""
MQTT Network Simulator for Cyber-Physical Co-Simulation
Simulates MQTT communication between smart inverters and grid operators
Includes network delays, packet loss, and attack injection capabilities

Based on research proposal: "Cyber-Physical Co-Simulation for Smart Grid Security"
Replaces ns-3 network simulator with Python-based implementation
"""

import asyncio
import json
import time
import random
import threading
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
from queue import Queue, Empty
import logging


@dataclass
class MQTTMessage:
    """MQTT message structure for smart inverter communication"""
    topic: str
    payload: Dict[str, Any]
    timestamp: float
    sender_id: str
    message_type: str  # 'control', 'telemetry', 'status'
    qos: int = 1


@dataclass
class NetworkDelay:
    """Network delay characteristics"""
    min_delay_ms: float
    max_delay_ms: float
    avg_delay_ms: float
    jitter_ms: float


@dataclass
class PacketLoss:
    """Packet loss characteristics"""
    loss_rate: float  # 0.0 - 1.0
    burst_loss: bool  # True for bursty losses
    burst_length: int  # Average burst length


class SmartInverterMQTTClient:
    """Smart inverter MQTT client simulation"""

    def __init__(self, inverter_id: str, bus_id: int, rated_power_kw: float):
        self.inverter_id = inverter_id
        self.bus_id = bus_id
        self.rated_power_kw = rated_power_kw

        # Inverter status
        self.is_connected = True
        self.is_compromised = False  # For FDI attack simulation
        self.current_power_kw = rated_power_kw * 0.8  # 80% generation
        self.voltage_setpoint = 1.0  # Per unit voltage setpoint

        # Communication
        self.last_heartbeat = time.time()
        self.message_queue = Queue()

        # Attack simulation
        self.fdi_attack_active = False
        self.false_data_injection = {}

    def generate_telemetry(self) -> Dict[str, Any]:
        """Generate inverter telemetry data"""

        # Normal telemetry
        telemetry = {
            'inverter_id': self.inverter_id,
            'bus_id': self.bus_id,
            'timestamp': time.time(),
            'active_power_kw': self.current_power_kw,
            'reactive_power_kvar': self.current_power_kw * 0.1,  # Power factor ~0.99
            'voltage_pu': 1.0 + random.gauss(0, 0.01),  # Small voltage variations
            'frequency_hz': 50.0 + random.gauss(0, 0.05),  # European 50Hz
            'temperature_c': 35 + random.gauss(0, 5),
            'status': 'online',
            'power_factor': 0.99
        }

        # Apply FDI attack if active
        if self.fdi_attack_active:
            for param, false_value in self.false_data_injection.items():
                if param in telemetry:
                    telemetry[param] = false_value

        return telemetry

    def process_control_command(self, command: Dict[str, Any]) -> bool:
        """Process control command from grid operator"""

        try:
            if 'active_power_setpoint' in command:
                new_setpoint = command['active_power_setpoint']
                if 0 <= new_setpoint <= self.rated_power_kw:
                    self.current_power_kw = new_setpoint

            if 'voltage_setpoint' in command:
                self.voltage_setpoint = command['voltage_setpoint']

            return True

        except Exception as e:
            logging.error(f"Error processing command for {self.inverter_id}: {e}")
            return False

    def inject_false_data(self, parameters: Dict[str, Any], duration_seconds: float = 10):
        """Inject false data for FDI attack simulation"""

        self.fdi_attack_active = True
        self.false_data_injection = parameters.copy()

        # Schedule attack end
        def end_attack():
            time.sleep(duration_seconds)
            self.fdi_attack_active = False
            self.false_data_injection.clear()

        attack_thread = threading.Thread(target=end_attack)
        attack_thread.daemon = True
        attack_thread.start()


class MQTTNetworkSimulator:
    """MQTT Network Simulator for smart grid communication"""

    def __init__(self, network_config: Dict[str, Any] = None):
        """
        Initialize MQTT network simulator

        Args:
            network_config: Network configuration parameters
        """
        self.config = network_config or self._get_default_config()
        self.inverters: Dict[str, SmartInverterMQTTClient] = {}
        self.message_history: List[MQTTMessage] = []

        # Network characteristics
        self.network_delay = NetworkDelay(
            min_delay_ms=self.config['network']['min_delay_ms'],
            max_delay_ms=self.config['network']['max_delay_ms'],
            avg_delay_ms=self.config['network']['avg_delay_ms'],
            jitter_ms=self.config['network']['jitter_ms']
        )

        self.packet_loss = PacketLoss(
            loss_rate=self.config['network']['packet_loss_rate'],
            burst_loss=self.config['network']['burst_loss'],
            burst_length=self.config['network']['burst_length']
        )

        # Message queues for co-simulation
        self.power_system_queue = Queue()  # Messages to power system
        self.network_system_queue = Queue()  # Messages from power system

        # Simulation control
        self.simulation_running = False
        self.simulation_time = 0.0
        self.time_step = self.config['simulation']['time_step_ms'] / 1000.0

        # Statistics
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'messages_lost': 0,
            'avg_delay_ms': 0,
            'max_delay_ms': 0
        }

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default network configuration"""
        return {
            'mqtt': {
                'broker_host': 'localhost',
                'broker_port': 1883,
                'keepalive': 60,
                'qos': 1
            },
            'network': {
                'min_delay_ms': 5,      # Minimum network delay
                'max_delay_ms': 50,     # Maximum network delay
                'avg_delay_ms': 15,     # Average network delay
                'jitter_ms': 5,         # Delay jitter
                'packet_loss_rate': 0.01,  # 1% packet loss
                'burst_loss': False,    # No bursty losses
                'burst_length': 3       # Average burst length
            },
            'simulation': {
                'time_step_ms': 100,    # 100ms simulation step
                'telemetry_interval_s': 1,  # 1 second telemetry interval
                'heartbeat_interval_s': 5   # 5 second heartbeat
            },
            'topics': {
                'telemetry': 'smartgrid/inverter/{}/telemetry',
                'control': 'smartgrid/inverter/{}/control',
                'status': 'smartgrid/inverter/{}/status',
                'heartbeat': 'smartgrid/inverter/{}/heartbeat'
            }
        }

    def register_inverter(self, inverter_id: str, bus_id: int, rated_power_kw: float):
        """Register a smart inverter for communication simulation"""

        inverter = SmartInverterMQTTClient(inverter_id, bus_id, rated_power_kw)
        self.inverters[inverter_id] = inverter

        print(f"📡 Registered inverter: {inverter_id} (Bus {bus_id}, {rated_power_kw}kW)")

    def simulate_network_delay(self) -> float:
        """Simulate realistic network delay"""

        # Base delay with jitter
        base_delay = random.uniform(self.network_delay.min_delay_ms,
                                   self.network_delay.max_delay_ms)
        jitter = random.gauss(0, self.network_delay.jitter_ms)

        total_delay_ms = max(0, base_delay + jitter)

        return total_delay_ms / 1000.0  # Convert to seconds

    def simulate_packet_loss(self) -> bool:
        """Simulate packet loss"""

        if random.random() < self.packet_loss.loss_rate:
            if self.packet_loss.burst_loss:
                # Simulate burst loss
                burst_count = random.poisson(self.packet_loss.burst_length)
                return burst_count > 0
            else:
                return True

        return False

    async def send_message(self, message: MQTTMessage) -> bool:
        """Send MQTT message with network simulation"""

        # Simulate packet loss
        if self.simulate_packet_loss():
            self.stats['messages_lost'] += 1
            print(f"📉 Message lost: {message.topic} from {message.sender_id}")
            return False

        # Simulate network delay
        delay_seconds = self.simulate_network_delay()

        # Update statistics
        self.stats['messages_sent'] += 1
        self.stats['avg_delay_ms'] = (self.stats['avg_delay_ms'] + delay_seconds * 1000) / 2
        self.stats['max_delay_ms'] = max(self.stats['max_delay_ms'], delay_seconds * 1000)

        # Simulate message transmission with delay
        await asyncio.sleep(delay_seconds)

        # Add to message history
        self.message_history.append(message)

        # Route message based on topic
        if '/control' in message.topic:
            self._handle_control_message(message)
        elif '/telemetry' in message.topic:
            self._handle_telemetry_message(message)

        self.stats['messages_received'] += 1
        return True

    def _handle_control_message(self, message: MQTTMessage):
        """Handle control message to inverter"""

        # Extract inverter ID from topic
        topic_parts = message.topic.split('/')
        if len(topic_parts) >= 3:
            inverter_id = topic_parts[2]

            if inverter_id in self.inverters:
                inverter = self.inverters[inverter_id]
                success = inverter.process_control_command(message.payload)

                if success:
                    print(f"✅ Control command sent to {inverter_id}")
                else:
                    print(f"❌ Control command failed for {inverter_id}")

    def _handle_telemetry_message(self, message: MQTTMessage):
        """Handle telemetry message from inverter"""

        # Forward telemetry to power system for co-simulation
        self.power_system_queue.put(message)

    async def run_telemetry_simulation(self):
        """Run continuous telemetry simulation"""

        print("🔄 Starting MQTT telemetry simulation")

        while self.simulation_running:
            for inverter_id, inverter in self.inverters.items():
                if inverter.is_connected:
                    # Generate telemetry
                    telemetry_data = inverter.generate_telemetry()

                    # Create MQTT message
                    topic = self.config['topics']['telemetry'].format(inverter_id)
                    message = MQTTMessage(
                        topic=topic,
                        payload=telemetry_data,
                        timestamp=time.time(),
                        sender_id=inverter_id,
                        message_type='telemetry'
                    )

                    # Send message
                    await self.send_message(message)

            # Wait for next telemetry interval
            await asyncio.sleep(self.config['simulation']['telemetry_interval_s'])

    def start_simulation(self):
        """Start the network simulation"""

        if self.simulation_running:
            print("⚠️ Simulation already running")
            return

        self.simulation_running = True
        print("🚀 Starting MQTT Network Simulation")

        # Start telemetry simulation in background
        asyncio.create_task(self.run_telemetry_simulation())

    def stop_simulation(self):
        """Stop the network simulation"""

        self.simulation_running = False
        print("🛑 MQTT Network Simulation stopped")

    def launch_fdi_attack(self, target_inverter: str, attack_params: Dict[str, Any],
                         duration_seconds: float = 30) -> bool:
        """Launch False Data Injection attack on target inverter"""

        if target_inverter not in self.inverters:
            print(f"❌ Target inverter {target_inverter} not found")
            return False

        print(f"🚨 Launching FDI Attack on {target_inverter}")
        print(f"   Attack parameters: {attack_params}")
        print(f"   Duration: {duration_seconds} seconds")

        # Inject false data
        self.inverters[target_inverter].inject_false_data(attack_params, duration_seconds)

        return True

    def get_network_statistics(self) -> Dict[str, Any]:
        """Get network simulation statistics"""

        stats = self.stats.copy()
        stats['total_inverters'] = len(self.inverters)
        stats['connected_inverters'] = sum(1 for inv in self.inverters.values() if inv.is_connected)
        stats['compromised_inverters'] = sum(1 for inv in self.inverters.values() if inv.is_compromised)
        stats['message_history_length'] = len(self.message_history)

        return stats

    def export_communication_data(self) -> pd.DataFrame:
        """Export communication data for analysis"""

        data = []
        for message in self.message_history:
            record = {
                'timestamp': message.timestamp,
                'topic': message.topic,
                'sender_id': message.sender_id,
                'message_type': message.message_type,
                'payload_size': len(json.dumps(message.payload))
            }
            data.append(record)

        return pd.DataFrame(data)


class CyberPhysicalCoSimulator:
    """Cyber-Physical Co-Simulation Integration"""

    def __init__(self, power_system_data: Dict[str, Any]):
        """
        Initialize cyber-physical co-simulation

        Args:
            power_system_data: Data from power system simulation
        """
        self.power_data = power_system_data
        self.mqtt_simulator = MQTTNetworkSimulator()

        # Co-simulation state
        self.simulation_step = 0
        self.sync_time_step = 0.1  # 100ms synchronization

        # Setup inverters from power system data
        self._setup_inverters_from_power_data()

    def _setup_inverters_from_power_data(self):
        """Setup MQTT inverters based on power system solar systems"""

        if 'solar_systems' not in self.power_data:
            print("⚠️ No solar systems found in power data")
            return

        for solar in self.power_data['solar_systems']:
            self.mqtt_simulator.register_inverter(
                inverter_id=solar['inverter_id'],
                bus_id=solar['bus'],
                rated_power_kw=solar['size_kw']
            )

    def start_cosimulation(self):
        """Start cyber-physical co-simulation"""

        print("🔗 Starting Cyber-Physical Co-Simulation")
        print("   Power System ⟷ Network Simulation")

        self.mqtt_simulator.start_simulation()

        print("✅ Co-simulation started successfully")

    def stop_cosimulation(self):
        """Stop cyber-physical co-simulation"""

        print("🔗 Stopping Cyber-Physical Co-Simulation")
        self.mqtt_simulator.stop_simulation()

    def test_fdi_attack_scenario(self, scenario_name: str = "voltage_manipulation"):
        """Test False Data Injection attack scenario"""

        print(f"🧪 Testing FDI Attack Scenario: {scenario_name}")

        if not self.mqtt_simulator.inverters:
            print("❌ No inverters available for attack testing")
            return None

        # Select first inverter as target
        target_inverter = list(self.mqtt_simulator.inverters.keys())[0]

        # Define attack scenarios
        attack_scenarios = {
            'voltage_manipulation': {
                'voltage_pu': 1.15,  # Inject high voltage reading (15% over nominal)
                'active_power_kw': 0,  # Fake zero power output
            },
            'power_manipulation': {
                'active_power_kw': 100,  # Fake high power output
                'reactive_power_kvar': 50,  # Fake high reactive power
            },
            'frequency_attack': {
                'frequency_hz': 52.5,  # Dangerous frequency reading
                'voltage_pu': 0.85,   # Low voltage reading
            }
        }

        if scenario_name in attack_scenarios:
            attack_params = attack_scenarios[scenario_name]
            success = self.mqtt_simulator.launch_fdi_attack(
                target_inverter=target_inverter,
                attack_params=attack_params,
                duration_seconds=30
            )

            if success:
                print(f"✅ FDI attack scenario '{scenario_name}' launched successfully")
                return {
                    'attack_type': scenario_name,
                    'target_inverter': target_inverter,
                    'attack_params': attack_params,
                    'start_time': time.time()
                }

        print(f"❌ Failed to launch FDI attack scenario")
        return None


def main():
    """Test the MQTT Network Simulator"""

    print("🌐 Testing MQTT Network Simulator for Cyber-Physical Co-Simulation")
    print("=" * 70)

    # Create network simulator
    mqtt_sim = MQTTNetworkSimulator()

    # Register some test inverters
    test_inverters = [
        ('INV_5_30', 5, 30),
        ('INV_10_20', 10, 20),
        ('INV_7_25', 7, 25),
    ]

    for inv_id, bus, power in test_inverters:
        mqtt_sim.register_inverter(inv_id, bus, power)

    print(f"\n📊 Network Configuration:")
    config = mqtt_sim.config
    print(f"   • Network Delay: {config['network']['min_delay_ms']}-{config['network']['max_delay_ms']}ms")
    print(f"   • Packet Loss Rate: {config['network']['packet_loss_rate']:.1%}")
    print(f"   • Telemetry Interval: {config['simulation']['telemetry_interval_s']}s")

    # Test FDI attack
    print(f"\n🚨 Testing False Data Injection Attack:")
    attack_result = mqtt_sim.launch_fdi_attack(
        target_inverter='INV_5_30',
        attack_params={'voltage_pu': 1.15, 'active_power_kw': 0},
        duration_seconds=10
    )

    # Get statistics
    stats = mqtt_sim.get_network_statistics()
    print(f"\n📈 Network Statistics:")
    for key, value in stats.items():
        print(f"   • {key.replace('_', ' ').title()}: {value}")

    # Test co-simulation integration
    print(f"\n🔗 Testing Cyber-Physical Co-Simulation:")

    # Mock power system data
    mock_power_data = {
        'solar_systems': [
            {'inverter_id': 'INV_5_30', 'bus': 5, 'size_kw': 30},
            {'inverter_id': 'INV_10_20', 'bus': 10, 'size_kw': 20}
        ]
    }

    cosim = CyberPhysicalCoSimulator(mock_power_data)

    # Test attack scenario
    attack_result = cosim.test_fdi_attack_scenario('voltage_manipulation')
    if attack_result:
        print(f"✅ FDI attack test completed")

    print(f"\n🏆 MQTT Network Simulator Setup Complete!")
    print("    Ready for cyber-physical co-simulation with power system")

    return mqtt_sim, cosim


if __name__ == "__main__":
    mqtt_sim, cosim = main()