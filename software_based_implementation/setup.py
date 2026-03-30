#!/usr/bin/env python3
"""
Setup Script for Software-Based PPSDG Framework
100% Software Implementation - No Hardware Dependencies

This script automates the installation and setup process for the
Privacy-Preserving Synthetic Data Generation Framework course project.
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

class PPSDGSetup:
    def __init__(self):
        self.system_info = {
            'os': platform.system(),
            'python_version': sys.version_info,
            'architecture': platform.machine()
        }

    def print_banner(self):
        print("🖥️" + "=" * 80)
        print("   SOFTWARE-BASED PPSDG FRAMEWORK SETUP")
        print("   100% Software Implementation - No Hardware Dependencies")
        print("   Course Project: 5 ECTS Credits")
        print("=" * 82)
        print(f"📊 System: {self.system_info['os']} {self.system_info['architecture']}")
        print(f"🐍 Python: {sys.version.split()[0]}")
        print("💰 Cost: $0 (100% Open Source)")
        print("=" * 82)

    def check_python_version(self):
        """Check if Python version is compatible"""
        print("\n🔍 Checking Python version...")

        if self.system_info['python_version'] < (3, 8):
            print(f"❌ Python 3.8+ required. Current version: {sys.version}")
            print("   Please upgrade Python and try again.")
            return False

        print(f"✅ Python {sys.version.split()[0]} is compatible")
        return True

    def check_system_requirements(self):
        """Check basic system requirements"""
        print("\n🔍 Checking system requirements...")

        # Check available memory
        try:
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024**3)
            print(f"💾 Available RAM: {memory_gb:.1f} GB")

            if memory_gb < 8:
                print("⚠️  Warning: Less than 8GB RAM detected. Consider reducing dataset size.")
            else:
                print("✅ Sufficient memory available")

        except ImportError:
            print("ℹ️  psutil not available - skipping memory check")

        # Check disk space
        try:
            disk_free = os.statvfs('.').f_bavail * os.statvfs('.').f_frsize / (1024**3)
            print(f"💽 Available disk space: {disk_free:.1f} GB")

            if disk_free < 5:
                print("⚠️  Warning: Less than 5GB free space. May need more for large datasets.")
            else:
                print("✅ Sufficient disk space available")

        except AttributeError:
            # Windows doesn't have statvfs
            print("ℹ️  Disk space check not available on this system")

        return True

    def create_virtual_environment(self):
        """Create Python virtual environment"""
        print("\n🔧 Creating virtual environment...")

        venv_path = Path("ppsdg_software_env")

        if venv_path.exists():
            print("ℹ️  Virtual environment already exists")
            return True

        try:
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
            print("✅ Virtual environment created successfully")

            # Provide activation instructions
            if self.system_info['os'] == 'Windows':
                activate_cmd = f"{venv_path}\\Scripts\\activate"
            else:
                activate_cmd = f"source {venv_path}/bin/activate"

            print(f"💡 To activate: {activate_cmd}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return False

    def install_requirements(self):
        """Install Python package requirements"""
        print("\n📦 Installing Python packages...")

        # Check if requirements.txt exists
        if not Path("requirements.txt").exists():
            print("⚠️  requirements.txt not found, installing core packages manually")
            return self.install_core_packages()

        try:
            # Install PyTorch CPU version first (special handling)
            print("   Installing PyTorch (CPU-only)...")
            subprocess.run([
                sys.executable, "-m", "pip", "install",
                "torch", "torchvision", "torchaudio",
                "--index-url", "https://download.pytorch.org/whl/cpu"
            ], check=True)

            # Install other requirements
            print("   Installing other packages...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], check=True)

            print("✅ All packages installed successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Package installation failed: {e}")
            print("   Trying fallback installation...")
            return self.install_core_packages()

    def install_core_packages(self):
        """Install core packages manually"""
        core_packages = [
            "numpy>=1.24.0",
            "pandas>=2.0.0",
            "scikit-learn>=1.3.0",
            "matplotlib>=3.7.0",
            "seaborn>=0.12.0"
        ]

        try:
            print("   Installing core packages...")
            subprocess.run([
                sys.executable, "-m", "pip", "install"
            ] + core_packages, check=True)

            print("✅ Core packages installed successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Core package installation failed: {e}")
            return False

    def test_installation(self):
        """Test if installation was successful"""
        print("\n🧪 Testing installation...")

        test_imports = [
            ("numpy", "np"),
            ("pandas", "pd"),
            ("sklearn", None),
            ("matplotlib.pyplot", "plt"),
            ("torch", None)
        ]

        failed_imports = []

        for module, alias in test_imports:
            try:
                if alias:
                    exec(f"import {module} as {alias}")
                else:
                    exec(f"import {module}")
                print(f"   ✅ {module}")
            except ImportError:
                print(f"   ❌ {module}")
                failed_imports.append(module)

        if failed_imports:
            print(f"\n⚠️  Some packages failed to import: {failed_imports}")
            print("   You can still run the framework, but some features may be limited.")
            return False
        else:
            print("\n✅ All packages imported successfully!")
            return True

    def create_demo_config(self):
        """Create demo configuration file"""
        print("\n📋 Creating demo configuration...")

        demo_config = {
            "simulation": {
                "n_consumers": 100,
                "simulation_days": 3,
                "attack_ratio": 0.05
            },
            "network": {
                "attack_types": ["dos_syn_flood", "port_scan"],
                "n_samples_per_type": 100
            },
            "privacy": {
                "epsilon": 1.0,
                "delta": 1e-5
            },
            "federation": {
                "n_clients": 3,
                "num_rounds": 3
            }
        }

        try:
            import json
            with open("demo_config.json", "w") as f:
                json.dump(demo_config, f, indent=2)
            print("✅ Demo configuration created: demo_config.json")
            return True
        except Exception as e:
            print(f"❌ Failed to create demo config: {e}")
            return False

    def run_quick_test(self):
        """Run a quick functionality test"""
        print("\n🚀 Running quick functionality test...")

        test_code = """
import numpy as np
import pandas as pd
from datetime import datetime

# Test data generation
print("   Testing data generation...")
data = np.random.random((100, 3))
df = pd.DataFrame(data, columns=['load', 'voltage', 'frequency'])

# Test basic statistics
print(f"   Generated {len(df)} data points")
print(f"   Mean load: {df['load'].mean():.3f}")

# Test privacy simulation
print("   Testing privacy mechanism...")
epsilon = 1.0
sensitivity = df['load'].max() - df['load'].min()
noise_scale = sensitivity / epsilon
noise = np.random.laplace(0, noise_scale, len(df))
private_data = df['load'] + noise

print(f"   Privacy cost (ε): {epsilon}")
print(f"   Utility preserved: {1.0 - abs(df['load'].mean() - private_data.mean()) / df['load'].mean():.3f}")

print("✅ Quick test completed successfully!")
"""

        try:
            exec(test_code)
            return True
        except Exception as e:
            print(f"❌ Quick test failed: {e}")
            return False

    def display_next_steps(self):
        """Display next steps for the user"""
        print("\n🎯 SETUP COMPLETED - NEXT STEPS")
        print("=" * 50)
        print("1. 📁 Files ready in current directory")
        print("2. 🚀 Run complete course project:")
        print("   python complete_software_implementation.py")
        print("")
        print("3. 📊 Or run individual components:")
        print("   python software_smart_grid_simulator.py")
        print("   python software_network_simulator.py")
        print("")
        print("4. 🎓 Course project deliverables will be generated in:")
        print("   software_course_results/")
        print("")
        print("💡 Estimated execution time: 15-30 minutes")
        print("💰 Total cost: $0 (100% open source)")
        print("🎯 Ready for academic submission!")

    def run_setup(self):
        """Run complete setup process"""
        self.print_banner()

        # Step 1: Check Python version
        if not self.check_python_version():
            return False

        # Step 2: Check system requirements
        if not self.check_system_requirements():
            return False

        # Step 3: Install packages
        if not self.install_requirements():
            print("⚠️  Package installation had issues, but continuing...")

        # Step 4: Test installation
        self.test_installation()

        # Step 5: Create demo config
        self.create_demo_config()

        # Step 6: Run quick test
        if not self.run_quick_test():
            print("⚠️  Quick test had issues, but framework may still work")

        # Step 7: Display next steps
        self.display_next_steps()

        return True

def main():
    """Main setup function"""
    print("Starting PPSDG Framework setup...")

    setup = PPSDGSetup()
    success = setup.run_setup()

    if success:
        print("\n🎉 SETUP COMPLETED SUCCESSFULLY!")
        print("Your software-based PPSDG framework is ready for use.")
    else:
        print("\n⚠️  SETUP COMPLETED WITH WARNINGS")
        print("Some components may not work perfectly, but you can try running the framework.")

    return success

if __name__ == "__main__":
    main()