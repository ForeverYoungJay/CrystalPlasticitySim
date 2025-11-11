


---



# CrystalPlasticitySim



*A multi-agent system that automates crystal plasticity workflows with DAMASK 3.0—covering input generation, simulation runs, post-processing, and parameter/boundary-condition optimization.*



> This repository accompanies the manuscript **“AI Agents for automating materials research: a case study of crystal plasticity simulations”** by **Jiyi Yang, Yoshinao Kobayashi, and Masahiko Demura (NIMS)**. The paper details the architecture, prompts, and case studies (Ni₃Al single crystal). See the **Citation** section below. 



---

## Highlights

* **End-to-end automation** of DAMASK 3.0 simulations: pre-processing → execution → post-processing.
* **Three collaborating agents** (Supervisor, Simulation, Computational Assistant) orchestrated with LangGraph.
* **Turn-key optimizers** for:

  * **Slip-related parameter calibration** (e.g., initial CRSS, saturation stress, hardening modulus).
  * **Boundary-condition fitting** (e.g., shear components of the deformation gradient to match a target quaternion).
* **Reproducibility by design:** versioned scripts, logged runs, deterministic file naming, and structured outputs.

> Architecture overview is shown in **Figure 1** (p. 6), with a full workflow trace in **Figure 7** (p. 33). Case-study results include stress–strain fitting (**Figure 3**, p. 31) and orientation-matching convergence (**Figures 5–6**, pp. 32–33). Tables of tuned parameters and optimized gradients are in **Tables 6–7** (pp. 31–32). 

---

## Repository layout

```
CrystalPlasticitySim/
├─ prompt.py                    # Role prompts & templates for all agents
├─ crystalplasticity/
│  ├─ damask_yaml.py            # Edit/validate DAMASK YAML (materials, loads)
│  ├─ damask_simulation.py      # Thin wrapper to run DAMASK and capture logs
│  ├─ damask_results.py         # Parse .hdf5 outputs, compute metrics
│  └─ utils.py                  # Common helpers (pathing, logging, I/O)
├─ agents/
│  ├─ supervisor.py             # Task decomposition, orchestration, termination
│  ├─ simulation_agent.py       # Pre/Run/Post with DAMASK tools
│  └─ compute_agent.py          # Env setup, script generation, debugging
├─ workflows/
│  ├─ optimize_parameters.py    # Case #1 (slip parameters)
│  └─ optimize_boundary.py      # Case #2 (F12, F13, F23 to match quaternion)
├─ examples/
│  ├─ workdir/                  # Example inputs & experimental data
│  └─ notebooks/                # Optional demo notebooks
├─ requirements.txt             # Python dependencies
├─ README.md
└─ LICENSE
```

> The paper explicitly mentions `prompt.py` and a DAMASK-focused tools trio (`damask_yaml.py`, `damask_simulation.py`, `damask_results.py`). 

---

## Prerequisites

* **Python** ≥ 3.10
* **DAMASK 3.0** installed and available on `PATH` (e.g., `damask_grid`). 
* A UNIX-like shell (Linux/macOS) recommended
* (Optional) **conda** or **venv** for isolation
* GPU not required; CPU is fine (runtime depends on model/mesh size)

---

## Install

```bash
# 1) clone
git clone https://github.com/ForeverYoungJay/CrystalPlasticitySim.git
cd CrystalPlasticitySim

# 2) create environment (example with venv)
python -m venv .venv
source .venv/bin/activate

# 3) install python deps
pip install -r requirements.txt

# 4) verify DAMASK (should return usage/help)
DAMASK_grid --help
```

---

## Quick start

### 0) Prepare a working directory

Place your **DAMASK input YAMLs** (materials, geometry/load) and any **experimental data** under a `workdir` (see `examples/workdir` for templates). The agents read/modify files *in place* and log all runs.

### 1) Optimize slip-related parameters (Case #1)

This reproduces the Ni₃Al stress–strain calibration described in the paper (MAPE < 2% using a global optimizer). **Ranges** for the main parameters (initial CRSS, saturation stress, hardening modulus) are given in **Table 5**; an example optimized set is in **Table 6** (p. 31). 

```
Optimize the slip-related material parameters in the DAMASK material file for the Ni₃Al17-A1 alloy.

Goal:
Minimize the mean absolute percentage error (MAPE) between simulated and experimental stress-strain curves. The target is to get the error below 0.1.

Parameters to tune (related to slip behavior):
Initial critical shear stress for slip — between 27 MPa and 90 MPa

Maximum critical shear stress for slip — between 1000 MPa and 5000 MPa

Initial hardening modulus for slip-slip interactions — between 100 MPa and 500 MPa

Additional instructions:
The DAMASK input files and experimental stress-strain data are in the workdir folder.

Clean the experimental data before using it in the optimization.

Use an efficient optimization algorithm to search the parameter space.

During optimization, log every step, not just the best result.

Logging:
Create a CSV file named optimization_results.csv. For each step of the optimization, append a row containing:

The current values of the three parameters

The corresponding computed MAPE

Make sure every trial (not just the final/best one) is recorded in the CSV.
```

**Outputs (in `workdir/outputs/parameters/`)**

* `optimization_results.csv` (per-iteration parameters & error)
* `best_params.yaml` (material YAML with injected best values)
* `fit_curve.png` & `mape_trace.png` (see **Figure 4**, p. 32 for an example trace) 

### 2) Optimize boundary conditions to match a target quaternion (Case #2)

This refines **F₁₂, F₁₃, F₂₃** within tight bounds to minimize the deviation angle to a **target quaternion** (e.g., `[0.034, 0.567, 0.384, 0.726]`). See **Table 7** (p. 32) and **Figure 6** (p. 33) for convergence. 

```bash
Optimize the three independent deformation gradients (F12, F13, F23) 
in the load file within the range of -0.00300 to 0.00300. The goal is to 
minimize the deviation angle between the simulated orientation quaternion 
from the DAMASK simulation and the experimental orientation quaternion 
[0.03451538, 0.56773038, 0.38495706, 0.72684178] within a 1-degree threshold. 
The initial configuration files for the DAMASK simulation are available 
in the 'workdir' folder. Perform optimization iteratively by adjusting 
F12, F13, and F23, running the DAMASK simulation, and computing the 
deviation angle. Use an efficient optimization algorithm to find the optimal 
deformation gradient values. Create a csvfile 'optimization_results.csv' to 
log the current values of F12, F13, and F23, and its simulation quaternion, 
along with the computed deviation angle for each iteration of the optimization process. 
And save the figure of how the best (minimum) deviation angle evolves during an optimization process.
```

**Outputs (in `workdir/outputs/boundary/`)**

* `optimization_results.csv` (F₁₂, F₁₃, F₂₃, simulated quaternion, deviation angle)
* `best_load.yaml` (load YAML with best values)
* `deviation_trace.png` (cumulative minimum angle vs. iteration)

---

## How it works

* **Supervisor Agent**
  Decomposes user goals, delegates tasks, tracks progress, and decides when to stop. (Role described on p. 6; prompt example p. 9.) 
* **Simulation Agent**
  Pre-processing → run DAMASK → post-processing. Handles YAML generation/update, execution, and parsing of HDF5 outputs (p. 6–8). 
* **Computational Assistant Agent**
  Sets up the Python environment, installs packages on-the-fly, generates/executes scripts, and self-heals upon errors with versioned scripts (p. 7–8). 

Agents are connected with **LangGraph**; prompts are codified in `prompt.py`, and domain-specific tools live under `crystalplasticity/`. The design favors **determinism and auditability**: absolute paths, unique run IDs, and consistent filenames (pp. 8–12). 

---

## Reproducibility & logging

Every optimization and simulation:

* writes a run log (e.g., `damask_monitor.log`),
* persists intermediate YAML/script versions,
* saves per-iteration results to CSV and figures for inspection (pp. 18–23). 

---

## Tips & troubleshooting

* **DAMASK not found**: ensure `damask_grid` is on `PATH` and matches the expected **3.0** series. 
* **Long runs**: reduce mesh size, population size (`--pop_size`), or iteration limits (`--max_iters`) for quick tests; increase later.
* **Failed iterations**: the Compute Agent auto-fixes common errors by generating new script versions (`version_1.py`, `version_2.py`, …). Check the `outputs/*/logs/` folder.
* **Custom objectives**: extend `damask_results.py` with your metric (e.g., texture, slip activity) and point the workflow to your scorer.

---

## Extending to other solvers

The agent/toolkit split is solver-agnostic: replace DAMASK-specific readers/writers and the execution wrapper to integrate **phase-field**, **MD**, or **FEM** tools while keeping the orchestration logic intact (pp. 24–25). 

---

## Citation

If you use **CrystalPlasticitySim**, please cite:

> **Yang, Jiyi; Kobayashi, Yoshinao; Demura, Masahiko.**
> *AI Agents for automating materials research: a case study of crystal plasticity simulations.*
> (Manuscript; see repo/paper for details.) 

You may also reference specific results and figures described in the manuscript:

* Architecture (**Fig. 1**, p. 6)
* Parameter optimization & fit (**Table 6**, **Fig. 3–4**, pp. 31–32)
* Boundary-condition optimization & convergence (**Table 7**, **Fig. 5–6**, pp. 32–33)
* Full workflow trace (**Fig. 7**, p. 33) 

---

## License

This project’s license is provided in `LICENSE`. If missing, please add one (e.g., MIT, BSD-3-Clause, Apache-2.0) to clarify permitted use.

---

## Acknowledgments

Supported in part by **MEXT Program: Data Creation and Utilization Type Material Research and Development Project** (JPMXP1122684766). 

---

**Questions or ideas?** Feel free to open an issue or start a discussion.
