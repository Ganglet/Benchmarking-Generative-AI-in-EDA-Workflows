# System Architecture

## Overview

The Benchmarking Generative AI in EDA Workflows framework is designed as a modular, extensible system for evaluating AI models on hardware description language (HDL) generation tasks. The architecture follows a pipeline-based approach with clear separation of concerns.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│  (run_phase1.py, run_phase2.py, run_phase4.py,              │
│   run_phase5.py)                                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                 Evaluation Pipeline                         │
│  (Eval_Pipeline.py: BenchmarkPipeline, HDLCompiler,        │
│   HDLSimulator, EvaluationMetrics)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼──────┐ ┌─────▼──────┐ ┌────▼──────────┐
│ Model Layer  │ │ Dataset    │ │ EDA Tools     │
│              │ │ Layer      │ │ Layer         │
│ Ollama/HF    │ │ tasks.json │ │ Verilator/    │
│ Interfaces   │ │ Loader     │ │ Icarus Verilog│
└──────────────┘ └────────────┘ └───────────────┘
```

> **Note on Yosys / SynthesisTool**: A `SynthesisTool` class (wrapping Yosys) exists in `Eval_Pipeline.py` and is instantiated by `BenchmarkPipeline`. However, none of the actual phase runners (`run_phase1.py` through `run_phase5.py`) call `pipeline.evaluate_task()` — they all construct `EvaluationMetrics` manually with synthesis fields set to `None`. Yosys is therefore **never invoked** in any benchmark run. Synthesis metrics (`gate_count`, `cell_count`, `estimated_area`) are always `None` in all results.

## Component Architecture

### 1. Model Interface Layer

**Purpose**: Abstract interface for different AI model backends

**Components**:
- `OllamaInterface`: Local model inference via Ollama API
- `HuggingFaceInterface`: Cloud/remote model inference via Transformers

**Key Features**:
- Unified API for model generation
- Support for temperature, max_tokens, and other generation parameters
- Automatic connection verification
- Error handling and retry logic

**Data Flow**:
```
Specification → Model Interface → Generated HDL Code
```

### 2. Evaluation Pipeline

**Purpose**: Core evaluation logic for syntax, simulation, and synthesis

**Components**:

#### `BenchmarkPipeline`
- Orchestrates the evaluation process
- Manages output directories
- Collects and aggregates metrics
- Handles task iteration and repetition

#### `HDLCompiler`
- Compiles Verilog code using Verilator or Icarus Verilog
- Parses compilation errors
- Validates syntax correctness
- Supports timeout handling

#### `HDLSimulator`
- Runs testbench simulations
- Compares outputs with reference implementations
- Extracts test case results
- Handles simulation timeouts

#### `EvaluationMetrics`
- Data structure for all evaluation results
- Includes syntax validity, simulation results, timing metrics
- Phase 4 extensions: iteration count, confidence, semantic repair status

**Data Flow**:
```
Generated Code → Compiler → Syntax Check
                      ↓
              Simulation → Functional Check
                      ↓
              Metrics Collection → Results Storage
```

### 3. Dataset Management

**Purpose**: Task specification and reference implementation management

**Components**:
- `dataset_loader.py`: Loads and validates tasks from JSON
- `tasks.json`: Task metadata (specifications, I/O, categories)
- Reference HDL files: Verified implementations for comparison
- Testbench files: Test vectors for functional verification

**Structure**:
```
dataset/
├── tasks.json              # Task metadata
├── combinational/         # Combinational circuit tasks
├── sequential/            # Sequential circuit tasks
├── fsm/                   # Finite state machine tasks
└── mixed/                 # Mixed/complex design tasks
```

### 4. Post-Processing Layer (Phase 2+)

**Purpose**: Fix common AI generation errors

**Components**:
- Module name extraction and correction
- Port specification enforcement
- SystemVerilog → Verilog conversion
- Sequential block normalization (`begin/end` enforcement)
- FSM and mixed design template generation
- AST-based structural repair (Phase 4)

**Processing Flow**:
```
Raw AI Output → Post-Processing → Cleaned Verilog
```

### 5. Semantic Repair Layer (Phase 4)

**Purpose**: Advanced validation and repair beyond syntax

**Components**:

#### `WaveformAnalyzer`
- Compares generated vs. reference waveforms
- Identifies functional mismatches
- Provides targeted feedback

#### `FormalVerifier`
- Formal equivalence checking
- Validates logical correctness
- Catches subtle functional errors

#### `ASTRepair`
- Abstract syntax tree analysis
- Structural code repair
- Fixes common structural issues

#### `SemanticRepair`
- Orchestrates all semantic repair tools
- Coordinates repair strategies
- Applies repairs based on confidence

**Data Flow**:
```
Compiled Code → Semantic Analysis → Repair Suggestions → Refined Code
```

### 6. Iterative Refinement Layer (Phase 4)

**Purpose**: Adaptive improvement through feedback loops

**Components**:

#### `IterativeEvaluator`
- Manages refinement iterations
- Implements adaptive stopping
- Coordinates with semantic repair
- Tracks iteration history

#### `FeedbackGenerator`
- Generates error feedback from compilation/simulation
- Creates targeted prompts for refinement
- Limits feedback length for efficiency

#### `ConfidenceTracker`
- Calculates confidence metrics (entropy, log probability)
- Enables entropy-based gating
- Supports adaptive stopping decisions

**Refinement Flow**:
```
Initial Generation → Evaluation → Feedback → Regeneration → ...
                                                              ↓
                                                    Success or Max Iterations
```

### 7. Analysis and Visualization

**Purpose**: Post-experiment analysis and reporting

**Components**:
- `statistical_analysis.py`: Statistical metrics and significance testing
- `visualizations.py`: Plot generation for results
- `Research_Data/`: Detailed benchmark analysis reports

## Phase Evolution

### Phase 1: Baseline
- Simple few-shot prompting
- Basic evaluation pipeline
- No post-processing

### Phase 2: Enhanced Prompting
- Constrained prompts with exact specifications
- Comprehensive post-processing
- Sequential normalization
- FSM/mixed template generation

### Phase 3: Iterative Refinement (Not Used)
- Basic iterative refinement
- Superseded by Phase 4

### Phase 4: Semantic-Aware Iterative Refinement
- Advanced semantic repair tools
- Confidence-based adaptive stopping
- Task tiering for efficiency
- Entropy-based gating
- Generation caching

## Data Flow Example (Phase 4)

```
1. Load Task Specification
   ↓
2. Generate Initial Code (Model Interface)
   ↓
3. Post-Process (Module name, ports, normalization)
   ↓
4. Compile (HDLCompiler)
   ↓
5. If syntax invalid → Generate Feedback → Regenerate (IterativeEvaluator)
   ↓
6. Simulate (HDLSimulator)
   ↓
7. If simulation fails → Semantic Analysis (WaveformAnalyzer, FormalVerifier)
   ↓
8. Apply Semantic Repair (ASTRepair, SemanticRepair)
   ↓
9. Re-evaluate or Stop (ConfidenceTracker, Adaptive Stopping)
   ↓
10. Collect Metrics (EvaluationMetrics)
   ↓
11. Save Results
```

## Configuration Management

### Global Configuration
- `instruction.json`: Research methodology, model specifications, dataset info, and a clear record of which metrics are implemented vs. not implemented
- `phase4_config.py`: Phase 4 feature flags and optimization settings
- `phase5_config.py`: Phase 5 feature flags (used in Benchmark 12)

### Runtime Configuration
- Task-specific settings (tiers, max iterations)
- Model-specific parameters (temperature, max tokens)
- Tool-specific settings (compiler choice, timeouts)

## Scalability Features (Phase 4)

1. **Task Tiering**: Different iteration limits for trivial/simple/complex tasks
2. **Entropy Gating**: Skip expensive operations when confidence is low
3. **Generation Caching**: Reuse successful generations
4. **Timeout Management**: Per-task runtime limits
5. **Fast Mode**: Aggressive optimizations for large-scale evaluation

## Extension Points

1. **New Models**: Implement `AIModelInterface` protocol
2. **New Tasks**: Add to `tasks.json` and create reference files
3. **New Post-Processors**: Extend `post_process_verilog()` function
4. **New Semantic Tools**: Implement repair interface
5. **New Metrics**: Extend `EvaluationMetrics` dataclass

## Error Handling

- Compilation errors: Parsed and returned as feedback
- Simulation timeouts: Handled gracefully with timeout limits
- Model API failures: Retry logic and connection verification
- File I/O errors: Path validation and error reporting
- Invalid task specifications: Dataset validation on load

## Performance Considerations

- **Parallelization**: Configurable parallel evaluation (currently disabled)
- **Caching**: Generation caching for repeated tasks
- **Timeouts**: Per-operation timeouts to prevent hangs
- **Resource Management**: Efficient file handling and cleanup
- **Memory**: Streaming for large result sets

## Security Considerations

- Local model execution (Ollama) for sensitive code
- No external API keys required for core functionality
- Sandboxed execution environment (Docker support)
- Input validation for all user-provided data

