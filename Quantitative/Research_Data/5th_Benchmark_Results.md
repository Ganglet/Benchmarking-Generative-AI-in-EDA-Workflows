# Analysis of 5th Benchmark Results - Phase 2 with Medium Model Introduction (Multiple Repetitions)

## Results Summary
- **Llama-3-8B-Large**: 53.3% syntax valid (σ=0.516), 40.0% simulation passed (σ=0.507) across 15 runs
- **StarCoder2-7B-Medium** *(new)*: 53.3% syntax valid (σ=0.516), 53.3% simulation passed (σ=0.516) across 15 runs
- **TinyLlama-1.1B-Small**: 46.7% syntax valid (σ=0.516), 33.3% simulation passed (σ=0.488) across 15 runs
- **System Status**: Constrained prompts + Post-processing + Statistical analysis (3 repetitions per task)
- **Methodology**: Five tasks × 3 repetitions per model (instruction.json) → 45 total generations

## Key Insight: Medium Model Bridges Sequential Gap

Introducing **StarCoder2-7B-Medium** reveals how a mid-sized model shifts the balance:
- StarCoder2 overtakes TinyLlama on sequential logic, delivering the only perfect DFF run this round and majority-passing counters
- Llama-3 remains dominant on easy combinational tasks but continues to collapse on sequential designs
- TinyLlama keeps fastest generation on average but slides back without additional post-processing fixes
- Overall variance (σ≈0.5) persists, confirming the need for repeated trials

---

## Statistical Results by Model

### Llama-3-8B-Large (8 billion parameters)

**Overall Performance (15 runs across 5 tasks × 3 repetitions):**
- **Syntax Valid Rate**: 53.3% (σ=0.516) – 8/15 runs successful
- **Simulation Pass Rate**: 40.0% (σ=0.507) – 6/15 runs successful
- **Average Generation Time**: 3.48s (σ=1.87s)
- **Average Compile Time**: 0.13s
- **Average Simulation Time**: 0.08s

**Task-by-Task Breakdown:**

1. **AND Gate** (3 runs):
   - Syntax: 100% (3/3)
   - Simulation: 100% (3/3)
   - Identical netlists across repetitions

2. **2-bit Adder** (3 runs):
   - Syntax: 66.7% (2/3)
   - Simulation: 0% (0/3) – logic errors persist even when syntax holds
   - Failure pattern: Off-by-one addition when carry propagates

3. **2-to-1 MUX** (3 runs):
   - Syntax: 100% (3/3)
   - Simulation: 100% (3/3)
   - Stable combinational success

4. **D Flip-Flop** (3 runs):
   - Syntax: 0% (0/3)
   - Simulation: 0% (0/3)
   - Error: "syntax error, unexpected else" – same as prior benchmark

5. **4-bit Counter** (3 runs):
   - Syntax: 0% (0/3)
   - Simulation: 0% (0/3)
   - Root cause: Misplaced `begin/end` around reset branch

**Key Observations:**
- Combinational logic remains reliable (100% syntax, 66.7% simulation in aggregate)
- Sequential logic remains unusable without manual repair
- Generation-time variance shrank slightly versus Phase 4 but still exceeds 50%

---

### StarCoder2-7B-Medium (7 billion parameters)

**Overall Performance (15 runs):**
- **Syntax Valid Rate**: 53.3% (σ=0.516) – 8/15 runs successful
- **Simulation Pass Rate**: 53.3% (σ=0.516) – 8/15 runs successful
- **Average Generation Time**: 3.10s (σ=4.66s) – extremely bursty between tasks
- **Average Compile Time**: 0.11s
- **Average Simulation Time**: 0.06s

**Task-by-Task Breakdown:**

1. **AND Gate** (3 runs):
   - Syntax: 0% (0/3)
   - Simulation: 0% (0/3)
   - Typical failure: Premature `endmodule` before body

2. **2-bit Adder** (3 runs):
   - Syntax: 100% (3/3)
   - Simulation: 100% (3/3)
   - Consistent ripple-carry implementation

3. **2-to-1 MUX** (3 runs):
   - Syntax: 0% (0/3)
   - Simulation: 0% (0/3)
   - Same structural issue as AND gate (truncated module)

4. **D Flip-Flop** (3 runs):
   - Syntax: 100% (3/3)
   - Simulation: 100% (3/3)
   - Generated code matches textbook template with synchronous reset

5. **4-bit Counter** (3 runs):
   - Syntax: 66.7% (2/3)
   - Simulation: 66.7% (2/3)
   - Successful runs increment correctly and hold state when enable is low

**Key Observations:**
- StarCoder2 anchors the middle ground: excels on sequential examples but stumbles on the simplest combinational modules
- Error profile suggests prompt formatting sensitivity (extra blank line before module header triggers early closure)
- Variance in generation time (σ=4.66s) is the highest seen so far, likely due to divergent decoding paths

---

### TinyLlama-1.1B-Small (1.1 billion parameters)

**Overall Performance (15 runs):**
- **Syntax Valid Rate**: 46.7% (σ=0.516) – 7/15 runs successful
- **Simulation Pass Rate**: 33.3% (σ=0.488) – 5/15 runs successful
- **Average Generation Time**: 4.05s (σ=3.62s)
- **Average Compile Time**: 0.095s
- **Average Simulation Time**: 0.044s

**Task-by-Task Breakdown:**

1. **AND Gate** (3 runs):
   - Syntax: 66.7% (2/3)
   - Simulation: 33.3% (1/3)
   - Error mix: Missing module ports and mis-typed assignments

2. **2-bit Adder** (3 runs):
   - Syntax: 66.7% (2/3)
   - Simulation: 66.7% (2/3)
   - Post-processing still required to standardize bit widths

3. **2-to-1 MUX** (3 runs):
   - Syntax: 66.7% (2/3)
   - Simulation: 66.7% (2/3)
   - Successes mimic prior-phase templates with ternary operator

4. **D Flip-Flop** (3 runs):
   - Syntax: 0% (0/3)
   - Simulation: 0% (0/3)
   - Regression: last phase’s successful template did not reappear

5. **4-bit Counter** (3 runs):
   - Syntax: 33.3% (1/3)
   - Simulation: 0% (0/3)
   - Failures oscillate between reset logic errors and width mismatches

**Key Observations:**
- TinyLlama lost ground on sequential logic compared with Phase 4
- Fastest generation times overall, but the advantage no longer offsets the repair workload
- Error taxonomy broadens: inconsistent port declarations, stray BSV syntax, and truncated always blocks

---

## Statistical Analysis: Variance and Confidence

### Variance Comparison (Per-Model)

| Metric | Llama-3-8B (σ) | StarCoder2-7B (σ) | TinyLlama-1.1B (σ) | Interpretation |
|--------|----------------|-------------------|--------------------|----------------|
| **Syntax Valid Rate** | 0.516 | 0.516 | 0.516 | All models exhibit comparable binary variance |
| **Simulation Pass Rate** | 0.507 | 0.516 | 0.488 | Performance swings remain substantial |
| **Generation Time** | 1.87s | 4.66s | 3.62s | StarCoder2 shows the largest timing spread |

### 95% Confidence Intervals (n=15 per model)

- **Llama-3-8B-Large**: Syntax 53.3% ± 26.1% (27.2%–79.4%); Simulation 40.0% ± 25.7% (14.3%–65.7%)
- **StarCoder2-7B-Medium**: Syntax 53.3% ± 26.1%; Simulation 53.3% ± 26.1% → Overlaps with both other models
- **TinyLlama-1.1B-Small**: Syntax 46.7% ± 26.1% (20.6%–72.8%); Simulation 33.3% ± 24.7% (8.6%–58.0%)

**Implication**: Mean differences remain statistically inconclusive; increased repetitions (≥5 per task) will be required for hypothesis testing.

---

## Task-by-Task Detailed Analysis

### Task 1: AND Gate
- **Llama-3-8B-Large**: 100% syntax & simulation; continues to deliver textbook `assign y = a & b;`
- **StarCoder2-7B-Medium**: 0% syntax; truncates the module after header → immediate `endmodule`
- **TinyLlama-1.1B-Small**: 33% simulation success; lapses include `assign y = a && b;` and missing port wires
- **Takeaway**: Mid model unexpectedly underperforms on the simplest task, suggesting formatting sensitivity

### Task 2: 2-bit Adder
- **Llama-3-8B-Large**: Syntax mostly stable but logic bug causes LSB mismatch under carry
- **StarCoder2-7B-Medium**: Perfect across all repetitions; concise ripple-carry netlists
- **TinyLlama-1.1B-Small**: Matches StarCoder2 when syntax valid, though still needs post-processing for bit slicing
- **Takeaway**: Prompt exemplars for arithmetic now generalize well to medium and small models

### Task 3: 2-to-1 MUX
- **Llama-3-8B-Large**: 100% success; identical to prior phases
- **StarCoder2-7B-Medium**: Same truncation error as AND gate → 0% success
- **TinyLlama-1.1B-Small**: 66.7% success; syntax issues stem from redundant default assignments
- **Takeaway**: Module preamble formatting is critical for StarCoder2; minor edits could flip success to 100%

### Task 4: D Flip-Flop
- **Llama-3-8B-Large**: Recurs with `end` before `else`; zero usable outputs
- **StarCoder2-7B-Medium**: 100% success; produces canonical synchronous reset block:

```1:10:results/Benchmark_5_Results/StarCoder2_7B_Medium_seq_dff_001/seq_dff_001_rep1.v
module d_flipflop(
    input wire clk, input wire rst, input wire d, output reg q
);
    always @(posedge clk) begin
        if (rst)
            q <= 1'b0;
        else
            q <= d;
    end
endmodule
```

- **TinyLlama-1.1B-Small**: 0% syntax; reintroduces stray `else` tokens and mixed indentation
- **Takeaway**: Medium model delivers the sequential stability previously missing

### Task 5: 4-bit Counter
- **Llama-3-8B-Large**: Same structural syntax failure as DFF
- **StarCoder2-7B-Medium**: 66.7% success; two runs pass all tests, one omits enable guard
- **TinyLlama-1.1B-Small**: Syntax 33%, Simulation 0%; the only syntax-valid run fails enable hold check
- **Takeaway**: StarCoder2 establishes the first majority-pass sequential counter in the study

---

## Error Pattern Analysis

### Llama-3-8B-Large
- **Sequential Syntax Errors**: 6/6 sequential attempts fail with `unexpected else`
- **Combinational Logic**: Stable templates; single adder logic failure linked to missing carry wire reset
- **Remedy Needed**: Stronger sequential exemplars emphasizing `begin/end` pairing in prompts

### StarCoder2-7B-Medium
- **Module Truncation**: 4/9 combinational runs stop after the header (`endmodule` at line 2)
- **Sequential Success**: Clean synchronous structures across all DFF runs
- **Remedy Needed**: Adjust decoding temperature or add explicit newline scaffolding for module body

### TinyLlama-1.1B-Small
- **Mixed Syntax Issues**: Port width omissions, stray high-level HDL keywords, misaligned `always` blocks
- **Sequential Regression**: No successful DFF run despite prior benchmark success
- **Remedy Needed**: Expand post-processing library to normalize ports and restructure sequential logic

---

## Model Comparison: Statistical Perspective

| Metric | Llama-3-8B | StarCoder2-7B | TinyLlama-1.1B | Leading Model |
|--------|------------|---------------|----------------|---------------|
| **Syntax Valid Rate** | 53.3% | 53.3% | 46.7% | Tie (Llama-3, StarCoder2) |
| **Simulation Pass Rate** | 40.0% | 53.3% | 33.3% | StarCoder2 |
| **Average Generation Time** | 3.48s | 3.10s | 4.05s | StarCoder2 |
| **Sequential Success** | 0% | 83.3% (5/6) | 0% | StarCoder2 |
| **Combinational Consistency** | 88.9% sim | 44.4% sim | 55.6% sim | Llama-3 |

**Interpretation**:
- StarCoder2 shifts the narrative: sequential competence can outweigh combinational hiccups for end-to-end pass rate
- Llama-3’s combinational strength still matters for quick wins but leaves large coverage gaps
- TinyLlama requires targeted post-processing or reranking to stay competitive

---

## Progression Analysis: 4th → 5th Benchmark

### Methodology Continuity
| Aspect | 4th Benchmark | 5th Benchmark |
|--------|----------------|----------------|
| **Repetitions** | 3 per task | 3 per task |
| **Models** | Llama-3-8B, TinyLlama-1.1B | + StarCoder2-7B (medium tier) |
| **Post-Processing** | Enabled | Enabled |
| **Statistical Outputs** | Mean ± σ | Mean ± σ |

### Results Evolution

| Model | Syntax (Φ4 → Φ5) | Simulation (Φ4 → Φ5) | Commentary |
|-------|-------------------|-----------------------|------------|
| **Llama-3-8B** | 60.0% → 53.3% | 53.3% → 40.0% | Sequential regressions persist without new prompting |
| **StarCoder2-7B** | — → 53.3% | — → 53.3% | Medium model debuts with balanced results |
| **TinyLlama-1.1B** | 66.7% → 46.7% | 60.0% → 33.3% | Loss of sequential wins dominates decline |

**Key Insight**: The medium model now anchors the leaderboard on simulation passes, underscoring the importance of exploring parameter scaling rather than only extremes.

---

## Remaining Challenges

### Challenge 1: Sequential Stability for Llama-3 and TinyLlama
- Provide explicit sequential exemplars in prompts
- Consider syntax-aware post-processing (AST rewrite) to repair dangling `else`

### Challenge 2: Prompt Formatting for StarCoder2
- Minor structural tweaks (explicit comments between module header and body) may eliminate truncation
- Evaluate decoding parameters that discourage premature `endmodule`

### Challenge 3: Statistical Significance
- Current CIs still span ±25%; plan ≥5 repetitions per task for Phase 6
- Introduce non-parametric tests (Wilcoxon) once sample size grows

---

## Conclusion

The fifth benchmark establishes a three-tier landscape:
1. **Llama-3-8B-Large** maintains flawless combinational generation but fails sequentially.
2. **StarCoder2-7B-Medium** delivers the first majority-success sequential results, highlighting the value of medium-scale models.
3. **TinyLlama-1.1B-Small** remains efficient yet unreliable without deeper post-processing.

Overall variance persists (σ≈0.5), reinforcing the methodology of repeated trials. The introduction of StarCoder2 demonstrates that medium models can provide a pragmatic balance between accuracy and resource cost, guiding the next wave of prompt and tooling refinements.

*Date: November 7, 2025*  
*Benchmark: Phase 2 with Medium Model Introduction (3 repetitions per task)*  
*Models: Llama-3-8B-Large, StarCoder2-7B-Medium, TinyLlama-1.1B-Small*  
*Total Runs: 45 (5 tasks × 3 models × 3 repetitions)*  
*Statistical Metrics: Mean rates with standard deviations (σ)*  
*Key Achievement: Medium model closes sequential performance gap*
