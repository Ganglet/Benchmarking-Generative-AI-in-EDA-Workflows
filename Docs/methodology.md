# Methodology: Phase Evolution Details

This document details the evolution of the benchmarking methodology from Phase 1 through Phase 4, explaining the rationale behind each phase and the improvements made.

## Overview

The benchmarking framework evolved through four distinct phases, each building upon the previous phase's insights and addressing identified limitations.

## Phase 1: Baseline Few-Shot Prompting

### Methodology
- **Prompting Strategy**: Few-shot learning with example circuits
- **Post-Processing**: None
- **Evaluation**: Basic syntax and simulation checks
- **Repetitions**: Single run per task

### Key Characteristics
- Simple, straightforward approach
- Minimal intervention in AI generation
- Baseline for comparison

### Results
- Low syntax validity (40-80% depending on model)
- Very low functional correctness (0-60%)
- High variance across tasks

### Limitations Identified
1. Models generate syntactically invalid code frequently
2. Module names and port specifications often incorrect
3. No mechanism to fix common errors
4. Single runs don't capture variance

### Design Rationale
Start with the simplest possible approach to establish baseline performance and understand fundamental model capabilities before adding complexity.

---

## Phase 2: Constrained Prompting + Post-Processing

### Evolution from Phase 1

**Phase 1 → Phase 2 Changes**:
- Few-shot prompting → Constrained prompts with exact module/port specs
- No post-processing → Comprehensive post-processing
- Single runs → Statistical analysis (3 repetitions)
- 5 tasks → 20 tasks (full dataset)
- 2 models → 3 models (added StarCoder2)
- Basic fixes → Sequential normalization + FSM/mixed templates

### Methodology Components

#### 1. Constrained Prompting
- **Exact Module Names**: Specify exact module name in prompt
- **Port Specifications**: Include exact port declarations
- **Format Constraints**: Enforce Verilog-2001 syntax requirements

**Rationale**: AI models benefit from explicit constraints, reducing ambiguity and generation errors.

#### 2. Post-Processing Pipeline

**Module Name Correction**:
- Extract expected module name from task ID
- Replace incorrect module names in generated code
- Handle common naming variations

**Port Specification Enforcement**:
- Extract port specifications from task metadata
- Ensure correct port declarations
- Fix port name mismatches

**SystemVerilog → Verilog Conversion**:
- Remove SystemVerilog-specific constructs
- Convert to Verilog-2001 compatible syntax
- Handle interface and package constructs

**BSV Construct Removal**:
- Remove Bluespec-specific syntax
- Convert to standard Verilog

**Port Name Normalization**:
- Standardize port naming conventions
- Fix case sensitivity issues

#### 3. Sequential Normalization (Benchmark 6+)

**Enforced `begin/end` Structure**:
- Ensure all sequential blocks have proper `begin/end`
- Fix missing block delimiters
- Template-based repair for common patterns

**Sequential Template Matching**:
- Match common sequential patterns
- Apply template-based fixes
- Improve DFF and counter reliability

**Rationale**: Sequential designs require specific structural patterns that models often miss.

#### 4. FSM/Mixed Template Generation (Benchmark 8+)

**Category-Specific Scaffolding**:
- Generate templates for FSM designs
- Provide scaffolding for mixed designs
- Prevent truncation with minimum structure

**Template-Based Repair**:
- Match FSM patterns and apply fixes
- Handle state machine structure
- Fix case statement issues

**Rationale**: Complex designs (FSM, mixed) need structural guidance that simple post-processing can't provide.

### Results
- Syntax validity: 55-93% (up from 40-80%)
- Simulation pass rate: 33-80% (up from 0-60%)
- FSM breakthrough: StarCoder2 achieves 66.7% syntax validity (from 0%)

### Key Achievements
- **FSM Breakthrough**: StarCoder2 achieves 66.7% syntax validity for FSM tasks
- **Mixed Design Success**: StarCoder2 achieves 66.7% functional correctness on priority encoder
- **Sequential Expansion**: All models handle expanded sequential library
- **Overall Improvement**: 70% syntax validity (Llama-3), 55% (StarCoder2), 65% (TinyLlama)

### Limitations Identified
1. Syntax validity ≠ functional correctness
2. Post-processing fixes structure but not logic
3. No mechanism for iterative improvement
4. No confidence tracking

---

## Phase 3: Iterative Refinement (Not Used)

### Methodology
- Basic iterative refinement with error feedback
- Fixed number of refinement attempts
- Simple error-based feedback

### Why Not Used
- Superseded by Phase 4's more sophisticated approach
- Phase 4 provides better semantic understanding
- More comprehensive repair mechanisms
- Better confidence tracking

### Design Decision
Skip Phase 3 in favor of more advanced Phase 4 approach that addresses the same goals with better techniques.

---

## Phase 4: Semantic-Aware Iterative Refinement

### Evolution from Phase 2

**Phase 2 → Phase 4 Changes**:
- Single-pass generation → Iterative refinement with feedback
- Syntax-only validation → Semantic validation (waveform, formal verification)
- Static post-processing → Adaptive AST-based repair
- No confidence tracking → Confidence modeling with entropy
- Fixed methodology → Adaptive stopping based on confidence

### Methodology Components

#### 1. Iterative Refinement Loop

**Adaptive Iteration**:
- Start with initial generation
- Evaluate syntax and simulation
- Generate feedback from errors
- Regenerate with feedback
- Repeat until success or max iterations

**Adaptive Stopping**:
- Stop early if confidence is high
- Continue if improvement is likely
- Based on entropy and improvement metrics

**Rationale**: Not all tasks need refinement, and confidence indicates when to stop.

#### 2. Semantic Repair Tools

**Waveform Analysis**:
- Compare generated vs. reference waveforms
- Identify functional mismatches
- Provide targeted feedback

**Formal Verification**:
- Formal equivalence checking
- Validate logical correctness
- Catch subtle functional errors

**AST Repair**:
- Abstract syntax tree analysis
- Structural code repair
- Fix common structural issues

**Rationale**: Syntax validity doesn't guarantee functional correctness. Semantic validation is needed.

#### 3. Confidence Tracking

**Entropy Calculation**:
- Calculate entropy from log probabilities
- Low entropy = high confidence
- High entropy = low confidence

**Entropy-Based Gating**:
- Skip expensive operations when confidence is low
- Focus resources on promising attempts
- Improve efficiency

**Adaptive Stopping**:
- Stop when confidence is high
- Continue when uncertainty exists
- Balance efficiency and correctness

**Rationale**: Confidence metrics enable intelligent resource allocation and early stopping.

#### 4. Task Tiering (Benchmark 10)

**Tier Classification**:
- Tier 0 (trivial): Basic gates, simple mux
- Tier 1 (simple): Adders, basic sequential
- Tier 2 (complex): FSM, mixed, advanced sequential

**Tier-Specific Limits**:
- Different max iterations per tier
- Fast-path for simple tasks
- Full pipeline for complex tasks

**Rationale**: Different tasks need different levels of refinement. Tiering improves efficiency.

### Results

**Benchmark 9 (20 tasks)**:
- Llama-3-8B: 71.7% syntax, 61.7% simulation
- StarCoder2-7B: 56.7% syntax, 33.3% simulation
- TinyLlama-1.1B: 75.0% syntax, 51.7% simulation

**Benchmark 10 (50 tasks)**:
- Llama-3-8B: 71.3% syntax, 61.3% simulation (stable with 2.5× expansion)
- StarCoder2-7B: 58.7% syntax, 32.0% simulation
- TinyLlama-1.1B: 78.7% syntax, 52.7% simulation (highest syntax validity)

### Key Achievements
- **Scalability Validation**: Performance stable with 2.5× dataset expansion
- **TinyLlama Breakthrough**: Achieves highest syntax validity (78.7%)
- **Efficient Refinement**: Most tasks succeed on first attempt (avg 1.1-1.3 iterations)
- **Confidence Calibration**: Low entropy correlates with success

### Current Limitations
1. FSM functional correctness still challenging (0% simulation despite syntax validity)
2. Mixed design logic correctness needs improvement
3. Some truncation issues persist
4. Johnson counter logic correctness issue

---

## Methodology Comparison

| Aspect | Phase 1 | Phase 2 | Phase 4 |
|--------|---------|---------|---------|
| **Prompting** | Few-shot | Constrained | Constrained |
| **Post-Processing** | None | Comprehensive | Comprehensive + Semantic |
| **Validation** | Syntax only | Syntax + Simulation | Syntax + Simulation + Semantic |
| **Refinement** | None | None | Iterative with feedback |
| **Confidence** | None | None | Entropy tracking |
| **Efficiency** | Fast | Medium | Optimized (tiering, gating) |
| **Syntax Validity** | 40-80% | 55-93% | 57-79% |
| **Simulation Pass** | 0-60% | 33-80% | 32-61% |

## Design Principles

### 1. Incremental Improvement
Each phase builds upon previous insights, addressing identified limitations systematically.

### 2. Reproducibility
- Fixed seeds and configurations
- Comprehensive documentation
- Open-source tools only

### 3. Statistical Rigor
- Multiple repetitions (3 per task)
- Standard deviations reported
- Confidence intervals calculated

### 4. Efficiency
- Task tiering for different complexities
- Entropy-based gating
- Adaptive stopping

### 5. Extensibility
- Modular design
- Clear extension points
- Well-documented interfaces

## Future Methodology Directions

### Potential Phase 5 Features
1. **Fault Injection**: Testbench evaluation with fault injection
2. **Prompt Variations**: Systematic prompt template testing
3. **Coverage Analysis**: Test coverage metrics
4. **Error Taxonomy**: Comprehensive error classification
5. **FSM Refinement**: Specialized FSM logic generation improvements

### Research Questions
1. Can fine-tuning on HDL corpus improve performance?
2. What prompt engineering techniques are most effective?
3. How do ensemble methods perform?
4. Can synthesis quality metrics guide generation?

## Conclusion

The methodology evolution demonstrates:
- **Systematic Improvement**: Each phase addresses specific limitations
- **Scalability**: Phase 4 validates approach with expanded dataset
- **Efficiency**: Optimizations enable large-scale evaluation
- **Reproducibility**: Clear methodology enables replication

The framework continues to evolve based on experimental insights and research needs.

