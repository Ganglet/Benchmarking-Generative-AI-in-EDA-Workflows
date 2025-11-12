# Benchmarking Generative AI in EDA Workflows

A comprehensive benchmarking framework for evaluating open-source generative AI models on automated Verilog HDL and testbench generation tasks.

## 📋 Overview

This project establishes the first structured, reproducible benchmark for AI-assisted hardware design at the RTL (Register Transfer Level). It evaluates models across:

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

This will evaluate all 20 tasks with 3 repetitions per model and save results to `../results/phase2_benchmark/`.

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
│       ├── tasks.json            # Task metadata (20 tasks)
│       ├── combinational/        # Combinational circuits (9 tasks)
│       ├── sequential/           # Sequential circuits (6 tasks)
│       ├── fsm/                  # Finite state machines (3 tasks)
│       └── mixed/                # Mixed designs (2 tasks)
├── results/                      # Generated outputs
│   ├── Benchmark_6_Results/      # Phase 2 with sequential normalization
│   ├── Benchmark_7_Results/      # Phase 2 full dataset expansion
│   └── Benchmark_8_Results/      # Enhanced Phase 2 with comprehensive examples
├── figures/                      # Visualization outputs
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container definition
└── README.md                     # This file
```

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

- ✅ **20 benchmark tasks** (fully implemented and tested)
  - 9 combinational circuits (gates, adders, mux, decoder)
  - 6 sequential circuits (flip-flops, registers, counters)
  - 3 FSM designs (sequence detector, traffic light, turnstile)
  - 2 mixed/complex designs (priority encoder, ALU)
- 🚧 **Expanding to 120 tasks** (in progress)
  - Target: 40 combinational, 40 sequential, 20 FSM, 20 mixed

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

### Phase 3: Dataset Expansion 🚧
- [ ] Expand to 30 tasks
- [ ] Expand to 60 tasks
- [ ] Reach 120 tasks target

### Phase 4: Advanced Features 📋
- [ ] Fault injection for testbench evaluation
- [ ] Prompt template variations
- [ ] Coverage analysis
- [ ] Error taxonomy
- [ ] FSM functional correctness refinement

### Phase 5: Full Benchmark & Publication 📋
- [ ] Run complete experiments on expanded dataset
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

## 📄 License

[Your License Choice]

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📧 Contact

[Your contact information]

## 🙏 Acknowledgments

- HDLBits for circuit examples
- OpenCores for reference designs
- Open-source EDA tool developers

---

## 📈 Latest Benchmark Results (8th Benchmark)

**Enhanced Phase 2 with Comprehensive Examples and Post-Processing**

| Model | Syntax Validity | Simulation Pass | Generation Time |
|-------|----------------|-----------------|-----------------|
| **Llama-3-8B-Large** | 70.0% (σ=0.462) | 58.3% (σ=0.497) | 5.14s (σ=4.66s) |
| **StarCoder2-7B-Medium** | 55.0% (σ=0.502) | 35.0% (σ=0.481) | 3.46s (σ=5.82s) |
| **TinyLlama-1.1B-Small** | 65.0% (σ=0.481) | 45.0% (σ=0.502) | 4.71s (σ=2.24s) |

**Key Breakthroughs:**
- ✅ **FSM Syntax Validity**: StarCoder2 achieves 66.7% syntax validity for FSM tasks (previously 0%)
- ✅ **Mixed Design Success**: StarCoder2 achieves 66.7% functional correctness on priority encoder
- ✅ **Sequential Expansion**: All models handle T flip-flop, shift register, and PIPO register
- ✅ **Overall Improvement**: Significant gains from 7th to 8th benchmark across all models

See `Quantitative/Research_Data/8th_Benchmark_Results.md` for detailed analysis.

---

**Status**: Active Development | **Last Updated**: November 2025

