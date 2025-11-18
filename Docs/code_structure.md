# Code Structure Reference

This document provides a detailed reference to the codebase structure, key modules, and their relationships.

## Directory Structure

```
Quantitative/
├── Core Pipeline
│   ├── Eval_Pipeline.py          # Main evaluation pipeline classes
│   ├── model_interface.py         # AI model integration
│   └── dataset_loader.py         # Task loading and validation
│
├── Phase Runners
│   ├── run_phase1.py             # Phase 1: Few-shot prompting
│   ├── run_phase2.py             # Phase 2: Constrained prompts + post-processing
│   ├── run_phase3.py             # Phase 3: Iterative refinement (unused)
│   └── run_phase4.py             # Phase 4: Semantic-aware iterative refinement
│
├── Phase 4 Components
│   ├── phase4_config.py          # Phase 4 configuration
│   ├── iterative_evaluator.py   # Iterative refinement loop
│   ├── feedback_generator.py     # Error feedback generation
│   ├── confidence_tracker.py    # Confidence modeling
│   ├── semantic_repair.py       # Semantic repair orchestrator
│   ├── waveform_analyzer.py     # Waveform analysis
│   ├── formal_verifier.py       # Formal verification
│   └── ast_repair.py            # AST-based code repair
│
├── Analysis Tools
│   ├── statistical_analysis.py  # Statistical analysis
│   └── visualizations.py        # Plotting and visualization
│
├── Configuration
│   └── instruction.json         # Research methodology config
│
└── Dataset
    └── dataset/                 # Task specifications and references
```

## Core Modules

### `Eval_Pipeline.py`

**Purpose**: Core evaluation infrastructure

**Key Classes**:

#### `BenchmarkTask`
```python
@dataclass
class BenchmarkTask:
    task_id: str
    spec: str
    reference_hdl: str
    reference_tb: str
    category: str
    inputs: List[str]
    outputs: List[str]
```
- Represents a single HDL design task
- Contains specification and reference files

#### `EvaluationMetrics`
```python
@dataclass
class EvaluationMetrics:
    # Syntax validity
    syntax_valid: bool
    compile_errors: List[str]
    
    # Functional correctness
    simulation_passed: bool
    test_cases_passed: int
    test_cases_total: int
    
    # Timing metrics
    generation_time: float
    compile_time: float
    simulation_time: float
    
    # Phase 4 extensions
    iteration_count: int
    confidence_entropy: Optional[float]
    semantic_repair_applied: List[str]
```
- Comprehensive metrics storage
- Extensible for new evaluation criteria

#### `HDLCompiler`
```python
class HDLCompiler:
    def compile(self, hdl_file: Path, output_dir: Path) -> tuple[bool, List[str]]
```
- Compiles Verilog using Verilator or Icarus Verilog
- Returns success status and error list
- Supports timeout handling

#### `HDLSimulator`
```python
class HDLSimulator:
    def simulate(self, hdl_file: Path, tb_file: Path, output_dir: Path) -> tuple[bool, Dict]
```
- Runs testbench simulations
- Compares outputs with reference
- Extracts test case results

#### `BenchmarkPipeline`
```python
class BenchmarkPipeline:
    def evaluate_task(self, task: BenchmarkTask, model: AIModelInterface) -> EvaluationMetrics
```
- Orchestrates evaluation process
- Manages output directories
- Aggregates results

### `model_interface.py`

**Purpose**: Abstract interface for AI models

**Key Classes**:

#### `OllamaInterface`
```python
class OllamaInterface:
    def generate_hdl(self, specification: str, temperature: float = 0.0) -> Tuple[str, float]
```
- Local model inference via Ollama API
- Connection verification
- Error handling and retries

#### `HuggingFaceInterface`
```python
class HuggingFaceInterface:
    def generate_hdl(self, specification: str, temperature: float = 0.0) -> Tuple[str, float]
```
- Cloud/remote model inference
- Transformers library integration
- Token management

**Common Interface**:
Both implement the same `generate_hdl()` method signature for interchangeability.

### `dataset_loader.py`

**Purpose**: Task loading and validation

**Key Functions**:

```python
def load_tasks_from_json(json_path: str) -> List[BenchmarkTask]
```
- Loads tasks from `tasks.json`
- Validates task structure
- Returns list of `BenchmarkTask` objects

```python
def validate_dataset(tasks: List[BenchmarkTask]) -> bool
```
- Validates all tasks have required files
- Checks file existence
- Reports missing files

```python
def print_dataset_stats(tasks: List[BenchmarkTask])
```
- Prints dataset statistics
- Category breakdown
- Task count by difficulty

## Phase Runners

### `run_phase1.py`

**Purpose**: Baseline few-shot prompting

**Key Functions**:
- `extract_module_name()`: Extracts module name from task ID
- `main()`: Runs Phase 1 benchmark

**Flow**:
1. Load tasks
2. Initialize models
3. Generate with few-shot examples
4. Evaluate (no post-processing)
5. Save results

### `run_phase2.py`

**Purpose**: Constrained prompts + post-processing

**Key Functions**:
- `extract_module_name()`: Module name extraction
- `get_port_spec()`: Extracts port specifications
- `get_constrained_prompt()`: Builds constrained prompt
- `post_process_verilog()`: Comprehensive post-processing

**Post-Processing Features**:
- Module name correction
- Port specification enforcement
- SystemVerilog → Verilog conversion
- Sequential block normalization
- FSM/mixed template generation

**Flow**:
1. Load tasks
2. Build constrained prompts
3. Generate code
4. Post-process
5. Evaluate
6. Save results

### `run_phase4.py`

**Purpose**: Semantic-aware iterative refinement

**Key Components**:
- `IterativeEvaluator`: Manages refinement loop
- `SemanticRepair`: Orchestrates repair tools
- `ConfidenceTracker`: Tracks confidence metrics
- `FeedbackGenerator`: Generates error feedback

**Flow**:
1. Load tasks and configuration
2. Initialize Phase 4 components
3. For each task:
   - Generate initial code
   - Post-process
   - Iterate with refinement:
     - Compile
     - If syntax invalid → generate feedback → regenerate
     - Simulate
     - If simulation fails → semantic analysis → repair
     - Check confidence → stop if high confidence
   - Collect metrics
4. Save results with iteration history

## Phase 4 Components

### `iterative_evaluator.py`

**Purpose**: Adaptive iterative refinement

**Key Class**:

#### `IterativeEvaluator`
```python
class IterativeEvaluator:
    def evaluate_with_refinement(
        self,
        task: BenchmarkTask,
        model: AIModelInterface,
        max_iterations: int,
        enable_waveform: bool,
        enable_formal: bool
    ) -> Tuple[EvaluationMetrics, List[Dict]]
```
- Manages refinement iterations
- Implements adaptive stopping
- Coordinates with semantic repair
- Returns best metrics and iteration history

### `semantic_repair.py`

**Purpose**: Orchestrates semantic repair tools

**Key Class**:

#### `SemanticRepair`
```python
class SemanticRepair:
    def repair(self, code: str, task: BenchmarkTask, metrics: EvaluationMetrics) -> Tuple[str, List[str]]
```
- Coordinates waveform analysis, formal verification, AST repair
- Applies repairs based on confidence
- Returns repaired code and applied repairs list

### `confidence_tracker.py`

**Purpose**: Confidence modeling

**Key Class**:

#### `ConfidenceTracker`
```python
class ConfidenceTracker:
    def calculate_entropy(self, log_probs: List[float]) -> float
    def should_continue(self, entropy: float, threshold: float) -> bool
```
- Calculates entropy from log probabilities
- Supports entropy-based gating
- Enables adaptive stopping

### `feedback_generator.py`

**Purpose**: Error feedback generation

**Key Class**:

#### `FeedbackGenerator`
```python
class FeedbackGenerator:
    def generate_feedback(
        self,
        compile_errors: List[str],
        simulation_errors: List[str],
        waveform_diff: Optional[str]
    ) -> str
```
- Generates targeted feedback from errors
- Limits feedback length
- Formats for model consumption

## Analysis Tools

### `statistical_analysis.py`

**Purpose**: Statistical analysis of results

**Key Class**:

#### `BenchmarkAnalyzer`
```python
class BenchmarkAnalyzer:
    def print_summary_report(self)
    def paired_statistical_test(self, model1: str, model2: str) -> Dict
    def category_breakdown(self) -> Dict
```
- Computes mean rates and standard deviations
- Performs statistical tests (Wilcoxon, t-test)
- Category-level analysis
- Confidence intervals

### `visualizations.py`

**Purpose**: Result visualization

**Key Class**:

#### `BenchmarkVisualizer`
```python
class BenchmarkVisualizer:
    def plot_overall_comparison(self, output_path: str)
    def plot_pass_rate_by_category(self, output_path: str)
    def plot_generation_time(self, output_path: str)
```
- Generates publication-ready plots
- Multiple visualization types
- Saves to specified paths

## Configuration Files

### `instruction.json`

**Structure**:
```json
{
  "project_title": "...",
  "research_scope": {...},
  "models": [...],
  "dataset": {...},
  "prompt_templates": [...],
  "benchmark_pipeline": {...}
}
```

**Purpose**: Research methodology specification
- Model configurations
- Dataset information
- Prompt templates
- Pipeline parameters

### `phase4_config.py`

**Purpose**: Phase 4 feature flags and settings

**Key Settings**:
- `MAX_ITERATIONS`: Maximum refinement iterations
- `ADAPTIVE_STOPPING`: Enable adaptive stopping
- `ENABLE_WAVEFORM_ANALYSIS`: Waveform analysis flag
- `ENABLE_FORMAL_VERIFICATION`: Formal verification flag
- `ENABLE_AST_REPAIR`: AST repair flag
- `MODE`: "fast" or "strict"
- `ENABLE_TASK_TIERS`: Task tiering for efficiency
- `ENTROPY_THRESHOLD`: Entropy gating threshold

## Data Flow Patterns

### Standard Evaluation Flow
```
Task → Model → Generated Code → Post-Process → Compile → Simulate → Metrics
```

### Phase 4 Refinement Flow
```
Task → Model → Code → Post-Process → Compile
                                    ↓ (if fail)
                              Feedback → Model → Code → ...
                                    ↓ (if syntax OK)
                              Simulate
                                    ↓ (if fail)
                              Semantic Analysis → Repair → Re-evaluate
                                    ↓
                              Check Confidence → Stop or Continue
```

## Key Design Patterns

### 1. Strategy Pattern
- Model interfaces (Ollama vs. HuggingFace)
- Compiler selection (Verilator vs. Icarus)
- Post-processing strategies

### 2. Pipeline Pattern
- Evaluation pipeline stages
- Sequential processing with error handling

### 3. Iterator Pattern
- Task iteration
- Repetition handling
- Iterative refinement loops

### 4. Factory Pattern
- Model creation
- Task loading
- Component initialization

## Extension Points

### Adding a New Model
1. Implement `AIModelInterface` protocol
2. Provide `generate_hdl()` method
3. Add to model initialization in phase runners

### Adding a New Post-Processor
1. Extend `post_process_verilog()` function
2. Add to Phase 2 or Phase 4 pipeline
3. Update configuration if needed

### Adding a New Semantic Tool
1. Implement repair interface
2. Add to `SemanticRepair` orchestrator
3. Update `EvaluationMetrics` if needed

### Adding a New Metric
1. Extend `EvaluationMetrics` dataclass
2. Update evaluation pipeline to compute metric
3. Update analysis tools to report metric

## Error Handling

### Compilation Errors
- Parsed and returned as feedback
- Stored in `EvaluationMetrics.compile_errors`
- Used for iterative refinement

### Simulation Errors
- Captured from testbench output
- Compared with reference
- Reported in metrics

### Model API Errors
- Connection verification
- Retry logic
- Graceful degradation

### File I/O Errors
- Path validation
- Error reporting
- Safe defaults

## Performance Optimizations

### Phase 4 Fast Mode
- Task tiering (different iteration limits)
- Entropy gating (skip expensive operations)
- Generation caching (reuse successful generations)
- Timeout management (per-task limits)

### Resource Management
- Efficient file handling
- Temporary file cleanup
- Memory-conscious streaming

## Testing Considerations

### Unit Test Targets
- Individual functions (post-processing, parsing)
- Class methods (compiler, simulator)
- Configuration loading

### Integration Test Targets
- Full pipeline execution
- Model integration
- EDA tool interaction

### Validation
- Dataset validation
- Result validation
- Metric computation verification

