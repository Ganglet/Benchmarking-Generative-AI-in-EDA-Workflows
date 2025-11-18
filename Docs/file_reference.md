# File Usage Summary

This document provides a comprehensive reference of all files in the codebase, which benchmarks they were used in, and their purpose.

## Core Files (Used in All Benchmarks)

| File | Purpose | Benchmarks |
|------|---------|------------|
| `Eval_Pipeline.py` | Main evaluation pipeline (compilation, simulation, metrics) | All (1-10) |
| `model_interface.py` | AI model integration (Ollama/HuggingFace interfaces) | All (1-10) |
| `dataset_loader.py` | Task loading and validation utilities | All (1-10) |
| `instruction.json` | Configuration and methodology specifications | All (1-10) |

## Phase Runners

| File | Benchmarks Used | Purpose |
|------|----------------|---------|
| `run_phase1.py` | 1 | Phase 1: Few-shot prompting baseline |
| `run_phase2.py` | 2-8 | Phase 2: Constrained prompts + post-processing (evolved across benchmarks) |
| `run_phase3.py` | None | Phase 3: Iterative refinement (not used in final benchmarks) |
| `run_phase4.py` | 9-10 | Phase 4: Semantic-aware iterative refinement |

## Phase 4 Components (Benchmarks 9-10)

| File | Benchmarks Used | Purpose |
|------|----------------|---------|
| `phase4_config.py` | 9-10 | Phase 4 configuration and feature flags |
| `iterative_evaluator.py` | 9-10 | Adaptive iterative refinement loop |
| `feedback_generator.py` | 9-10 | Error feedback generation |
| `confidence_tracker.py` | 9-10 | Confidence modeling and entropy tracking |
| `semantic_repair.py` | 9-10 | Semantic repair orchestrator |
| `waveform_analyzer.py` | 9-10 | Waveform difference analysis |
| `formal_verifier.py` | 9-10 | Formal equivalence checking |
| `ast_repair.py` | 9-10 | AST-based code repair |

## Analysis Tools (Post-Processing)

| File | Purpose | Usage |
|------|---------|-------|
| `statistical_analysis.py` | Standalone statistical analysis tool | Post-experiment analysis |
| `visualizations.py` | Standalone visualization generation tool | Post-experiment visualization |

## Dataset Files

| File/Directory | Purpose | Benchmarks |
|---------------|---------|------------|
| `dataset/tasks.json` | Task metadata and specifications | All (1-10) |
| `dataset/combinational/` | Combinational circuit tasks | All (1-10) |
| `dataset/sequential/` | Sequential circuit tasks | All (1-10) |
| `dataset/fsm/` | Finite state machine tasks | All (1-10) |
| `dataset/mixed/` | Mixed/complex design tasks | All (1-10) |

## Configuration Files

| File | Purpose | Benchmarks |
|------|---------|------------|
| `instruction.json` | Research methodology configuration | All (1-10) |
| `phase4_config.py` | Phase 4 feature flags and settings | 9-10 |
| `requirements.txt` | Python dependencies | All (1-10) |

## Unused Files

| File | Status | Reason |
|------|--------|--------|
| `improved_prompts.py` | Unused | Early experiment, prompts integrated into phase runners |
| `run_improved_benchmark.py` | Unused | Alternative implementation, superseded by phase-specific runners |
| `run_mini_benchmark.py` | Testing only | Quick test script, not used for actual benchmark results |

## File Dependencies

### Phase 1 Dependencies
```
run_phase1.py
├── Eval_Pipeline.py
├── model_interface.py
├── dataset_loader.py
└── instruction.json
```

### Phase 2 Dependencies
```
run_phase2.py
├── Eval_Pipeline.py
├── model_interface.py
├── dataset_loader.py
└── instruction.json
```

### Phase 4 Dependencies
```
run_phase4.py
├── Eval_Pipeline.py
├── model_interface.py
├── dataset_loader.py
├── instruction.json
├── phase4_config.py
├── iterative_evaluator.py
├── feedback_generator.py
├── confidence_tracker.py
├── semantic_repair.py
│   ├── waveform_analyzer.py
│   ├── formal_verifier.py
│   └── ast_repair.py
└── run_phase2.py (for post-processing functions)
    ├── extract_module_name()
    ├── get_port_spec()
    ├── get_constrained_prompt()
    └── post_process_verilog()
```

## File Evolution

### Phase 1 → Phase 2
- **Added**: Enhanced post-processing in `run_phase2.py`
- **Added**: Constrained prompt generation
- **Added**: Module name extraction and correction

### Phase 2 → Phase 4
- **Added**: All Phase 4 components (iterative evaluator, semantic repair, etc.)
- **Added**: Configuration file (`phase4_config.py`)
- **Enhanced**: Post-processing with semantic repair integration

## Import Patterns

### Common Imports (All Phases)
```python
from Eval_Pipeline import BenchmarkPipeline, EvaluationMetrics, HDLCompiler, HDLSimulator
from model_interface import OllamaInterface, HuggingFaceInterface
from dataset_loader import load_tasks_from_json, validate_dataset
```

### Phase 2 Specific
```python
from run_phase2 import (
    extract_module_name,
    get_port_spec,
    get_constrained_prompt,
    post_process_verilog
)
```

### Phase 4 Specific
```python
from phase4_config import Phase4Config
from iterative_evaluator import IterativeEvaluator
from feedback_generator import FeedbackGenerator
from confidence_tracker import ConfidenceTracker
from semantic_repair import SemanticRepair
from waveform_analyzer import WaveformAnalyzer
from formal_verifier import FormalVerifier
from ast_repair import ASTRepair
```

## File Size and Complexity

### Large Files (>1000 lines)
- `run_phase2.py`: ~1864 lines (comprehensive post-processing)
- `Eval_Pipeline.py`: Core pipeline implementation

### Medium Files (200-1000 lines)
- `run_phase4.py`: ~508 lines
- `visualizations.py`: ~374 lines
- `statistical_analysis.py`: Analysis implementation

### Small Files (<200 lines)
- Most Phase 4 components
- Configuration files
- Utility modules

## Maintenance Notes

### Files Requiring Regular Updates
- `tasks.json`: When adding new tasks
- `instruction.json`: When changing methodology
- `phase4_config.py`: When adjusting Phase 4 settings
- `requirements.txt`: When adding dependencies

### Files That Should Not Be Modified
- `Eval_Pipeline.py`: Core infrastructure (changes affect all phases)
- `model_interface.py`: Standard interface (changes break compatibility)
- `dataset_loader.py`: Standard loading (changes break validation)

## Extension Points

### Adding New Features
1. **New Post-Processor**: Extend `post_process_verilog()` in `run_phase2.py`
2. **New Semantic Tool**: Add to `semantic_repair.py` orchestrator
3. **New Metric**: Extend `EvaluationMetrics` in `Eval_Pipeline.py`
4. **New Model**: Implement interface in `model_interface.py`

### Adding New Phase
1. Create new `run_phaseX.py` file
2. Import necessary components
3. Implement phase-specific logic
4. Update this documentation

