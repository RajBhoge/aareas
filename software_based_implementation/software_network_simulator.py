"""
Software-Based Network Attack Simulator
Replaces IXIA Perfect Storm with Pure Software Implementation

This module uses Scapy and mathematical models to simulate network attacks
without requiring specialized penetration testing hardware
"""

import numpy as np
import pandas as pd
import time
import threading
import queue
from typing import Dict, List, Any, Tuple
import json
import hashlib
from datetime import datetime, timedelta

# Try to import scapy, fallback to pure simulation if not available
try:
    from scapy.all import IP, TCP, UDP, ICMP, Raw
    SCAPY_AVAILABLE = True
except ImportError:
    print("⚠️ Scapy not available - using pure mathematical simulation")
    SCAPY_AVAILABLE = False


class SoftwareNetworkAttackSimulator:
    """
    Software-based network attack simulation
    Replaces IXIA Perfect Storm hardware with Scapy-based simulation
    """

    def __init__(self, simulation_mode='mathematical'):
        """
        Initialize network attack simulator

        Args:
            simulation_mode: 'scapy' for packet-level simulation, 'mathematical' for pure math
        """
        self.simulation_mode = simulation_mode if SCAPY_AVAILABLE else 'mathematical'
        self.attack_patterns = {}
        self.simulation_results = []
        self.network_topology = self._create_virtual_network_topology()

        print(f"🌐 Software Network Attack Simulator Initialized")
        print(f"   Mode: {self.simulation_mode.title()} simulation")
        print(f"   Scapy Available: {SCAPY_AVAILABLE}")

        self._initialize_attack_patterns()

    def _create_virtual_network_topology(self) -> Dict[str, Any]:
        """Create virtual network topology for simulation"""

        topology = {
            'subnets': {
                'smart_grid_control': '192.168.10.0/24',
                'ami_network': '192.168.20.0/24',
                'corporate_network': '192.168.30.0/24',
                'dmz': '192.168.100.0/24'
            },
            'devices': {
                'scada_server': {'ip': '192.168.10.10', 'services': [502, 443, 80]},  # Modbus, HTTPS, HTTP
                'historian': {'ip': '192.168.10.20', 'services': [1433, 80, 443]},    # SQL Server, Web
                'hmi_station': {'ip': '192.168.10.30', 'services': [3389, 80, 443]},  # RDP, Web
                'meter_concentrator': {'ip': '192.168.20.10', 'services': [4059, 22]}, # DNP3, SSH
                'field_gateway': {'ip': '192.168.20.20', 'services': [502, 22, 80]},  # Modbus, SSH, HTTP
                'corporate_server': {'ip': '192.168.30.10', 'services': [80, 443, 22, 25]},
                'firewall': {'ip': '192.168.100.1', 'services': [22, 443]}
            },
            'communication_protocols': [
                'Modbus/TCP (502)', 'DNP3 (4059)', 'IEC 61850 (102)',
                'HTTP (80)', 'HTTPS (443)', 'SSH (22)', 'FTP (21)'
            ]
        }

        return topology

    def _initialize_attack_patterns(self):
        """Initialize comprehensive attack pattern library"""

        self.attack_patterns = {
            # Network Layer Attacks
            'dos_syn_flood': {
                'category': 'network',
                'description': 'SYN flood denial of service attack',
                'packet_size_range': (40, 100),
                'packet_rate_range': (1000, 10000),
                'duration_range': (10, 300),
                'target_ports': [80, 443, 502, 4059],  # Include smart grid protocols
                'severity': 'high',
                'simulation_function': self._simulate_syn_flood
            },

            'ddos_amplification': {
                'category': 'network',
                'description': 'DDoS amplification attack using multiple sources',
                'packet_size_range': (512, 1024),
                'packet_rate_range': (5000, 50000),
                'duration_range': (60, 1800),
                'amplification_factor': 100,
                'severity': 'critical',
                'simulation_function': self._simulate_ddos_amplification
            },

            'port_scan': {
                'category': 'reconnaissance',
                'description': 'Network port scanning for service discovery',
                'packet_size_range': (64, 128),
                'packet_rate_range': (10, 1000),
                'duration_range': (60, 3600),
                'scan_types': ['tcp_syn', 'tcp_connect', 'udp_scan'],
                'severity': 'medium',
                'simulation_function': self._simulate_port_scan
            },

            # Smart Grid Specific Attacks
            'modbus_attack': {
                'category': 'protocol',
                'description': 'Modbus protocol exploitation (smart grid)',
                'packet_size_range': (128, 512),
                'packet_rate_range': (50, 500),
                'duration_range': (300, 3600),
                'target_ports': [502],
                'modbus_functions': [1, 2, 3, 4, 5, 6, 15, 16],  # Read/Write functions
                'severity': 'critical',
                'simulation_function': self._simulate_modbus_attack
            },

            'dnp3_attack': {
                'category': 'protocol',
                'description': 'DNP3 protocol exploitation (SCADA)',
                'packet_size_range': (256, 1024),
                'packet_rate_range': (20, 200),
                'duration_range': (600, 7200),
                'target_ports': [4059],
                'dnp3_functions': ['read', 'write', 'control', 'freeze'],
                'severity': 'critical',
                'simulation_function': self._simulate_dnp3_attack
            },

            # Advanced Persistent Threats
            'apt_lateral_movement': {
                'category': 'apt',
                'description': 'Advanced Persistent Threat with lateral movement',
                'packet_size_range': (200, 800),
                'packet_rate_range': (5, 50),
                'duration_range': (3600, 86400),  # 1-24 hours
                'movement_stages': ['reconnaissance', 'initial_breach', 'persistence', 'lateral_movement', 'data_exfiltration'],
                'severity': 'critical',
                'simulation_function': self._simulate_apt_attack
            },

            'man_in_the_middle': {
                'category': 'interception',
                'description': 'Man-in-the-Middle attack on smart grid communications',
                'packet_size_range': (200, 1500),
                'packet_rate_range': (10, 100),
                'duration_range': (1800, 43200),  # 30 minutes to 12 hours
                'intercept_protocols': ['modbus', 'dnp3', 'http', 'https'],
                'severity': 'high',
                'simulation_function': self._simulate_mitm_attack
            },

            # Data Integrity Attacks
            'false_data_injection': {
                'category': 'integrity',
                'description': 'False data injection into smart grid measurements',
                'packet_size_range': (128, 512),
                'packet_rate_range': (1, 10),
                'duration_range': (3600, 172800),  # 1 hour to 2 days
                'data_types': ['load_measurements', 'voltage_readings', 'frequency_data'],
                'severity': 'high',
                'simulation_function': self._simulate_false_data_injection
            }
        }

    def _simulate_syn_flood(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate SYN flood attack"""

        attack_data = []
        packet_size = np.random.uniform(*config['packet_size_range'])
        packet_rate = np.random.uniform(*config['packet_rate_range'])
        duration = np.random.uniform(*config['duration_range'])
        total_packets = int(packet_rate * duration)

        target_device = np.random.choice(list(self.network_topology['devices'].keys()))
        target_ip = self.network_topology['devices'][target_device]['ip']
        target_port = np.random.choice(config['target_ports'])

        print(f"   🎯 SYN Flood: {total_packets:,} packets → {target_ip}:{target_port}")

        for i in range(total_packets):
            # Generate spoofed source IP
            source_ip = f"10.{np.random.randint(0, 256)}.{np.random.randint(0, 256)}.{np.random.randint(1, 255)}"

            packet_info = {
                'timestamp': time.time() + i / packet_rate,
                'source_ip': source_ip,
                'dest_ip': target_ip,
                'dest_port': target_port,
                'packet_size': packet_size + np.random.normal(0, 10),
                'tcp_flags': 'SYN',
                'attack_type': 'dos_syn_flood',
                'target_device': target_device,
                'severity': config['severity'],
                'sequence_number': np.random.randint(0, 2**32),
                'window_size': 8192
            }

            if self.simulation_mode == 'scapy':
                # Create actual packet structure (not sent)
                packet_info['scapy_packet'] = self._create_syn_packet(source_ip, target_ip, target_port)

            attack_data.append(packet_info)

        return attack_data

    def _simulate_ddos_amplification(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate DDoS amplification attack"""

        attack_data = []
        duration = np.random.uniform(*config['duration_range'])
        base_packet_rate = np.random.uniform(*config['packet_rate_range'])
        amplification_factor = config['amplification_factor']

        # Multiple attack sources
        num_sources = np.random.randint(50, 500)
        attack_sources = [f"172.16.{np.random.randint(0, 256)}.{np.random.randint(1, 255)}"
                         for _ in range(num_sources)]

        target_device = np.random.choice(list(self.network_topology['devices'].keys()))
        target_ip = self.network_topology['devices'][target_device]['ip']

        total_packets = int(base_packet_rate * amplification_factor * duration / num_sources)

        print(f"   💥 DDoS Amplification: {num_sources} sources, {total_packets * num_sources:,} packets")

        for source_ip in attack_sources:
            for i in range(total_packets):
                packet_info = {
                    'timestamp': time.time() + i * duration / total_packets,
                    'source_ip': source_ip,
                    'dest_ip': target_ip,
                    'dest_port': 80,  # HTTP flood
                    'packet_size': np.random.uniform(*config['packet_size_range']),
                    'attack_type': 'ddos_amplification',
                    'target_device': target_device,
                    'severity': config['severity'],
                    'amplification_factor': amplification_factor,
                    'attack_wave': len(attack_data) // 1000  # Track attack waves
                }

                attack_data.append(packet_info)

        return attack_data

    def _simulate_port_scan(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate network port scanning"""

        attack_data = []
        scan_type = np.random.choice(config['scan_types'])
        duration = np.random.uniform(*config['duration_range'])

        # Select target device
        target_device = np.random.choice(list(self.network_topology['devices'].keys()))
        target_ip = self.network_topology['devices'][target_device]['ip']
        scanner_ip = "192.168.100.50"  # Attacker IP

        # Generate port range to scan
        common_ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 502, 993, 995, 4059]
        port_range = list(range(1, 1025)) + common_ports
        ports_to_scan = np.random.choice(port_range, size=np.random.randint(100, 1000), replace=False)

        print(f"   🔍 Port Scan: {scan_type} scan of {len(ports_to_scan)} ports on {target_ip}")

        for i, port in enumerate(ports_to_scan):
            packet_info = {
                'timestamp': time.time() + i * (duration / len(ports_to_scan)),
                'source_ip': scanner_ip,
                'dest_ip': target_ip,
                'dest_port': port,
                'packet_size': np.random.uniform(*config['packet_size_range']),
                'scan_type': scan_type,
                'attack_type': 'port_scan',
                'target_device': target_device,
                'severity': config['severity'],
                'port_status': self._determine_port_status(port, target_device),
                'response_time': np.random.uniform(0.001, 0.1)  # Response time in seconds
            }

            attack_data.append(packet_info)

        return attack_data

    def _simulate_modbus_attack(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate Modbus protocol attack (Smart Grid specific)"""

        attack_data = []
        duration = np.random.uniform(*config['duration_range'])
        packet_rate = np.random.uniform(*config['packet_rate_range'])
        total_packets = int(packet_rate * duration)

        # Target SCADA server or field gateway
        modbus_targets = [device for device, info in self.network_topology['devices'].items()
                         if 502 in info['services']]
        target_device = np.random.choice(modbus_targets)
        target_ip = self.network_topology['devices'][target_device]['ip']
        attacker_ip = "192.168.100.100"

        print(f"   ⚡ Modbus Attack: {total_packets} protocol packets → {target_ip}")

        for i in range(total_packets):
            modbus_function = np.random.choice(config['modbus_functions'])
            register_address = np.random.randint(0, 10000)  # Modbus register
            register_count = np.random.randint(1, 100)

            packet_info = {
                'timestamp': time.time() + i / packet_rate,
                'source_ip': attacker_ip,
                'dest_ip': target_ip,
                'dest_port': 502,
                'packet_size': np.random.uniform(*config['packet_size_range']),
                'attack_type': 'modbus_attack',
                'target_device': target_device,
                'severity': config['severity'],
                'modbus_function': modbus_function,
                'register_address': register_address,
                'register_count': register_count,
                'unit_id': np.random.randint(1, 255),
                'transaction_id': np.random.randint(0, 65536)
            }

            attack_data.append(packet_info)

        return attack_data

    def _simulate_dnp3_attack(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate DNP3 protocol attack (SCADA specific)"""

        attack_data = []
        duration = np.random.uniform(*config['duration_range'])
        packet_rate = np.random.uniform(*config['packet_rate_range'])
        total_packets = int(packet_rate * duration)

        # Target meter concentrator or SCADA systems
        dnp3_targets = [device for device, info in self.network_topology['devices'].items()
                       if 4059 in info['services']]
        target_device = np.random.choice(dnp3_targets)
        target_ip = self.network_topology['devices'][target_device]['ip']
        attacker_ip = "192.168.20.100"

        print(f"   📡 DNP3 Attack: {total_packets} SCADA packets → {target_ip}")

        for i in range(total_packets):
            dnp3_function = np.random.choice(config['dnp3_functions'])
            object_group = np.random.randint(1, 50)  # DNP3 object group
            variation = np.random.randint(1, 10)     # Object variation

            packet_info = {
                'timestamp': time.time() + i / packet_rate,
                'source_ip': attacker_ip,
                'dest_ip': target_ip,
                'dest_port': 4059,
                'packet_size': np.random.uniform(*config['packet_size_range']),
                'attack_type': 'dnp3_attack',
                'target_device': target_device,
                'severity': config['severity'],
                'dnp3_function': dnp3_function,
                'object_group': object_group,
                'variation': variation,
                'source_address': np.random.randint(1, 65519),
                'destination_address': np.random.randint(1, 65519)
            }

            attack_data.append(packet_info)

        return attack_data

    def _simulate_apt_attack(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate Advanced Persistent Threat attack with multiple stages"""

        attack_data = []
        total_duration = np.random.uniform(*config['duration_range'])
        stages = config['movement_stages']

        stage_duration = total_duration / len(stages)
        current_time = time.time()

        print(f"   🕵️ APT Attack: {len(stages)} stages over {total_duration/3600:.1f} hours")

        for stage_idx, stage in enumerate(stages):
            stage_packets = self._generate_apt_stage(stage, stage_duration, current_time)
            attack_data.extend(stage_packets)
            current_time += stage_duration

        return attack_data

    def _generate_apt_stage(self, stage: str, duration: float, start_time: float) -> List[Dict[str, Any]]:
        """Generate APT attack stage-specific traffic"""

        stage_data = []
        packets_per_stage = np.random.randint(50, 500)

        if stage == 'reconnaissance':
            # Port scans, DNS queries, network mapping
            for i in range(packets_per_stage):
                packet_info = {
                    'timestamp': start_time + i * (duration / packets_per_stage),
                    'source_ip': '10.0.0.100',
                    'dest_ip': np.random.choice([info['ip'] for info in self.network_topology['devices'].values()]),
                    'dest_port': np.random.choice([22, 80, 443, 502]),
                    'packet_size': np.random.uniform(64, 128),
                    'attack_type': 'apt_lateral_movement',
                    'apt_stage': stage,
                    'severity': 'high',
                    'stealth_level': 0.9  # High stealth
                }
                stage_data.append(packet_info)

        elif stage == 'initial_breach':
            # Exploit attempts, malware delivery
            for i in range(packets_per_stage):
                packet_info = {
                    'timestamp': start_time + i * (duration / packets_per_stage),
                    'source_ip': '203.0.113.100',  # External IP
                    'dest_ip': self.network_topology['devices']['corporate_server']['ip'],
                    'dest_port': np.random.choice([80, 443]),
                    'packet_size': np.random.uniform(1000, 5000),
                    'attack_type': 'apt_lateral_movement',
                    'apt_stage': stage,
                    'severity': 'critical',
                    'payload_type': 'malware_dropper'
                }
                stage_data.append(packet_info)

        # Additional stages...
        elif stage == 'lateral_movement':
            # Internal network traversal
            devices = list(self.network_topology['devices'].keys())
            for i in range(packets_per_stage):
                source_device = np.random.choice(devices)
                target_device = np.random.choice(devices)

                packet_info = {
                    'timestamp': start_time + i * (duration / packets_per_stage),
                    'source_ip': self.network_topology['devices'][source_device]['ip'],
                    'dest_ip': self.network_topology['devices'][target_device]['ip'],
                    'dest_port': np.random.choice([22, 135, 445, 3389]),  # Common lateral movement ports
                    'packet_size': np.random.uniform(200, 1000),
                    'attack_type': 'apt_lateral_movement',
                    'apt_stage': stage,
                    'severity': 'high',
                    'credential_harvesting': True
                }
                stage_data.append(packet_info)

        return stage_data

    def _simulate_mitm_attack(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate Man-in-the-Middle attack"""

        attack_data = []
        duration = np.random.uniform(*config['duration_range'])
        packet_rate = np.random.uniform(*config['packet_rate_range'])
        total_packets = int(packet_rate * duration)

        # Set up MITM scenario
        victim_ip = self.network_topology['devices']['hmi_station']['ip']
        server_ip = self.network_topology['devices']['scada_server']['ip']
        attacker_ip = '192.168.10.50'  # MITM position

        print(f"   🔄 MITM Attack: {total_packets} intercepted packets")

        for i in range(total_packets):
            # Simulate intercepted and potentially modified packets
            packet_info = {
                'timestamp': time.time() + i / packet_rate,
                'original_source_ip': victim_ip,
                'original_dest_ip': server_ip,
                'mitm_ip': attacker_ip,
                'dest_port': np.random.choice([80, 443, 502]),
                'packet_size': np.random.uniform(*config['packet_size_range']),
                'attack_type': 'man_in_the_middle',
                'severity': config['severity'],
                'intercepted': True,
                'modified': np.random.choice([True, False], p=[0.3, 0.7]),
                'protocol': np.random.choice(config['intercept_protocols'])
            }

            attack_data.append(packet_info)

        return attack_data

    def _simulate_false_data_injection(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Simulate false data injection into smart grid measurements"""

        attack_data = []
        duration = np.random.uniform(*config['duration_range'])
        injection_rate = np.random.uniform(*config['packet_rate_range'])
        total_injections = int(injection_rate * duration)

        target_device = 'meter_concentrator'
        target_ip = self.network_topology['devices'][target_device]['ip']
        attacker_ip = '192.168.20.200'

        print(f"   💉 False Data Injection: {total_injections} false measurements")

        for i in range(total_injections):
            data_type = np.random.choice(config['data_types'])

            # Generate false measurement values
            if data_type == 'load_measurements':
                false_value = np.random.uniform(0.1, 100.0)  # kW
                normal_range = (1.0, 20.0)
            elif data_type == 'voltage_readings':
                false_value = np.random.uniform(180, 280)  # V
                normal_range = (220, 240)
            elif data_type == 'frequency_data':
                false_value = np.random.uniform(45, 55)  # Hz
                normal_range = (49.8, 50.2)

            packet_info = {
                'timestamp': time.time() + i * (duration / total_injections),
                'source_ip': attacker_ip,
                'dest_ip': target_ip,
                'dest_port': 502,  # Modbus
                'packet_size': np.random.uniform(*config['packet_size_range']),
                'attack_type': 'false_data_injection',
                'target_device': target_device,
                'severity': config['severity'],
                'data_type': data_type,
                'false_value': false_value,
                'normal_range': normal_range,
                'deviation_factor': abs(false_value - np.mean(normal_range)) / (normal_range[1] - normal_range[0])
            }

            attack_data.append(packet_info)

        return attack_data

    def _determine_port_status(self, port: int, target_device: str) -> str:
        """Determine if a port is open, closed, or filtered based on device type"""

        device_info = self.network_topology['devices'].get(target_device, {})
        open_ports = device_info.get('services', [])

        if port in open_ports:
            return 'open'
        elif port in [135, 139, 445]:  # Common Windows ports
            return 'filtered'
        else:
            return 'closed'

    def _create_syn_packet(self, src_ip: str, dst_ip: str, dst_port: int):
        """Create SYN packet using Scapy (if available)"""

        if not SCAPY_AVAILABLE:
            return None

        try:
            packet = IP(src=src_ip, dst=dst_ip) / TCP(dport=dst_port, flags='S')
            return packet
        except Exception:
            return None

    def generate_comprehensive_attack_dataset(self,
                                            attack_types: List[str] = None,
                                            n_samples_per_type: int = 100,
                                            include_normal_traffic: bool = True) -> pd.DataFrame:
        """Generate comprehensive attack dataset for course project"""

        if attack_types is None:
            attack_types = ['dos_syn_flood', 'port_scan', 'modbus_attack', 'false_data_injection']

        print(f"🔧 Generating comprehensive network attack dataset...")
        print(f"   Attack types: {attack_types}")
        print(f"   Samples per type: {n_samples_per_type}")

        all_attack_data = []

        for attack_type in attack_types:
            if attack_type in self.attack_patterns:
                print(f"   🎯 Simulating {attack_type}...")
                config = self.attack_patterns[attack_type]

                # Generate multiple instances of this attack type
                for instance in range(n_samples_per_type // 50):  # Batch processing
                    attack_data = config['simulation_function'](config)
                    all_attack_data.extend(attack_data)

        # Add normal traffic for comparison
        if include_normal_traffic:
            print("   📊 Generating normal network traffic...")
            normal_data = self._generate_normal_network_traffic(len(all_attack_data) // 2)
            all_attack_data.extend(normal_data)

        # Convert to DataFrame and shuffle
        df = pd.DataFrame(all_attack_data)
        df = df.sample(frac=1).reset_index(drop=True)  # Shuffle

        # Add derived features for ML
        df = self._add_network_features(df)

        print(f"✅ Generated {len(df):,} network traffic samples")
        print(f"   Attack samples: {len([x for x in all_attack_data if x.get('attack_type') != 'normal']):,}")
        print(f"   Normal samples: {len([x for x in all_attack_data if x.get('attack_type') == 'normal']):,}")

        return df

    def _generate_normal_network_traffic(self, n_samples: int) -> List[Dict[str, Any]]:
        """Generate normal network traffic patterns"""

        normal_data = []
        devices = list(self.network_topology['devices'].keys())

        for i in range(n_samples):
            source_device = np.random.choice(devices)
            dest_device = np.random.choice(devices)

            # Avoid self-communication
            while dest_device == source_device:
                dest_device = np.random.choice(devices)

            source_ip = self.network_topology['devices'][source_device]['ip']
            dest_ip = self.network_topology['devices'][dest_device]['ip']

            # Normal communication patterns
            if 'scada' in source_device or 'scada' in dest_device:
                # SCADA traffic
                dest_port = np.random.choice([502, 4059, 80, 443])
                packet_size = np.random.uniform(128, 512)
                session_duration = np.random.uniform(300, 3600)
            elif 'corporate' in source_device or 'corporate' in dest_device:
                # Corporate traffic
                dest_port = np.random.choice([80, 443, 25, 110])
                packet_size = np.random.uniform(500, 1500)
                session_duration = np.random.uniform(60, 1800)
            else:
                # General smart grid communication
                dest_port = np.random.choice([80, 443, 22, 502])
                packet_size = np.random.uniform(200, 800)
                session_duration = np.random.uniform(120, 1200)

            packet_info = {
                'timestamp': time.time() + i * np.random.uniform(0.1, 10.0),
                'source_ip': source_ip,
                'dest_ip': dest_ip,
                'dest_port': dest_port,
                'packet_size': packet_size,
                'attack_type': 'normal',
                'severity': 'none',
                'session_duration': session_duration,
                'protocol': 'TCP' if dest_port in [80, 443, 22, 502, 4059] else 'UDP',
                'bytes_transferred': packet_size * np.random.randint(1, 100)
            }

            normal_data.append(packet_info)

        return normal_data

    def _add_network_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features for machine learning"""

        # Network flow features
        df['flow_duration'] = df.get('session_duration', 0)
        df['packets_per_second'] = 1.0 / (df.get('flow_duration', 1) + 0.001)
        df['bytes_per_packet'] = df['packet_size']
        df['is_smart_grid_port'] = df['dest_port'].isin([502, 4059, 102])
        df['is_encrypted'] = df['dest_port'].isin([443, 22])

        # Attack indicators
        df['is_attack'] = df['attack_type'] != 'normal'
        df['attack_severity_numeric'] = df['severity'].map({
            'none': 0, 'low': 1, 'medium': 2, 'high': 3, 'critical': 4
        }).fillna(0)

        # Time-based features
        df['hour_of_day'] = pd.to_datetime(df['timestamp'], unit='s').dt.hour
        df['day_of_week'] = pd.to_datetime(df['timestamp'], unit='s').dt.dayofweek

        # Statistical features (for ML)
        df['packet_size_zscore'] = (df['packet_size'] - df['packet_size'].mean()) / df['packet_size'].std()

        return df

    def visualize_attack_patterns(self, df: pd.DataFrame, save_plots: bool = True):
        """Create visualizations of attack patterns"""

        print("📊 Generating network attack visualizations...")

        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        fig.suptitle('Software-Based Network Attack Simulation Results', fontsize=16)

        # Plot 1: Attack type distribution
        if 'attack_type' in df.columns:
            attack_counts = df['attack_type'].value_counts()
            axes[0, 0].bar(range(len(attack_counts)), attack_counts.values)
            axes[0, 0].set_title('Attack Type Distribution')
            axes[0, 0].set_xticks(range(len(attack_counts)))
            axes[0, 0].set_xticklabels(attack_counts.index, rotation=45, ha='right')
            axes[0, 0].set_ylabel('Number of Packets')

        # Plot 2: Packet size distribution
        axes[0, 1].hist(df['packet_size'], bins=50, alpha=0.7, edgecolor='black')
        axes[0, 1].set_title('Packet Size Distribution')
        axes[0, 1].set_xlabel('Packet Size (bytes)')
        axes[0, 1].set_ylabel('Frequency')

        # Plot 3: Port distribution
        port_counts = df['dest_port'].value_counts().head(10)
        axes[0, 2].bar(range(len(port_counts)), port_counts.values)
        axes[0, 2].set_title('Top 10 Destination Ports')
        axes[0, 2].set_xticks(range(len(port_counts)))
        axes[0, 2].set_xticklabels(port_counts.index, rotation=45)

        # Plot 4: Attack severity
        if 'severity' in df.columns:
            severity_counts = df['severity'].value_counts()
            axes[1, 0].pie(severity_counts.values, labels=severity_counts.index, autopct='%1.1f%%')
            axes[1, 0].set_title('Attack Severity Distribution')

        # Plot 5: Timeline of attacks
        if 'timestamp' in df.columns:
            df['hour'] = pd.to_datetime(df['timestamp'], unit='s').dt.hour
            hourly_attacks = df[df['is_attack'] == True]['hour'].value_counts().sort_index()
            axes[1, 1].plot(hourly_attacks.index, hourly_attacks.values, 'r-o')
            axes[1, 1].set_title('Attack Distribution by Hour')
            axes[1, 1].set_xlabel('Hour of Day')
            axes[1, 1].set_ylabel('Number of Attacks')
            axes[1, 1].grid(True)

        # Plot 6: Protocol distribution
        if 'protocol' in df.columns:
            protocol_counts = df['protocol'].value_counts()
            axes[1, 2].bar(protocol_counts.index, protocol_counts.values)
            axes[1, 2].set_title('Protocol Distribution')
            axes[1, 2].set_ylabel('Number of Packets')

        plt.tight_layout()

        if save_plots:
            plt.savefig('/home/azureuser/aareas/software_network_simulation.png',
                       dpi=300, bbox_inches='tight')
            print("📁 Visualization saved to software_network_simulation.png")

        plt.show()

# Demo execution
if __name__ == "__main__":
    print("🌐 Software-Based Network Attack Simulator Demo")
    print("=" * 70)

    # Initialize simulator
    simulator = SoftwareNetworkAttackSimulator(simulation_mode='mathematical')

    # Generate attack dataset
    attack_dataset = simulator.generate_comprehensive_attack_dataset(
        attack_types=['dos_syn_flood', 'port_scan', 'modbus_attack', 'false_data_injection'],
        n_samples_per_type=200,  # Reduced for demo
        include_normal_traffic=True
    )

    # Display results
    print(f"\n📊 Network Attack Simulation Results:")
    print(f"   Total Packets: {len(attack_dataset):,}")
    print(f"   Attack Types: {attack_dataset['attack_type'].nunique()}")
    print(f"   Time Span: {attack_dataset['timestamp'].max() - attack_dataset['timestamp'].min():.0f} seconds")

    print(f"\n🎯 Attack Type Breakdown:")
    attack_breakdown = attack_dataset['attack_type'].value_counts()
    for attack_type, count in attack_breakdown.items():
        print(f"   {attack_type}: {count:,}")

    print(f"\n⚠️ Severity Distribution:")
    severity_breakdown = attack_dataset['severity'].value_counts()
    for severity, count in severity_breakdown.items():
        print(f"   {severity}: {count:,}")

    # Save dataset
    attack_dataset.to_csv('/home/azureuser/aareas/software_network_attack_data.csv', index=False)
    print(f"\n💾 Dataset saved to software_network_attack_data.csv")

    # Create visualizations
    simulator.visualize_attack_patterns(attack_dataset)

    print("\n✅ Software-Based Network Attack Simulation Complete!")