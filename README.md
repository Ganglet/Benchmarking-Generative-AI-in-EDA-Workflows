# Benchmarking Generative AI in EDA Workflows

A comprehensive benchmarking framework for evaluating open-source generative AI models on automated Verilog HDL and testbench generation tasks.

## 📋 Overview

This project establishes the first structured, reproducible benchmark for AI-assisted hardware design at the RTL (Register Transfer Level). It evaluates models across:

- **Final dataset scope**: 50 curated Verilog design and verification tasks spanning 23 combinational, 14 sequential, 8 FSM, and 5 mixed/complex designs.

- **Circuit (HDL) generation** from textual specifications
- **Testbench generation** for functional verification
- **Quantitative benchmarking** against reference implementations

## 🎯 Models Evaluated

| Tier | Model | Size | Purpose |
|------|-------|------|---------|
| Large | Llama 3 8B Instruct | 8B | High-quality general-purpose baseline |
| Medium | StarCoder2 | 7B | Code-specialized mid-tier model |
| Small | TinyLlama | 1.1B | Lightweight resource-constrained baseline |

<img width="2830" height="1272" alt="pipeline_flow_diagram" src="https://github.com/user-attachments/assets/d0444274-b7cb-4b16-99aa-cfa5f6e74109" />

## 📊 Evaluation Metrics

### Metrics Computed in Every Benchmark Run
- **Syntax Validity (SV)**: % of files that compile without errors (Verilator + iverilog)
- **Functional Correctness (FC)**: % producing expected simulation outputs (iverilog + testbench)
- **Generation Time (GT)**: Average inference time per task
- **Compile Time**: Verilator/iverilog compilation time
- **Simulation Time**: iverilog/vvp simulation time

### Additional Metrics Computed in Phase 4+ Runs (Benchmarks 9, 10, 12)
- **Iteration Count**: Number of generation–evaluation cycles per task
- **Confidence Entropy**: Token-level entropy as a model confidence proxy
- **Waveform Diff Summary**: Signal-level mismatch between generated and reference waveform (when enabled)
- **Formal Equivalence Status**: Result of formal equivalence check (when enabled)
- **Semantic Repair Applied**: List of repair operations applied during iterative refinement

### Metrics Defined but NOT Computed
The following were originally planned but have **not been implemented** in any benchmark run:
- **Synthesis Quality (SQ)**: Gate count / area via Yosys — `SynthesisTool` class exists in code but is never invoked; all results have `gate_count=None`, `cell_count=None`
- **Testbench Detection Rate (TDR)**: Fault injection coverage — no fault injector built; `fault_detection_ratio` is always `None`
- **Prompt Sensitivity (PS)**: Variance across prompt templates A/B/C — each phase uses a single fixed prompt style; cross-template comparison not run
- **Hallucination Index (HI)**: Undeclared signal count — no code exists to detect these
- **Usability Score (US)**: Composite formula `0.4*FC + 0.3*SV + 0.2*(1−area) + 0.1*TDR` — never evaluated (depends on SQ and TDR)

## 🚀 Quick Start

### Prerequisites

**Required Tools:**
```bash
# Ubuntu/Debian
sudo apt-get install iverilog verilator yosys python3.10 python3-pip

# macOS
brew install icarus-verilog verilator yosys python@3.10
```

**Python Dependencies:**
```bash
pip install -r requirements.txt
```

**Optional Dependencies (for Phase 4 features):**
- `pyvcd>=0.4.0` - For waveform analysis (installed by default in requirements.txt)
- `pyverilog>=1.3.0` - For AST-based code repair (installed by default in requirements.txt)

Note: These are optional. If not installed, Phase 4 will gracefully disable the corresponding features (waveform analysis, AST repair).

**AI Models (Ollama):**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull llama3
ollama pull tinyllama
ollama pull starcoder2:7b
```

**Note**: StarCoder2 can also be used via HuggingFace Transformers. See `model_interface.py` for configuration options.

### Running Your First Benchmark

1. **Validate Dataset:**
```bash
cd Quantitative
python dataset_loader.py
```

2. **Run Phase 2 Benchmark (Recommended):**
```bash
python run_phase2.py
```

This runs the full benchmark dataset (currently 50 tasks) with 3 repetitions per model and saves results to `../results/phase2_benchmark/`.

**Alternative: Run Mini Benchmark:**
```bash
python run_mini_benchmark.py
```

This evaluates 5 starter tasks and saves results to `../results/mini_benchmark/`.

3. **Analyze Results:**
```bash
python statistical_analysis.py ../results/mini_benchmark/benchmark_results.json
```

4. **Generate Visualizations:**
```bash
python visualizations.py ../results/mini_benchmark/benchmark_results.json ../figures/
```

## 🐳 Docker Setup

> **Note on reproducibility**: All 12 benchmarks (1,610 runs) were conducted locally on macOS (Apple Silicon) using Icarus Verilog 12.0, Verilator 5.038, and Yosys 0.58 installed via Homebrew. The Docker setup is provided to allow others to run the pipeline on any platform without manual tool installation. It has been validated by successfully running the mini benchmark (5 tasks × 3 models × 3 repetitions) end-to-end inside the container.
>
> <img width="1728" height="1117" alt="Screenshot 2026-03-31 at 11 52 06 AM" src="https://github.com/user-attachments/assets/707d7cbc-2e82-450f-92d1-be0bc2528e9c" />

> Tool versions inside the container (Debian Trixie apt): Icarus Verilog 12.0, Verilator 5.032, Yosys 0.52.

### Prerequisites

**On the Host Machine:**
1. Install Ollama:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama serve  # Start Ollama service
   ```
2. Pull required models:
   ```bash
   ollama pull llama3
   ollama pull tinyllama
   ollama pull starcoder2:7b
   ```

### Build and Run with Docker:

```bash
# Build image
docker-compose build

# Run container (Ollama connection configured automatically)
docker-compose up -d

# Access shell
docker exec -it eda_benchmark bash

# Inside container — run mini benchmark (5 tasks, validated):
cd /workspace/Quantitative
python run_mini_benchmark.py

# Or run the full 50-task benchmark:
python run_phase5.py
```

### Docker-Ollama Connection

Ollama runs on the host machine; the container connects to it via `OLLAMA_BASE_URL`:
- **Windows/Mac Docker Desktop**: Uses `http://host.docker.internal:11434` (configured automatically)
- **Linux**: Set `OLLAMA_BASE_URL` to your host IP:
  ```bash
  export OLLAMA_BASE_URL=http://your-host-ip:11434
  docker-compose up -d
  ```

**Verify Connection:**
```bash
# Inside container
python -c "from model_interface import OllamaInterface; OllamaInterface('llama3')"
```

## 📁 Project Structure

```
Paper/
├── DATASET_LICENSE                                  # Dataset license (CC BY-NC 4.0)
├── Docs/                                            # Extended documentation set
│   ├── architecture.md
│   ├── benchmark_history.md
│   ├── dataset_description.md
│   └── ...
├── Quantitative/                                    # Core benchmarking stack
│   ├── Eval_Pipeline.py          # Main evaluation pipeline
│   ├── instruction.json          # Methodology + run configuration
│   ├── model_interface.py        # AI model integration (Ollama/HF)
│   ├── dataset_loader.py         # Task loading utilities
│   ├── statistical_analysis.py   # Statistical analysis module
│   ├── visualizations.py         # Plotting and visualization
│   ├── confidence_tracker.py     # Entropy-based confidence modeling
│   ├── feedback_generator.py     # Error feedback for refinement loops
│   ├── iterative_evaluator.py    # Iterative evaluation driver
│   ├── waveform_analyzer.py      # Waveform comparison + diffing
│   ├── formal_verifier.py        # Formal equivalence checks
│   ├── ast_repair.py             # AST-guided repair helpers
│   ├── semantic_repair.py        # Semantic repair orchestrator
│   ├── phase4_config.py          # Phase 4 feature toggles
│   ├── phase5_config.py          # Phase 5 experiment settings
│   ├── phase5_feedback.py        # Prompt templates for Phase 5
│   ├── phase5_repair.py          # Phase 5 repair utilities
│   ├── run_phase1.py             # Phase 1: Few-shot prompting
│   ├── run_phase2.py             # Phase 2: Constrained prompts + post-processing
│   ├── run_phase3.py             # Phase 3: Iterative refinement (legacy)
│   ├── run_phase4.py             # Phase 4: Semantic-aware refinement
│   ├── run_phase5.py             # Phase 5: Extended repair experiments
│   ├── Research_Data/            # Benchmark analysis reports (1st–12th)
│   │   ├── 1st_Benchmark_Results.md
│   │   ├── ...
│   │   └── 12th_Benchmark_Results.md
│   └── dataset/
│       ├── tasks.json            # Task metadata (50 tasks, final scope)
│       ├── combinational/        # Combinational circuits (23 tasks)
│       ├── sequential/           # Sequential circuits (14 tasks)
│       ├── fsm/                  # Finite state machines (8 tasks)
│       └── mixed/                # Mixed designs (5 tasks)
├── Research_Paper/                                   # Reference papers + citations
│   ├── CITATION.md
│   └── *.pdf
├── results/                                          # Generated benchmark outputs
│   ├── Benchmark_1&2_Results/
│   ├── Benchmark_3&4_Results/
│   ├── Benchmark_5_Results/
│   ├── Benchmark_6_Results/
│   ├── Benchmark_7_Results/
│   ├── Benchmark_8_Results/
│   ├── Benchmark_9_Results/
│   ├── Benchmark_10_Results/
│   ├── Benchmark_11_Results/
│   ├── Benchmark_12_Results/
│   └── mini_benchmark/                               # Docker-validated mini benchmark results
├── figures/                                          # Visualization exports by benchmark
│   ├── 1st_Benchmark_figures/
│   ├── ...
│   └── 12th_Benchmark_figures/
├── docker-compose.yml                               # Containerized workflow entrypoint
├── Dockerfile                                        # Base container definition
├── LICENSE                                           # MIT license (code)
├── README.md                                         # This file
├── ROADMAP.md                                        # Development roadmap
└── requirements.txt                                  # Python dependencies
```

## 📊 Benchmark Test History

This section documents all 12 benchmark tests, which files were used, and their key features.

### Core Files (Used in All Benchmarks)
- **`Eval_Pipeline.py`** - Main evaluation pipeline (compilation, simulation, metrics)
- **`model_interface.py`** - AI model integration (Ollama/HuggingFace interfaces)
- **`dataset_loader.py`** - Task loading and validation utilities
- **`instruction.json`** - Configuration and methodology specifications

### Analysis Tools (Post-Processing)
- **`statistical_analysis.py`** - Standalone statistical analysis tool
- **`visualizations.py`** - Standalone visualization generation tool

---

### Benchmark 1: Initial Pipeline Test
**Runner**: `run_phase1.py`  
**Methodology**: Phase 1 - Few-shot prompting  
**Tasks**: 5 tasks (first 5 from dataset)  
**Models**: Llama-3-8B, TinyLlama-1.1B  
**Repetitions**: 1 per task  
**Key Features**:
- Basic few-shot prompting with examples
- No post-processing
- System configuration validation (EDA tools)

**Results**: `results/Benchmark_1&2_Results/`  
**Analysis**: `Research_Data/1st_Benchmark_Results.md`

---

### Benchmark 2: Constrained Prompts Introduction
**Runner**: `run_phase2.py`  
**Methodology**: Phase 2 - Constrained prompts + post-processing  
**Tasks**: 5 tasks  
**Models**: Llama-3-8B, TinyLlama-1.1B  
**Repetitions**: 1 per task  
**Key Features**:
- Task-specific module/port name constraints
- Basic post-processing fixes
- Module name extraction and correction

**Results**: `results/Benchmark_1&2_Results/`  
**Analysis**: `Research_Data/2nd_Benchmark_Results.md`

---

### Benchmark 3: Post-Processing Refinement
**Runner**: `run_phase2.py`  
**Methodology**: Phase 2 - Enhanced post-processing  
**Tasks**: 5 tasks  
**Models**: Llama-3-8B, TinyLlama-1.1B  
**Repetitions**: 1 per task  
**Key Features**:
- Improved post-processing with SystemVerilog→Verilog conversion
- BSV construct removal
- Port name normalization

**Results**: `results/Benchmark_3&4_Results/`  
**Analysis**: `Research_Data/3rd_Benchmark_Results.md`

---

### Benchmark 4: Statistical Analysis Introduction
**Runner**: `run_phase2.py`  
**Methodology**: Phase 2 + Statistical analysis (3 repetitions)  
**Tasks**: 5 tasks  
**Models**: Llama-3-8B, TinyLlama-1.1B  
**Repetitions**: 3 per task (per `instruction.json`)  
**Key Features**:
- Multiple repetitions for statistical significance
- Mean rates with standard deviations (σ)
- Variance quantification

**Results**: `results/Benchmark_3&4_Results/`  
**Analysis**: `Research_Data/4th_Benchmark_Results.md`

---

### Benchmark 5: Medium Model Introduction
**Runner**: `run_phase2.py`  
**Methodology**: Phase 2 + StarCoder2-7B addition  
**Tasks**: 5 tasks  
**Models**: Llama-3-8B, StarCoder2-7B, TinyLlama-1.1B  
**Repetitions**: 3 per task  
**Key Features**:
- Three-tier model comparison (Large/Medium/Small)
- StarCoder2 code-specialized model evaluation
- Sequential logic performance analysis

**Results**: `results/Benchmark_5_Results/`  
**Analysis**: `Research_Data/5th_Benchmark_Results.md`

---

### Benchmark 6: Sequential Normalization Upgrade
**Runner**: `run_phase2.py`  
**Methodology**: Phase 2 + Sequential normalization post-processing  
**Tasks**: 5 tasks  
**Models**: Llama-3-8B, StarCoder2-7B, TinyLlama-1.1B  
**Repetitions**: 3 per task  
**Key Features**:
- Enhanced `post_process_verilog()` with sequential normalization
- Enforced `begin/end` structure for sequential blocks
- Sequential template matching and repair
- DFF and counter reliability improvements

**Results**: `results/Benchmark_6_Results/`  
**Analysis**: `Research_Data/6th_Benchmark_Results.md`

---

### Benchmark 7: Full Dataset Expansion
**Runner**: `run_phase2.py`  
**Methodology**: Phase 2 + Full 20-task dataset  
**Tasks**: 20 tasks (9 combinational, 6 sequential, 3 FSM, 2 mixed)  
**Models**: Llama-3-8B, StarCoder2-7B, TinyLlama-1.1B  
**Repetitions**: 3 per task  
**Key Features**:
- Complete benchmark coverage
- Category-specific performance analysis
- FSM and mixed design challenges exposed

**Results**: `results/Benchmark_7_Results/`  
**Analysis**: `Research_Data/7th_Benchmark_results.md`

---

### Benchmark 8: Comprehensive Examples & Enhanced Post-Processing
**Runner**: `run_phase2.py`  
**Methodology**: Phase 2 + Comprehensive examples for all task types  
**Tasks**: 20 tasks  
**Models**: Llama-3-8B, StarCoder2-7B, TinyLlama-1.1B  
**Repetitions**: 3 per task  
**Key Features**:
- Complete examples for all task categories (combinational, sequential, FSM, mixed)
- Enhanced post-processing with FSM/mixed template generation
- Category-specific scaffolding to prevent truncation
- FSM syntax validity breakthrough (StarCoder2: 0% → 66.7%)

**Results**: `results/Benchmark_8_Results/`  
**Analysis**: `Research_Data/8th_Benchmark_Results.md`

---

### Benchmark 9: Semantic-Aware Iterative Refinement (Phase 4)
**Runner**: `run_phase4.py`  
**Methodology**: Phase 4 - Semantic-aware iterative refinement  
**Tasks**: 20 tasks  
**Models**: Llama-3-8B, StarCoder2-7B, TinyLlama-1.1B  
**Repetitions**: 3 per task  
**Key Features**:
- **Semantic repair components**:
  - `waveform_analyzer.py` - Waveform difference analysis
  - `formal_verifier.py` - Formal equivalence checking
  - `ast_repair.py` - AST-based code repair
  - `semantic_repair.py` - Orchestrates semantic repair tools
- **Iterative evaluation**:
  - `iterative_evaluator.py` - Adaptive iterative refinement loop
  - `feedback_generator.py` - Error feedback generation
  - `confidence_tracker.py` - Confidence modeling (entropy tracking)
- **Configuration**:
  - `phase4_config.py` - Phase 4 feature flags and settings
- **Imports from Phase 2**:
  - Uses `extract_module_name()`, `get_port_spec()`, `get_constrained_prompt()`, `post_process_verilog()` from `run_phase2.py`

**Results**: `results/Benchmark_9_Results/`  
**Analysis**: `Research_Data/` (if available)

---

### Benchmark 10: Final 50-Task Dataset Validation
**Runner**: `run_phase4.py`  
**Methodology**: Phase 4 - Semantic-aware iterative refinement with expanded dataset  
**Tasks**: 50 tasks (23 combinational, 14 sequential, 8 FSM, 5 mixed)  
**Models**: Llama-3-8B, StarCoder2-7B, TinyLlama-1.1B  
**Repetitions**: 3 per task (450 total generations)  
**Key Features**:
- Validates scalability of the Phase 4 pipeline on the full 50-task scope
- Semantic repair stack (waveform analysis, formal verification, AST repair) plus confidence tracking
- Captures per-model entropy/iteration statistics for the larger dataset
- Highlights remaining FSM and mixed-design functional correctness gaps

**Results**: `results/Benchmark_10_Results/`  
**Analysis**: `Research_Data/10th_Benchmark_Results.md`

---

### Benchmark 11: Single-Model Reproducibility & Generation Time Optimization
**Runner**: `run_phase4.py`
**Methodology**: Phase 4 - Single-model validation run (Llama-3-8B only)
**Tasks**: 50 tasks (full dataset)
**Models**: Llama-3-8B only
**Repetitions**: 3 per task (150 total generations)
**Key Features**:
- Validates reproducibility of Benchmark 10 results with a single model
- Measures generation time optimization (8.84s → 4.77s, −46%)
- Confirms syntax validity (71.3%) and simulation pass rate (61.3%) are stable

**Results**: `results/Benchmark_11_Results/`
**Analysis**: `Quantitative/Research_Data/11th_Benchmark_Results.md`

---

### Benchmark 12: Phase 5 Quality-Focused Multi-Model Run
**Runner**: `run_phase5.py`  
**Methodology**: Phase 5 strict mode (waveform + formal enabled, semantic/AST repair)  
**Tasks**: 50 tasks (full dataset)  
**Models**: Llama-3-8B, StarCoder2-7B, TinyLlama-1.1B  
**Repetitions**: 3 per task (450 total generations)  
**Key Features**:
- Strict mode (no entropy skips), waveform analysis, formal verification for FSM/complex tasks
- Higher iteration caps (up to 6) with lower improvement threshold for refinement
- Confidence tracking, semantic repair, and AST repair kept enabled

**Results**: `results/Benchmark_12_Results/`  
**Analysis**: `Quantitative/Research_Data/12th_Benchmark_Results.md`

---

<img width="3496" height="4470" alt="task_performance_matrix" src="https://github.com/user-attachments/assets/93769eda-8356-4557-9e47-bd6e5820fbd2" />
<img width="2956" height="2534" alt="model_comparison_radar" src="https://github.com/user-attachments/assets/e78f850f-7a1e-4b01-8c4d-0733676d0782" />


### File Usage Summary

| File | Benchmarks Used | Purpose |
|------|----------------|---------|
| `run_phase1.py` | 1 | Phase 1: Few-shot prompting baseline |
| `run_phase2.py` | 2-8 | Phase 2: Constrained prompts + post-processing (evolved across benchmarks) |
| `run_phase3.py` | None | Phase 3: Iterative refinement (not used in final benchmarks) |
| `run_phase4.py` | 9, 10 | Phase 4: Semantic-aware iterative refinement |
| `run_phase5.py` | 12 | Phase 5: Enhanced FSM/mixed prompts + micro-repair |
| `waveform_analyzer.py` | 9, 10, 12 | Waveform analysis for semantic repair |
| `formal_verifier.py` | 9, 10, 12 | Formal verification for semantic repair |
| `ast_repair.py` | 9, 10, 12 | AST-based code repair |
| `semantic_repair.py` | 9, 10, 12 | Semantic repair orchestrator |
| `iterative_evaluator.py` | 9, 10, 12 | Adaptive iterative evaluation loop |
| `feedback_generator.py` | 9, 10 | Error feedback generation |
| `confidence_tracker.py` | 9, 10, 12 | Confidence modeling and entropy tracking |
| `phase4_config.py` | 9, 10 | Phase 4 configuration |
| `phase5_config.py` | 12 | Phase 5 configuration |
| `phase5_feedback.py` | 12 | Category-aware feedback templates for Phase 5 |
| `phase5_repair.py` | 12 | Phase 5 micro-repair engine |

---

### Evolution of Features

**Phase 1 → Phase 2 (Benchmarks 1-8)**:
- Few-shot prompting → Constrained prompts with exact module/port specs
- No post-processing → Comprehensive post-processing
- Single runs → Statistical analysis (3 repetitions)
- 5 tasks → 20 tasks (full dataset)
- 2 models → 3 models (added StarCoder2)
- Basic fixes → Sequential normalization + FSM/mixed templates

**Phase 2 → Phase 4 (Benchmarks 9–10)**:
- Single-pass generation → Iterative refinement with feedback
- Syntax-only validation → Semantic validation (waveform, formal verification)
- Static post-processing → Adaptive AST-based repair
- No confidence tracking → Confidence modeling with entropy
- Fixed methodology → Adaptive stopping based on confidence

**Phase 4 → Phase 5 (Benchmark 12)**:
- Standard constrained prompts → Enhanced FSM/mixed-specific prompts with reference templates
- Standard post-processing → Micro-repair engine runs before standard post-processing
- Generic feedback → Category-aware feedback targeting FSM and mixed design failure modes

## 📖 Usage Examples

### Test a Single Model:
```python
from model_interface import OllamaInterface
from dataset_loader import load_tasks_from_json
from Eval_Pipeline import BenchmarkPipeline

# Load tasks
tasks = load_tasks_from_json("dataset/tasks.json")

# Initialize model
model = OllamaInterface("llama3")

# Run evaluation
pipeline = BenchmarkPipeline(Path("./results"))
metrics = pipeline.evaluate_task(tasks[0], model)
```

### Compare Models:
```python
from statistical_analysis import BenchmarkAnalyzer

analyzer = BenchmarkAnalyzer("results/benchmark_results.json")
analyzer.print_summary_report()

# Statistical test
result = analyzer.paired_statistical_test("Llama-3-8B", "TinyLlama-1.1B")
print(f"p-value: {result['wilcoxon_p_value']}")
```

### Custom Visualization:
```python
from visualizations import BenchmarkVisualizer

viz = BenchmarkVisualizer(results_json="results/benchmark_results.json")
viz.plot_overall_comparison("figures/comparison.png")
viz.plot_pass_rate_by_category("figures/by_category.png")
```

## 🔬 Extending the Framework

### Adding New Tasks

1. Create reference Verilog and testbench files
2. Add entry to `dataset/tasks.json`:
```json
{
  "task_id": "new_task_001",
  "category": "combinational",
  "difficulty": "medium",
  "specification": "Design a...",
  "reference_hdl": "path/to/reference.v",
  "reference_tb": "path/to/testbench.v",
  "inputs": ["a", "b"],
  "outputs": ["y"]
}
```

### Adding New Models

```python
# For Ollama models
model = OllamaInterface("model-name")

# For HuggingFace models
from model_interface import HuggingFaceInterface
model = HuggingFaceInterface("org/model-name")
```

## 📊 Current Dataset

- ✅ **50 benchmark tasks** (finalized scope)
  - 23 combinational circuits (basic gates, arithmetic blocks, mux/decoder variants)
  - 14 sequential circuits (flip-flops, shift registers, counters, Johnson/PIPO variants)
  - 8 FSM designs (sequence detectors, controllers, traffic light)
  - 5 mixed/complex designs (priority encoder, ALU)
- 🛑 **Further dataset expansion intentionally paused at 50 tasks** to focus on semantic-aware refinement, evaluation quality, and documentation.

<img width="4124" height="2715" alt="dataset_statistics_dashboard" src="https://github.com/user-attachments/assets/bfa912e3-6530-4e38-a0ad-4542766d3b55" />

## 🛠️ Development Roadmap

### Phase 1: Core Implementation ✅
- [x] Pipeline infrastructure
- [x] Model integration (Ollama/HF)
- [x] Starter dataset (5 tasks)
- [x] Statistical analysis
- [x] Visualization module

### Phase 2: Enhanced Prompting & Post-Processing ✅
- [x] Constrained prompts with exact module/port specifications
- [x] Comprehensive examples for all task types (20 tasks)
- [x] Enhanced post-processing with FSM/mixed template generation
- [x] Sequential normalization for reliable sequential designs
- [x] Category-specific scaffolding to prevent truncation
- [x] Full 20-task benchmark evaluation (8th benchmark)

**Key Achievements:**
- **FSM Breakthrough**: StarCoder2 achieves 66.7% syntax validity for FSM tasks (previously 0%)
- **Mixed Design Success**: StarCoder2 achieves 66.7% functional correctness on priority encoder
- **Sequential Expansion**: All models handle expanded sequential library (T flip-flop, shift register, PIPO register)
- **Overall Improvement**: 70% syntax validity (Llama-3), 55% (StarCoder2), 65% (TinyLlama)

### Phase 3: Dataset Expansion ✅ (Concluded)
- [x] Expand to 30 tasks
- [x] Expand to 50 tasks (final scope)

*Decision*: Scope is intentionally capped at 50 curated tasks to prioritize deeper analysis, semantic-aware refinement, and documentation polish over further breadth.

### Phase 4: Full Benchmark & Publication ✅
- [x] Run complete experiments on final 50-task dataset (Benchmarks 10, 11, 12 — 1,610 total runs)
- [x] Generate publication-ready results
- [x] Write research paper (submitted for journal publication)


## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 🙏 Acknowledgments

- HDLBits for circuit examples
- OpenCores for reference designs
- Open-source EDA tool developers

---

## License

The **source code** in this repository is released under the **MIT License**.  
See: [LICENSE](LICENSE)

The **dataset files** (reference Verilog, testbenches, and `tasks.json`) are released under the  
**Creative Commons Attribution–NonCommercial 4.0 License (CC BY-NC 4.0)**.  
See: [DATASET_LICENSE](DATASET_LICENSE)

---

**Status**: Research complete, paper under journal review | **Last Updated**: March 2026
