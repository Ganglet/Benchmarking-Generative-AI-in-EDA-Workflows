# Dataset Description

This document describes the benchmark dataset used for evaluating generative AI models on HDL generation tasks.

## Overview

The dataset consists of standardized digital circuit specifications with corresponding verified HDL implementations and testbenches. Each task includes a natural language specification, reference Verilog module, and self-checking testbench.

## Current Dataset Status

### Total Tasks: 50

**Distribution**:
- **Combinational**: 23 tasks (46%)
- **Sequential**: 14 tasks (28%)
- **FSM**: 8 tasks (16%)
- **Mixed/Complex**: 5 tasks (10%)

### Target Dataset: 120 Tasks

**Planned Distribution**:
- **Combinational**: 40 tasks (33%)
- **Sequential**: 40 tasks (33%)
- **FSM**: 20 tasks (17%)
- **Mixed/Complex**: 20 tasks (17%)

## Task Categories

### Combinational Circuits (23 tasks)

**Basic Gates**:
- AND gate (`comb_and_gate_001-003`)
- OR gate (`comb_or_gate_001-003`)
- NOT gate (`comb_not_gate_001-002`)
- XOR gate (`comb_xor_gate_001-002`)

**Arithmetic Blocks**:
- Half adder (`comb_half_adder_001-002`)
- Full adder (`comb_full_adder_001-002`)
- 2-bit adder (`comb_adder_2bit_001-003`)

**Multiplexers & Decoders**:
- 2-to-1 multiplexer (`comb_mux_2to1_001-003`)
- 2-to-4 decoder (`comb_decoder_2to4_001-003`)

**Characteristics**:
- Synthesizable combinational logic
- No clock or state elements
- Output depends only on current inputs
- Typically easier for AI models

### Sequential Circuits (14 tasks)

**Flip-Flops**:
- D flip-flop (`seq_dff_001-003`)
- T flip-flop (`seq_t_flipflop_001-002`)

**Registers**:
- 4-bit shift register (`seq_shift_register_4bit_001-002`)
- 8-bit PIPO register (`seq_pipo_register_8bit_001-002`)

**Counters**:
- 4-bit counter (`seq_counter_4bit_001-003`)
- 4-bit Johnson counter (`seq_johnson_counter_4bit_001-002`)

**Characteristics**:
- Clock-driven designs
- State elements (flip-flops)
- Synchronous reset and enable signals
- Require proper `begin/end` structure

### Finite State Machines (8 tasks)

**Sequence Detectors**:
- 101 sequence detector (`fsm_sequence_detector_101_001-003`)

**Controllers**:
- Traffic light controller (`fsm_traffic_light_001-002`)
- Turnstile controller (`fsm_turnstile_controller_001-003`)

**Characteristics**:
- State-based designs
- State transitions based on inputs
- Output depends on current state
- Most challenging category for AI models

### Mixed/Complex Designs (5 tasks)

**Encoders**:
- 4-to-2 priority encoder (`mixed_priority_encoder_4to2_001-003`)

**ALUs**:
- 4-bit ALU (`mixed_simple_alu_4bit_001-002`)

**Characteristics**:
- Combine combinational and sequential logic
- Complex control logic
- Multiple operations or modes
- Case statements and priority logic

## Task Structure

### Task Metadata Format

Each task in `tasks.json` follows this structure:

```json
{
  "task_id": "category_task_name_001",
  "category": "combinational|sequential|fsm|mixed",
  "difficulty": "easy|medium|hard",
  "specification": "Natural language specification text",
  "reference_hdl": "path/to/reference.v",
  "reference_tb": "path/to/testbench.v",
  "inputs": ["input1", "input2"],
  "outputs": ["output1", "output2"]
}
```

### Field Descriptions

- **`task_id`**: Unique identifier following pattern `category_task_name_number`
- **`category`**: Task category (combinational, sequential, fsm, mixed)
- **`difficulty`**: Difficulty level (easy, medium, hard)
- **`specification`**: Natural language description of the design
- **`reference_hdl`**: Path to reference Verilog module
- **`reference_tb`**: Path to reference testbench
- **`inputs`**: List of input port names
- **`outputs`**: List of output port names

### File Organization

```
dataset/
├── tasks.json                    # Task metadata
├── combinational/
│   ├── and_gate/
│   │   ├── reference.v
│   │   └── testbench.v
│   ├── or_gate/
│   │   ├── reference.v
│   │   └── testbench.v
│   └── ...
├── sequential/
│   ├── d_flipflop/
│   │   ├── reference.v
│   │   └── testbench.v
│   └── ...
├── fsm/
│   ├── sequence_detector_101/
│   │   ├── reference.v
│   │   └── testbench.v
│   └── ...
└── mixed/
    ├── priority_encoder_4to2/
    │   ├── reference.v
    │   └── testbench.v
    └── ...
```

## Reference Implementation Requirements

### Verilog Module Requirements

1. **Synthesizable Verilog-2001**: Must compile with Verilator and Icarus Verilog
2. **Correct Interface**: Must match specification inputs/outputs exactly
3. **Functional Correctness**: Must implement specification correctly
4. **Clean Code**: Well-formatted, readable code

### Testbench Requirements

1. **Self-Checking**: Must use `$display` for pass/fail reporting
2. **Comprehensive**: Must test all relevant input combinations
3. **Clear Output**: Must clearly indicate pass/fail for each test case
4. **Termination**: Must call `$finish` when complete

### Example Testbench Format

```verilog
module testbench;
    // Declarations
    reg input1, input2;
    wire output1;
    
    // Instantiate DUT
    module_name dut(.input1(input1), .input2(input2), .output1(output1));
    
    initial begin
        // Test case 1
        input1 = 0; input2 = 0; #10;
        if (output1 !== expected_value) 
            $display("FAIL: Test case 1");
        else 
            $display("PASS: Test case 1");
        
        // Test case 2
        input1 = 1; input2 = 1; #10;
        if (output1 !== expected_value) 
            $display("FAIL: Test case 2");
        else 
            $display("PASS: Test case 2");
        
        $finish;
    end
endmodule
```

## Data Sources

### Primary Sources

1. **HDLBits**: Circuit examples and testbenches
   - Educational HDL practice platform
   - Well-tested examples
   - Clear specifications

2. **OpenCores**: Reference HDL designs
   - Open-source hardware designs
   - Industry-standard implementations
   - Verified designs

3. **Custom Generated**: Original specifications
   - Created for specific research needs
   - Fills gaps in available examples
   - Ensures category balance

### Attribution

All reference designs are properly attributed:
- HDLBits examples: Educational use
- OpenCores designs: Respect original licenses
- Custom designs: Created for this research

## Dataset Validation

### Validation Process

1. **Syntax Validation**: All reference files compile without errors
2. **Simulation Validation**: All testbenches pass with reference implementations
3. **Metadata Validation**: All tasks have complete metadata
4. **File Existence**: All referenced files exist

### Validation Command

```bash
cd Quantitative
python dataset_loader.py
```

This will:
- Load all tasks from `tasks.json`
- Validate file existence
- Check metadata completeness
- Report any issues

## Difficulty Levels

### Easy
- Simple logic (basic gates, DFF)
- Few inputs/outputs
- Straightforward specifications
- Well-known patterns

**Examples**: AND gate, D flip-flop, 2-to-1 mux

### Medium
- Moderate complexity (adders, counters)
- Multiple inputs/outputs
- Some design decisions required
- Common patterns

**Examples**: Full adder, 4-bit counter, sequence detector

### Hard
- Complex designs (ALUs, complex FSMs)
- Many inputs/outputs
- Multiple design decisions
- Less common patterns

**Examples**: 4-bit ALU, traffic light controller

## Task Naming Convention

### Pattern
```
{category}_{task_name}_{number}
```

### Examples
- `comb_and_gate_001`: Combinational AND gate, first variant
- `seq_counter_4bit_001`: Sequential 4-bit counter, first variant
- `fsm_sequence_detector_101_001`: FSM sequence detector for pattern 101, first variant
- `mixed_priority_encoder_4to2_001`: Mixed 4-to-2 priority encoder, first variant

### Variants
- `_001`, `_002`, `_003`: Different specifications for same design
- Allows testing specification variation sensitivity
- Same reference implementation, different natural language descriptions

## Dataset Expansion Plan

### Phase 1: Current (50 tasks) ✅
- 23 combinational
- 14 sequential
- 8 FSM
- 5 mixed

### Phase 2: Target 60 tasks
- Add 10 more tasks
- Focus on FSM and mixed variants
- Maintain category balance

### Phase 3: Target 80 tasks
- Add 20 more tasks
- Expand combinational and sequential
- Add more FSM variants

### Phase 4: Target 120 tasks
- Add 40 more tasks
- Reach target distribution (40/40/20/20)
- Comprehensive coverage

## Quality Assurance

### Reference Implementation Quality

All reference implementations are:
- ✅ Synthesizable (Verilator validation)
- ✅ Functionally correct (testbench validation)
- ✅ Well-documented (clear code structure)
- ✅ Standard compliant (Verilog-2001)

### Testbench Quality

All testbenches are:
- ✅ Self-checking (automatic pass/fail)
- ✅ Comprehensive (relevant test cases)
- ✅ Clear output (readable results)
- ✅ Properly terminated (`$finish`)

### Specification Quality

All specifications are:
- ✅ Clear and unambiguous
- ✅ Complete (all I/O specified)
- ✅ Natural language
- ✅ Consistent format

## Usage Guidelines

### For Benchmarking
- Use all tasks for comprehensive evaluation
- Maintain task order for reproducibility
- Use 3 repetitions per task for statistical significance

### For Development
- Start with easy tasks for testing
- Use medium tasks for validation
- Test with hard tasks before full benchmark

### For Research
- Analyze by category for insights
- Compare difficulty levels
- Study specification variation effects

## License

The dataset files (reference Verilog, testbenches, and `tasks.json`) are released under the **Creative Commons Attribution–NonCommercial 4.0 License (CC BY-NC 4.0)**.

See [DATASET_LICENSE](../DATASET_LICENSE) for details.

## Contributing New Tasks

See [docs/extending.md](extending.md) for detailed instructions on adding new tasks to the dataset.

### Quick Checklist
- [ ] Create reference Verilog module
- [ ] Create self-checking testbench
- [ ] Validate compilation and simulation
- [ ] Add entry to `tasks.json`
- [ ] Run dataset validation
- [ ] Test with mini benchmark

## Statistics

### Current Distribution
- **Total Tasks**: 50
- **Combinational**: 23 (46%)
- **Sequential**: 14 (28%)
- **FSM**: 8 (16%)
- **Mixed**: 5 (10%)

### Difficulty Distribution
- **Easy**: ~40%
- **Medium**: ~50%
- **Hard**: ~10%

### Average Task Characteristics
- **Average Inputs**: 2-4 ports
- **Average Outputs**: 1-3 ports
- **Average Lines of Code**: 10-50 lines
- **Average Test Cases**: 4-16 cases

## Future Enhancements

### Planned Additions
1. **Wider Designs**: 8-bit, 16-bit variants
2. **More FSM Types**: More sequence detectors, controllers
3. **Advanced Sequential**: FIFOs, pipelines
4. **Complex Mixed**: Processors, datapaths

### Research Directions
1. **Specification Variation**: Multiple specifications per design
2. **Difficulty Calibration**: Refined difficulty levels
3. **Coverage Metrics**: Test coverage analysis
4. **Error Taxonomy**: Systematic error classification

---

**Last Updated**: November 2025  
**Dataset Version**: 1.0 (50 tasks)

