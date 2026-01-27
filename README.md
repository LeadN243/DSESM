# Portugal Energy System Model - PyPSA

**Group Q** - Data Science for Energy System Modeling (DSESM)

## 📋 Project Overview

This repository contains a PyPSA-based energy system model for Portugal, analyzing the country's electricity sector with a focus on renewable energy integration, network optimization, and policy scenarios. The model incorporates:

- High-resolution temporal and spatial data
- Renewable energy resources (solar, wind, hydro)
- Conventional generation capacity
- Transmission network infrastructure
- Load profiles and demand patterns
- Climate and weather data integration via Atlite

## 🎯 Project Objectives

1. Build a comprehensive PyPSA model of Portugal's electricity system
2. Analyze renewable energy integration potential
3. Evaluate network constraints and optimal capacity expansion
4. Compare policy scenarios and their impact on system costs and emissions
5. Generate reproducible results with open-source tools

## 📁 Repository Structure

```
DSESM/
├── data/
│   ├── raw/               # Raw data (not tracked in git)
│   └── processed/         # Cleaned and processed data
│       ├── eligibility/   # Geographic eligibility data
│       ├── load/          # Demand profiles
│       └── regions/       # Regional boundaries
├── scripts/               # Python scripts for data processing and modeling (placeholder tracked)
├── notebooks/             # Jupyter notebooks for analysis and visualization (placeholder tracked)
├── docs/                  # Documentation and reports (placeholder tracked)
├── environment.yml        # Conda environment specification
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## 🚀 Getting Started

### Prerequisites

- [Anaconda](https://www.anaconda.com/products/distribution) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
- Git
- Access to Climate Data Store (CDS) API (for ERA5 weather data)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/LeadN243/DSESM.git
   cd DSESM
   ```

2. **Create the conda environment**
   ```bash
   conda env create -f environment.yml
   conda activate dsesm
   ```

3. **Configure CDS API** (for climate data access)
   - Register at [Climate Data Store](https://cds.climate.copernicus.eu)
   - Create `~/.cdsapirc` with your credentials:
     ```
     url: https://cds.climate.copernicus.eu/api/v2
     key: YOUR_UID:YOUR_API_KEY
     ```

### Quick Start

```bash
# Activate environment
conda activate dsesm

# Run Jupyter notebook
jupyter notebook groupQasssignment.ipynb
```

## 📊 Data Sources

- **Network topology**: PyPSA-Eur or custom Portugal grid data
- **Renewable resources**: ERA5 climate reanalysis via Atlite
- **Load data**: ENTSO-E Transparency Platform
- **Generation capacity**: ENTSOE, IRENA, national statistics
- **Geographic data**: Natural Earth, OpenStreetMap
- **Hydro resources**: National reservoir and hydropower data

## 📦 Data Setup & Sharing

- Raw data is not included in the repo by default (see `.gitignore`). Place raw inputs in `data/raw/` locally.
- If you want data tracked on GitHub, remove the `data/raw/` ignore rule or force-add specific processed files (e.g., `git add -f data/processed/...`).
- Keep the `data/processed/` structure (`eligibility/`, `load/`, `regions/`) for cleaned outputs; commit only lightweight processed files needed to reproduce results.
- When sharing with collaborators, provide either the data files or a download link plus expected filenames/structure.

## 🔧 Methodology

1. **Data Collection**: Download and preprocess weather, load, and infrastructure data
2. **Network Building**: Create PyPSA network with nodes, generators, lines, and loads
3. **Resource Assessment**: Calculate renewable capacity factors using Atlite
4. **Model Optimization**: Solve optimal power flow and capacity expansion
5. **Scenario Analysis**: Compare baseline vs. policy scenarios
6. **Visualization**: Generate maps, time series, and summary statistics

## 📈 Key Features

- ✅ Hourly temporal resolution
- ✅ Multiple renewable technologies (onshore wind, solar PV, hydro)
- ✅ Network constraints and transmission modeling
- ✅ CO₂ emissions accounting
- ✅ Capacity expansion optimization
- ✅ Scenario comparison framework

## 👥 Team Members

- Team Member 1 - [Role/Contribution]
- Team Member 2 - [Role/Contribution]
- Team Member 3 - [Role/Contribution]
- Team Member 4 - [Role/Contribution]

## 📝 Usage Examples

```python
import pypsa
import pandas as pd

# Load the network
network = pypsa.Network("results/portugal_network.nc")

# Run optimization
network.optimize(solver_name='highs')

# Extract results
generation = network.generators_t.p
costs = network.objective
```

## 🔬 Results

Results will be saved in:
- `results/` - Optimized network files and statistics
- `figures/` - Generated plots and visualizations
- `docs/` - Final reports and documentation

## 📚 References

- PyPSA: https://pypsa.org
- Atlite: https://atlite.readthedocs.io
- PyPSA-Eur: https://pypsa-eur.readthedocs.io

## 📄 License

This project is for educational purposes as part of DSESM coursework.

## 🤝 Contributing

This is a group assignment project. All contributions should be coordinated within the team.

## ⚠️ Notes

- Raw data files are not tracked in git (see `.gitignore`)
- Large result files should be stored separately or compressed
- Ensure all code is properly documented and reproducible
