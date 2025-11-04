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
```

### Running Your First Benchmark

1. **Validate Dataset:**
```bash
cd Quantitative
python dataset_loader.py
```

2. **Run Mini Benchmark:**
```bash
python run_mini_benchmark.py
```

This will evaluate 5 tasks with available models and save results to `../results/mini_benchmark/`.

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
Paper_Own/
├── Quantitative/
│   ├── Eval_Pipeline.py          # Main evaluation pipeline
│   ├── model_interface.py        # AI model integration (Ollama/HF)
│   ├── dataset_loader.py         # Task loading utilities
│   ├── statistical_analysis.py   # Statistical analysis module
│   ├── visualizations.py         # Plotting and visualization
│   ├── run_mini_benchmark.py     # Quick test runner
│   └── dataset/
│       ├── tasks.json            # Task metadata
│       ├── combinational/        # Combinational circuits
│       ├── sequential/           # Sequential circuits
│       ├── fsm/                  # Finite state machines
│       └── mixed/                # Mixed designs
├── results/                      # Generated outputs
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

- ✅ **5 starter tasks** (3 combinational, 2 sequential)
- 🚧 **Expanding to 120 tasks** (in progress)
  - 40 combinational circuits
  - 40 sequential circuits
  - 20 FSM designs
  - 20 mixed designs

## 🛠️ Development Roadmap

### Phase 1: Core Implementation ✅
- [x] Pipeline infrastructure
- [x] Model integration (Ollama/HF)
- [x] Starter dataset (5 tasks)
- [x] Statistical analysis
- [x] Visualization module

### Phase 2: Dataset Expansion 🚧
- [ ] Expand to 30 tasks (Week 1-2)
- [ ] Expand to 60 tasks (Week 3-4)
- [ ] Reach 120 tasks target (Week 5-6)

### Phase 3: Advanced Features 📋
- [ ] Fault injection for testbench evaluation
- [ ] Prompt template variations
- [ ] Coverage analysis
- [ ] Error taxonomy

### Phase 4: Full Benchmark 📋
- [ ] Run complete experiments
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

**Status**: Active Development | **Last Updated**: October 2025

