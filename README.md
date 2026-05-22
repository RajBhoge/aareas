# Privacy-Preserving Synthetic Data Generation for Smart Grid Cybersecurity (PPSDG)

Research project implementing a **Privacy-Preserving Synthetic Data Generation Framework (PPSDG-F)** for Smart Grid Cybersecurity, featuring federated learning, fuzzy synthetic data generation, and adaptive FDI (False Data Injection) attack intelligence.

## Research Overview

This repository contains research-based implementations, presentations, and architecture designs for a 5 ECTS course project at **Friedrich-Alexander-Universität Erlangen-Nürnberg (FAU)**.

**Research Question:** Can AI-driven FDI attacks outperform static approaches through real-time learning and adaptation?

**Novel Contribution:** First implementation of adaptive FDI attack intelligence using reinforcement learning to optimize attack strategies in real-time — achieving 33.3% better detection evasion than static baselines.

## Repository Structure

```
aareas/
├── research_based_implementation/   # Full PPSDG-F framework (Python)
│   ├── fedgrid_shield.py            # Federated learning + intrusion detection
│   ├── fuzzy_synthetic_generator.py # Fuzzy qualitative synthetic data
│   ├── integrated_ppsdg_framework.py
│   └── stpt_privacy.py              # Differential privacy for time series
├── software_based_implementation/   # Standalone smart grid simulator
│   ├── software_smart_grid_simulator.py
│   └── software_network_simulator.py
├── newresearch/                     # Adaptive FDI attack research
│   ├── adaptive_fdi_research_framework.py
│   ├── adaptive_fdi_attack_intelligence.py
│   └── research_summary.md
├── software_course_results/         # Course results and analysis
└── *.pptx / *.png                   # Presentations and architecture diagrams
```

## Key Research Results

| Metric | Adaptive (RL) | Static Baseline |
|--------|--------------|-----------------|
| Attack Success Rate | 83.3% | 90.0% |
| Detection Rate | 50.0% | 83.3% |
| **Detection Evasion** | **+33.3%** | — |
| Learning Improvement | +20.0% over episodes | — |

The adaptive system trades raw success rate for significantly better stealth — a meaningful trade-off in real-world adversarial scenarios.

## Research Foundation

Based on 5 peer-reviewed papers:
1. *Generating benchmark datasets for intrusion detection* — Computers & Security, 2012
2. *Fuzzy qualitative IDS dataset generation* — Computer Networks, 2017
3. *Differentially Private Electricity Time Series* — ArXiv, 2024
4. *Privacy in Smart Grids* — Dissertation, 2013
5. *Federated Learning for Smart Grid* — IEEE Access, 2021

## Technologies

| Technology | Purpose |
|------------|---------|
| Python | Core implementation language |
| Federated Learning | Privacy-preserving distributed ML |
| Q-Learning (RL) | Adaptive FDI attack intelligence |
| Differential Privacy | Time-series data privacy |
| Fuzzy Logic | Synthetic dataset generation |

## Author

**Raj Bhoge** — MSc ICT Student, FAU Erlangen-Nürnberg | Cloud & AI Engineer  
[GitHub](https://github.com/RajBhoge) | [LinkedIn](https://www.linkedin.com/in/raj-bhoge-834280194/)
