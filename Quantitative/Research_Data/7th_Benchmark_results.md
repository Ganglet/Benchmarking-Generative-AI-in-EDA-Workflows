# Analysis of 7th Benchmark Results - Phase 2 Full Dataset Expansion (20 Tasks × 3 Repetitions)

## Results Summary
- **Llama-3-8B-Large**: 43.3% syntax valid (σ=0.500), 28.3% simulation passed (σ=0.454) across 60 runs; average generation time 4.92 s (σ=3.59 s)
- **StarCoder2-7B-Medium**: 21.7% syntax valid (σ=0.415), 13.3% simulation passed (σ=0.343) across 60 runs; average generation time 2.76 s (σ=4.19 s)
- **TinyLlama-1.1B-Small**: 23.3% syntax valid (σ=0.427), 18.3% simulation passed (σ=0.390) across 60 runs; average generation time 5.47 s (σ=2.08 s)
- **System Status**: Phase 2 pipeline with constrained prompts, sequential normalization, and statistical analysis now exercised on the complete 20-task benchmark (combinational, sequential, FSM, mixed/complex)
- **Methodology**: Twenty tasks × 3 models × 3 repetitions → 180 total generations captured in `Benchmark_7_Results/`

## Key Insight: Dataset Expansion Exposes Category Gaps

Covering the full benchmark sharply lowers success rates: all three models continue to solve the simplest combinational and baseline sequential blocks, yet every FSM and mixed/complex design fails syntax or simulation. Sequential normalization still stabilizes DFFs and synchronous counters, but richer stateful designs (Johnson counter, shift register, T flip-flop) remain out of reach, highlighting a need for category-specific prompting and repair.

---

## Statistical Results by Model

### Llama-3-8B-Large (8 billion parameters)

**Overall Performance (60 runs across 20 tasks × 3 repetitions):**
- **Syntax Valid Rate**: 43.3% (σ=0.500)
- **Simulation Pass Rate**: 28.3% (σ=0.454)
- **Average Generation Time**: 4.92 s (σ=3.59 s)
- **Average Compile Time**: 0.152 s
- **Average Simulation Time**: 0.053 s
- **Average Tests Passed**: 1.03 / 1.15 per run

**Task-by-Task Breakdown (category aggregates):**
- **Combinational (9 tasks)**: 74.1% syntax, 40.7% simulation – AND/OR/MUX succeed consistently; XOR and arithmetic variants collapse post-processing
- **Sequential (6 tasks)**: 33.3% syntax, 33.3% simulation – Only `seq_dff_001` and `seq_counter_4bit_001` remain reliable
- **FSM (3 tasks)**: 0% syntax, 0% simulation – All state machines rejected or mis-specified
- **Mixed/Complex (2 tasks)**: 0% syntax, 0% simulation – Priority encoder and ALU both produce invalid Verilog

**Key Observations:**
- Core template adherence persists on basic gates and canonical sequential patterns.
- FSM and mixed tasks reveal limitations in the constrained prompt: outputs frequently truncate after the header or revert to fallback modules.
- Despite the broader task set, generation latency stays moderate, indicating fewer regeneration loops than the previous phase.

### StarCoder2-7B-Medium (7 billion parameters)

**Overall Performance (60 runs):**
- **Syntax Valid Rate**: 21.7% (σ=0.415)
- **Simulation Pass Rate**: 13.3% (σ=0.343)
- **Average Generation Time**: 2.76 s (σ=4.19 s)
- **Average Compile Time**: 0.110 s
- **Average Simulation Time**: 0.023 s
- **Average Tests Passed**: 0.57 / 0.67 per run

**Task-by-Task Breakdown:**
- **Combinational**: 25.9% syntax, 11.1% simulation – Only the 2-bit adder clears tests regularly; most gates terminate after the module header
- **Sequential**: 33.3% syntax, 27.8% simulation – DFF and counter succeed; all other registers fail to elaborate
- **FSM & Mixed**: 0% syntax, 0% simulation – Persistent truncation or SystemVerilog leakage

**Key Observations:**
- StarCoder2 retains competence on arithmetic templates (`comb_adder_2bit_001`) and the normalized DFF.
- Truncation remains the dominant failure mode; prompts need additional scaffolding to prevent immediate `endmodule`.
- Generation-time variance spikes when the decoder diverges, matching the frequency of zero-length bodies.

### TinyLlama-1.1B-Small (1.1 billion parameters)

**Overall Performance (60 runs):**
- **Syntax Valid Rate**: 23.3% (σ=0.427)
- **Simulation Pass Rate**: 18.3% (σ=0.390)
- **Average Generation Time**: 5.47 s (σ=2.08 s)
- **Average Compile Time**: 0.104 s
- **Average Simulation Time**: 0.024 s
- **Average Tests Passed**: 0.77 / 0.77 per run

**Task-by-Task Breakdown:**
- **Combinational**: 29.6% syntax, 22.2% simulation – AND gate is again a bright spot; arithmetic modules drift on port naming
- **Sequential**: 33.3% syntax, 27.8% simulation – DFF and counter succeed; parallel registers and Johnson counter fail
- **FSM & Mixed**: 0% syntax, 0% simulation – All attempts revert to fallback templates or emit malformed syntax

**Key Observations:**
- TinyLlama sustains quality on the simplest designs but regresses on newly introduced registers.
- Naming mistakes and missing enable logic dominate combinational failures.
- Despite higher per-run latency than StarCoder2, TinyLlama exhibits steadier decode (lower σ on generation time).

---

## Task-by-Task Detailed Analysis

### Basic Gates (`comb_and_gate_001`, `comb_or_gate_001`, `comb_not_gate_001`, `comb_xor_gate_001`)
- **Success**: Llama-3 and TinyLlama now pass AND/OR consistently; StarCoder2 still truncates.
- **Failure**: XOR and NOT regress across models due to missing assignments or fallback modules.
- **Representative Pass**:

```1:9:results/Benchmark_7_Results/Llama_3_8B_Large_comb_and_gate_001/comb_and_gate_001_rep1.v
module and_gate(
    input wire a,
    input wire b,
    output wire y
);
    assign y = a & b;
endmodule
```

### Arithmetic Blocks (`comb_half_adder_001`, `comb_full_adder_001`, `comb_adder_2bit_001`)
- **StarCoder2** keeps the 2-bit adder intact (100% sim) but drops the half/full adders.
- **Llama-3** loses reliability on full adders; post-processing removes required logic.
- **TinyLlama** struggles with carry ports; only partial success on the 2-bit adder (0.67 sim).

### Multiplexer & Decoder (`comb_mux_2to1_001`, `comb_decoder_2to4_001`)
- Llama-3 sustains perfect MUX outputs but fails the decoder due to invalid shift logic.
- TinyLlama hits occasional MUX success but stumbles on decoder enable semantics.
- StarCoder2 truncates both modules in most runs.

### Sequential Library (`seq_dff_001`, `seq_t_flipflop_001`, `seq_shift_register_4bit_001`, `seq_pipo_register_8bit_001`, `seq_johnson_counter_4bit_001`, `seq_counter_4bit_001`)
- **Common Success**: `seq_dff_001` remains a template match for every model.
- **Partial Success**: `seq_counter_4bit_001` passes for Llama-3 (100%) and partially for StarCoder2/TinyLlama.
- **Failures**: T flip-flop, shift register, PIPO register, Johnson counter all fail across models—usually due to missing always blocks or misdeclared ports.

### FSM Controllers (`fsm_sequence_detector_101_001`, `fsm_traffic_light_001`, `fsm_turnstile_controller_001`)
- Zero syntax/simulation success for all models. Outputs either remain empty after the module header or revert to placeholder combinational logic, revealing a lack of state-machine priors in the constrained prompt.

### Mixed/Complex (`mixed_priority_encoder_4to2_001`, `mixed_simple_alu_4bit_001`)
- Every run fails syntax: missing case statements, incorrect ternaries, or fallback modules that violate port requirements.

---

## Statistical Analysis: Variance and Confidence

| Metric | Llama-3-8B (σ) | StarCoder2-7B (σ) | TinyLlama-1.1B (σ) | Interpretation |
|--------|----------------|-------------------|--------------------|----------------|
| **Syntax Valid Rate** | 0.500 | 0.415 | 0.427 | High variance reflects all-or-nothing task outcomes in the expanded set |
| **Simulation Pass Rate** | 0.454 | 0.343 | 0.390 | Failure-heavy distribution compresses accuracy gains |
| **Generation Time** | 3.59 s | 4.19 s | 2.08 s | Llama-3 steadies vs. Phase 6; StarCoder2 retries when truncating |

### 95% Confidence Intervals (n = 60 per model)
- **Llama-3-8B-Large**: Syntax 43.3% ± 12.6% (≈30.7%–56.0%); Simulation 28.3% ± 11.5% (≈16.8%–39.8%)
- **StarCoder2-7B-Medium**: Syntax 21.7% ± 10.5% (≈11.2%–32.2%); Simulation 13.3% ± 8.7% (≈4.7%–22.0%)
- **TinyLlama-1.1B-Small**: Syntax 23.3% ± 10.8% (≈12.5%–34.1%); Simulation 18.3% ± 9.9% (≈8.5%–28.2%)

---

## Error Pattern Analysis

### Llama-3-8B-Large
- Falls back to placeholder modules for new combinational and mixed tasks, causing zero test coverage.
- FSM prompts trigger empty module bodies; post-processing cannot infer state transitions without structure.
- Sequential normalization still works, but only for the original Phase 6 tasks.

### StarCoder2-7B-Medium
- Truncation dominates: the decoder stops immediately after the module declaration for many tasks.
- When logic is produced, syntax usually passes, but simulation fails due to missing enable/reset semantics.
- FSM attempts introduce SystemVerilog keywords that the cleanup strips, leaving empty modules.

### TinyLlama-1.1B-Small
- Port naming mismatches (e.g., missing `en` or swapped bus widths) resurface with the larger dataset.
- Sequential designs beyond counters drop required non-blocking assignments, yielding compile errors.
- FSM and mixed tasks often emit explanatory text despite the constrained prompt, leading to cleanup-induced voids.

---

## Model Comparison: Statistical Perspective

| Metric | Llama-3-8B | StarCoder2-7B | TinyLlama-1.1B | Leading Model |
|--------|------------|---------------|----------------|---------------|
| **Syntax Valid Rate** | 43.3% | 21.7% | 23.3% | Llama-3 |
| **Simulation Pass Rate** | 28.3% | 13.3% | 18.3% | Llama-3 |
| **Average Generation Time** | 4.92 s | 2.76 s | 5.47 s | StarCoder2 (fastest) |
| **Category Coverage (any sim success)** | Comb., Seq. | Comb., Seq. | Comb., Seq. | Tie (none solve FSM/Mixed) |

---

## Progression Analysis: 6th → 7th Benchmark

### Methodology Continuity
| Aspect | 6th Benchmark | 7th Benchmark |
|--------|----------------|----------------|
| **Repetitions** | 3 per task | 3 per task |
| **Models** | Same trio | Same trio |
| **Task Count** | 5 tasks | 20 tasks |
| **Post-Processing** | Sequential normalization | Same |
| **Statistical Outputs** | Mean ± σ | Mean ± σ |

### Results Evolution

| Model | Syntax (Φ6 → Φ7) | Simulation (Φ6 → Φ7) | Commentary |
|-------|------------------|-----------------------|------------|
| **Llama-3-8B** | 93.3% → 43.3% | 73.3% → 28.3% | Full dataset exposes gaps in FSM/mixed coverage |
| **StarCoder2-7B** | 66.7% → 21.7% | 66.7% → 13.3% | Truncation resurfaces when prompts tackle larger catalog |
| **TinyLlama-1.1B** | 80.0% → 23.3% | 80.0% → 18.3% | New sequential tasks break the template-driven gains |

**Key Insight**: The expanded benchmark highlights the need for category-aware prompting and repair; Phase 6 gains were limited to the original five tasks.

---

## Remaining Challenges

### Challenge 1: FSM and Mixed Modules
- Introduce dedicated exemplars or step-by-step templates for state machines, priority encoders, and ALUs.
- Enhance post-processing to synthesize minimum viable FSM scaffolds (state enums, case statements) when missing.

### Challenge 2: Sequential Breadth
- Extend normalization to cover shift registers, Johnson counters, and PIPO registers.
- Enforce enable/reset validation during cleanup to avoid empty bodies.

### Challenge 3: Prompt Scaffolding for Combinational Variety
- Add category-specific body comments to prevent truncation (especially for StarCoder2).
- Implement port validation before accepting fallback modules.

---

## Conclusion

The seventh benchmark demonstrates that scaling the task suite from five to twenty designs uncovers significant coverage gaps. Llama-3 retains a modest edge but misses every FSM and mixed circuit; StarCoder2 and TinyLlama regress sharply once templates fall outside the original scope. Achieving >70% coverage again will require targeted prompts and repairs for the newly introduced categories, not just broader repetition.

*Date: November 10, 2025*  
*Benchmark: Phase 2 Full Dataset Expansion (20 tasks × 3 models × 3 repetitions)*  
*Models: Llama-3-8B-Large, StarCoder2-7B-Medium, TinyLlama-1.1B-Small*  
*Total Runs: 180*  
*Statistical Metrics: Mean rates with standard deviations (σ) and 95% confidence intervals*  
*Key Takeaway: Full-benchmark coverage demands category-aware prompting and post-processing beyond the sequential normalization used in Phase 6*

