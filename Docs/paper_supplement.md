# Research Paper Supplement

This document provides additional experimental details, design rationale, and supplementary information for the research paper "Benchmarking Generative AI in EDA Workflows".

## Experimental Design

### Dataset Construction

#### Task Selection Criteria
- **Synthesizability**: All tasks must be synthesizable Verilog-2001
- **Verifiability**: Each task has a self-checking testbench
- **Diversity**: Coverage across combinational, sequential, FSM, and mixed designs
- **Difficulty Gradient**: Tasks range from simple gates to complex ALUs

#### Task Distribution
- **Combinational (23 tasks)**: Basic gates, arithmetic blocks, multiplexers, decoders
- **Sequential (14 tasks)**: Flip-flops, registers, counters, shift registers
- **FSM (8 tasks)**: Sequence detectors, controllers
- **Mixed (5 tasks)**: Priority encoders, ALUs

#### Reference Implementation Quality
- All reference HDL verified through:
  - Compilation with Verilator and Icarus Verilog
  - Simulation with comprehensive testbenches
  - Manual code review for correctness

### Model Selection Rationale

#### Three-Tier Architecture
We selected models across three size tiers to evaluate:
1. **Scaling effects**: How model size affects performance
2. **Efficiency trade-offs**: Performance vs. resource requirements
3. **Specialization impact**: Code-specialized vs. general-purpose models

#### Model Details

**Llama-3-8B-Large**:
- General-purpose instruction-tuned model
- Strong baseline for comparison
- Represents state-of-the-art open-source general models

**StarCoder2-7B-Medium**:
- Code-specialized model
- Trained on large code corpus
- Tests hypothesis that code specialization helps HDL generation

**TinyLlama-1.1B-Small**:
- Lightweight baseline
- Tests performance on resource-constrained scenarios
- Demonstrates minimum viable model size

### Evaluation Methodology

#### Repetitions and Statistical Significance
- **3 repetitions per task**: Reduces variance, enables statistical analysis
- **Standard deviations reported**: Quantifies uncertainty
- **95% confidence intervals**: Statistical significance testing

#### Metrics Selection

**Primary Metrics**:
- **Syntax Validity**: Essential for usability
- **Functional Correctness**: Core requirement for correctness
- **Generation Time**: Practical deployment consideration

**Secondary Metrics**:
- **Iteration Count**: Efficiency of refinement (Phase 4)
- **Confidence Entropy**: Calibration of model confidence
- **Category Breakdown**: Task-specific performance patterns

#### Evaluation Tools

**Compilation**:
- Verilator: Primary compiler (strict linting)
- Icarus Verilog: Secondary validation

**Simulation**:
- Icarus Verilog: Testbench execution
- Output comparison with reference implementations

**Synthesis** (Future):
- Yosys: Logic synthesis
- Gate count and area estimation

## Phase Evolution Rationale

### Phase 1: Baseline Establishment

**Purpose**: Establish baseline performance with minimal intervention

**Key Findings**:
- Models generate syntactically invalid code frequently
- Simple gates work, complex designs fail
- No clear size advantage without post-processing

**Design Decision**: Start simple to understand fundamental capabilities

### Phase 2: Constrained Prompting

**Rationale**: 
- AI models benefit from explicit constraints
- Module/port specifications reduce ambiguity
- Post-processing fixes common generation errors

**Key Innovations**:
- **Constrained Prompts**: Exact module name and port specifications
- **Post-Processing Pipeline**: Systematic error correction
- **Sequential Normalization**: Template-based sequential block repair
- **FSM/Mixed Templates**: Category-specific scaffolding

**Impact**:
- Syntax validity: 40-80% → 55-93%
- Simulation pass rate: 0-60% → 33-80%

### Phase 3: Iterative Refinement (Not Used)

**Rationale**: 
- Initial attempt at iterative improvement
- Superseded by Phase 4's more sophisticated approach

**Why Not Used**:
- Phase 4 provides better semantic understanding
- More comprehensive repair mechanisms
- Better confidence tracking

### Phase 4: Semantic-Aware Iterative Refinement

**Rationale**:
- Syntax validity ≠ functional correctness
- Need semantic validation beyond compilation
- Adaptive refinement based on confidence

**Key Innovations**:

1. **Semantic Repair Tools**:
   - Waveform analysis: Functional correctness validation
   - Formal verification: Logical equivalence checking
   - AST repair: Structural code repair

2. **Confidence Tracking**:
   - Entropy calculation from log probabilities
   - Adaptive stopping when confidence is high
   - Entropy-based gating for efficiency

3. **Task Tiering**:
   - Different iteration limits for different task complexities
   - Fast-path optimizations for simple tasks
   - Full pipeline for complex tasks

**Impact**:
- Maintains syntax validity gains
- Improves functional correctness
- Enables efficient large-scale evaluation

## Design Decisions

### Why Verilog-2001?

- **Widely Supported**: All EDA tools support Verilog-2001
- **Synthesizable Subset**: Clear synthesizable constructs
- **Industry Standard**: Most common HDL in industry
- **Tool Compatibility**: Works with open-source tools

### Why Not SystemVerilog?

- **Tool Limitations**: Not all open-source tools support SystemVerilog
- **Complexity**: More complex language, harder to validate
- **Focus**: RTL-level design, not verification features

### Post-Processing Strategy

**Decision**: Fix errors rather than prevent them

**Rationale**:
- AI models will always make some errors
- Post-processing is more reliable than perfect prompting
- Allows models to focus on logic, not syntax

**Trade-offs**:
- May mask model limitations
- Requires maintenance as models improve
- Adds processing overhead

### Iterative Refinement Approach

**Decision**: Adaptive refinement with confidence tracking

**Rationale**:
- Not all tasks need refinement
- Confidence indicates when to stop
- Efficiency matters for large-scale evaluation

**Alternative Considered**: Fixed number of iterations
- **Rejected**: Too slow, unnecessary for simple tasks

## Limitations and Future Work

### Current Limitations

1. **FSM Functional Correctness**:
   - Syntax validity achieved but simulation fails
   - State machine logic generation needs improvement
   - Complex FSMs (traffic light) remain challenging

2. **Mixed Design Logic**:
   - ALU operations work syntactically but fail functionally
   - Case statement generation correct, operation logic incorrect
   - Need better operation validation

3. **Truncation Issues**:
   - Simple gates still truncate for some models
   - Decoder shift logic remains challenging
   - May need minimum line constraints

4. **Scalability**:
   - Large-scale evaluation (120 tasks) not yet completed
   - Performance optimizations needed
   - Resource requirements for full benchmark

### Future Work Directions

1. **Dataset Expansion**:
   - Reach 120-task target
   - Add more complex designs
   - Include more FSM variants

2. **Advanced Features**:
   - Fault injection for testbench evaluation
   - Coverage analysis
   - Error taxonomy development

3. **Model Improvements**:
   - Fine-tuning on HDL corpus
   - Prompt engineering research
   - Multi-model ensemble approaches

4. **Tool Integration**:
   - Synthesis quality metrics
   - Timing analysis
   - Power estimation

## Ablation Studies

### Post-Processing Impact

**Study**: Compare with/without post-processing

**Findings**:
- Post-processing improves syntax validity by 30-50%
- Sequential normalization critical for sequential designs
- FSM templates enable syntax validity for FSMs

### Iterative Refinement Impact

**Study**: Compare single-pass vs. iterative refinement

**Findings**:
- Most tasks succeed on first attempt (avg 1.1-1.3 iterations)
- Iterative refinement helps recover from failures
- Smaller models benefit more from refinement

### Confidence Tracking Impact

**Study**: Compare with/without confidence-based stopping

**Findings**:
- Low entropy correlates with success
- Entropy gating reduces unnecessary iterations
- Adaptive stopping improves efficiency

## Statistical Analysis Details

### Variance Analysis

**Observation**: High variance (σ ≈ 0.4-0.5) in success rates

**Interpretation**:
- LLM generation is inherently stochastic
- Multiple repetitions essential for reliable results
- Single runs can be misleading

### Model Comparison

**Statistical Tests**:
- Wilcoxon signed-rank test for paired comparisons
- t-test for independent samples
- 95% confidence intervals for rates

**Key Findings**:
- TinyLlama achieves highest syntax validity (78.7%)
- Llama-3 maintains best simulation rates (61.3%)
- StarCoder2 shows unique FSM capabilities

### Category Analysis

**Patterns Observed**:
- Combinational: High success (70-85%)
- Sequential: High success (70-88%)
- FSM: Low success (0-67% syntax, 0% simulation)
- Mixed: Variable success (17-83% syntax, 0-33% simulation)

## Reproducibility

### Environment Setup

**Required Tools**:
- Python 3.10+
- Icarus Verilog
- Verilator
- Yosys (optional, for synthesis)

**Model Setup**:
- Ollama for local models
- HuggingFace Transformers for remote models

### Configuration Files

**Key Files**:
- `instruction.json`: Research methodology
- `phase4_config.py`: Phase 4 settings
- `tasks.json`: Dataset specification

### Randomness Control

**Seeds**:
- Model generation: Temperature 0.0 for reproducibility
- Task order: Fixed order in `tasks.json`
- Repetitions: Sequential (1, 2, 3)

### Result Validation

**Verification Steps**:
1. Dataset validation on load
2. Compilation verification
3. Simulation output comparison
4. Statistical consistency checks

## Ethical Considerations

### Model Usage

- All models used are open-source
- No proprietary models evaluated
- Respectful of model licenses

### Dataset

- Reference designs from open sources (OpenCores, HDLBits)
- Proper attribution in documentation
- CC BY-NC 4.0 license for dataset

### Reproducibility

- Full code and configuration provided
- Detailed methodology documentation
- Open-source tools only

## Acknowledgments

### Data Sources

- **HDLBits**: Circuit examples and testbenches
- **OpenCores**: Reference HDL designs
- **Open-source EDA tools**: Verilator, Icarus Verilog, Yosys

### Model Providers

- **Meta**: Llama-3 models
- **BigCode**: StarCoder2 models
- **TinyLlama Team**: TinyLlama models

### Tool Developers

- Open-source EDA tool developers
- Ollama team for local inference
- HuggingFace for model access

## Contact

For questions about the research methodology or experimental design, please open an issue or contact the authors.

