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

## 📊 Evaluation Metrics

### Primary Metrics
- **Syntax Validity (SV)**: % of files that compile without errors
- **Functional Correctness (FC)**: % producing expected simulation outputs
- **Synthesis Quality (SQ)**: Cell count and logic depth
- **Testbench Detection Rate (TDR)**: Fault detection capability
- **Generation Time (GT)**: Average inference time

### Secondary Metrics
- **Prompt Sensitivity (PS)**: Variance across prompt templates
- **Hallucination Index (HI)**: Invalid construct frequency
- **Usability Score (US)**: Composite quality metric

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

### Build and Run with Docker:

```bash
# Build image
docker-compose build

# Run container
docker-compose up -d

# Access shell
docker exec -it eda_benchmark bash

# Inside container:
cd /workspace/Quantitative
python run_mini_benchmark.py
```

## 📁 Project Structure

```
Paper/
├── Quantitative/
│   ├── Eval_Pipeline.py          # Main evaluation pipeline
│   ├── model_interface.py        # AI model integration (Ollama/HF)
│   ├── dataset_loader.py         # Task loading utilities
│   ├── statistical_analysis.py   # Statistical analysis module
│   ├── visualizations.py         # Plotting and visualization
│   ├── run_mini_benchmark.py     # Quick test runner
│   ├── run_phase1.py             # Phase 1: Few-shot prompting
│   ├── run_phase2.py             # Phase 2: Constrained prompts + post-processing
│   ├── run_phase3.py             # Phase 3: Iterative refinement
│   ├── Research_Data/            # Benchmark analysis reports
│   │   ├── 1st_Benchmark_Results.md
│   │   ├── 6th_Benchmark_Results.md
│   │   ├── 7th_Benchmark_results.md
│   │   └── 8th_Benchmark_Results.md
│   └── dataset/
│       ├── tasks.json            # Task metadata (50 tasks, final scope)
│       ├── combinational/        # Combinational circuits (23 tasks)
│       ├── sequential/           # Sequential circuits (14 tasks)
│       ├── fsm/                  # Finite state machines (8 tasks)
│       └── mixed/                # Mixed designs (5 tasks)
├── results/                      # Generated outputs
│   ├── Benchmark_6_Results/      # Phase 2 with sequential normalization
│   ├── Benchmark_7_Results/      # Phase 2 full dataset expansion
│   └── Benchmark_8_Results/      # Enhanced Phase 2 with comprehensive examples
├── figures/                      # Visualization outputs
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container definition
└── README.md                     # This file
```

## 📊 Benchmark Test History

This section documents all 9 benchmark tests, which files were used, and their key features.

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

### File Usage Summary

| File | Benchmarks Used | Purpose |
|------|----------------|---------|
| `run_phase1.py` | 1 | Phase 1: Few-shot prompting baseline |
| `run_phase2.py` | 2-8 | Phase 2: Constrained prompts + post-processing (evolved across benchmarks) |
| `run_phase3.py` | None | Phase 3: Iterative refinement (not used in final benchmarks) |
| `run_phase4.py` | 9 | Phase 4: Semantic-aware iterative refinement |
| `waveform_analyzer.py` | 9 | Waveform analysis for semantic repair |
| `formal_verifier.py` | 9 | Formal verification for semantic repair |
| `ast_repair.py` | 9 | AST-based code repair |
| `semantic_repair.py` | 9 | Semantic repair orchestrator |
| `iterative_evaluator.py` | 9 | Adaptive iterative evaluation loop |
| `feedback_generator.py` | 9 | Error feedback generation |
| `confidence_tracker.py` | 9 | Confidence modeling and entropy tracking |
| `phase4_config.py` | 9 | Phase 4 configuration |

---

### Evolution of Features

**Phase 1 → Phase 2 (Benchmarks 1-8)**:
- Few-shot prompting → Constrained prompts with exact module/port specs
- No post-processing → Comprehensive post-processing
- Single runs → Statistical analysis (3 repetitions)
- 5 tasks → 20 tasks (full dataset)
- 2 models → 3 models (added StarCoder2)
- Basic fixes → Sequential normalization + FSM/mixed templates

**Phase 2 → Phase 4 (Benchmark 9)**:
- Single-pass generation → Iterative refinement with feedback
- Syntax-only validation → Semantic validation (waveform, formal verification)
- Static post-processing → Adaptive AST-based repair
- No confidence tracking → Confidence modeling with entropy
- Fixed methodology → Adaptive stopping based on confidence

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

### Phase 4: Advanced Features 📋
- [ ] Fault injection for testbench evaluation
- [ ] Prompt template variations
- [ ] Coverage analysis
- [ ] Error taxonomy
- [ ] FSM functional correctness refinement

### Phase 5: Full Benchmark & Publication 📋
- [ ] Run complete experiments on final 50-task dataset
- [ ] Generate publication-ready results
- [ ] Write research paper

## 📚 Citation

```bibtex
@inproceedings{benchmark-genai-eda,
  title={Benchmarking Generative AI in EDA Workflows},
  author={[Your Name]},
  year={2025},
  note={In preparation}
}
```

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

**Status**: Active Development | **Last Updated**: November 2025
