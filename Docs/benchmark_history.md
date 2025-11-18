# Benchmark Test History

This document documents all 10 benchmark tests, which files were used, and their key features.

## Core Files (Used in All Benchmarks)

- **`Eval_Pipeline.py`** - Main evaluation pipeline (compilation, simulation, metrics)
- **`model_interface.py`** - AI model integration (Ollama/HuggingFace interfaces)
- **`dataset_loader.py`** - Task loading and validation utilities
- **`instruction.json`** - Configuration and methodology specifications

## Analysis Tools (Post-Processing)

- **`statistical_analysis.py`** - Standalone statistical analysis tool
- **`visualizations.py`** - Standalone visualization generation tool

---

## Benchmark 1: Initial Pipeline Test

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

## Benchmark 2: Constrained Prompts Introduction

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

## Benchmark 3: Post-Processing Refinement

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

## Benchmark 4: Statistical Analysis Introduction

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

## Benchmark 5: Medium Model Introduction

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

## Benchmark 6: Sequential Normalization Upgrade

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

## Benchmark 7: Full Dataset Expansion

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

## Benchmark 8: Comprehensive Examples & Enhanced Post-Processing

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

## Benchmark 9: Semantic-Aware Iterative Refinement (Phase 4)

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
**Analysis**: `Research_Data/9th_Benchmark_Results.md`

**Key Results**:
- Llama-3-8B: 71.7% syntax, 61.7% simulation
- StarCoder2-7B: 56.7% syntax, 33.3% simulation
- TinyLlama-1.1B: 75.0% syntax, 51.7% simulation

---

## Benchmark 10: Semantic-Aware Iterative Refinement with Expanded Dataset

**Runner**: `run_phase4.py`  
**Methodology**: Phase 4 - Semantic-aware iterative refinement with expanded dataset  
**Tasks**: 50 tasks (23 combinational, 14 sequential, 8 FSM, 5 mixed)  
**Models**: Llama-3-8B, StarCoder2-7B, TinyLlama-1.1B  
**Repetitions**: 3 per task  
**Key Features**:
- Same Phase 4 features as Benchmark 9
- **Dataset expansion**: 2.5× increase from 20 to 50 tasks
- Validates scalability of semantic-aware iterative refinement
- Task tiering and fast-path optimizations for efficiency

**Results**: `results/Benchmark_9&10_Results/`  
**Analysis**: `Research_Data/10th_Benchmark_Results.md`

**Key Results**:
- Llama-3-8B: 71.3% syntax, 61.3% simulation (150 runs)
- StarCoder2-7B: 58.7% syntax, 32.0% simulation (150 runs)
- TinyLlama-1.1B: 78.7% syntax, 52.7% simulation (150 runs) - **Highest syntax validity**

**Key Achievement**: Expanded dataset validates scalability of Phase 4 pipeline, with performance remaining stable across all models despite 2.5× task increase.

---

## Summary Statistics Across All Benchmarks

| Benchmark | Tasks | Models | Repetitions | Total Runs | Key Innovation |
|-----------|-------|--------|-------------|------------|----------------|
| 1 | 5 | 2 | 1 | 10 | Baseline few-shot |
| 2 | 5 | 2 | 1 | 10 | Constrained prompts |
| 3 | 5 | 2 | 1 | 10 | Enhanced post-processing |
| 4 | 5 | 2 | 3 | 30 | Statistical analysis |
| 5 | 5 | 3 | 3 | 45 | Three-tier models |
| 6 | 5 | 3 | 3 | 45 | Sequential normalization |
| 7 | 20 | 3 | 3 | 180 | Full dataset |
| 8 | 20 | 3 | 3 | 180 | Comprehensive examples |
| 9 | 20 | 3 | 3 | 180 | Semantic-aware refinement |
| 10 | 50 | 3 | 3 | 450 | Expanded dataset validation |

**Total**: 1,160 benchmark runs across all experiments

