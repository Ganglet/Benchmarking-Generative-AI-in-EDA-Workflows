# Extending the Framework

This guide explains how to extend the benchmarking framework with new tasks, models, post-processors, and evaluation metrics.

## Adding New Tasks

### Step 1: Create Reference Files

Create the reference Verilog module and testbench files:

**Example: `dataset/combinational/new_task/reference.v`**
```verilog
module new_task_001(
    input a,
    input b,
    output y
);
    assign y = a & b;
endmodule
```

**Example: `dataset/combinational/new_task/testbench.v`**
```verilog
module testbench;
    reg a, b;
    wire y;
    
    new_task_001 dut(.a(a), .b(b), .y(y));
    
    initial begin
        a = 0; b = 0; #10;
        if (y !== 0) $display("FAIL: 0&0 should be 0");
        else $display("PASS: 0&0 = 0");
        
        a = 1; b = 1; #10;
        if (y !== 1) $display("FAIL: 1&1 should be 1");
        else $display("PASS: 1&1 = 1");
        
        $finish;
    end
endmodule
```

### Step 2: Add Task Metadata

Add entry to `dataset/tasks.json`:

```json
{
  "task_id": "comb_new_task_001",
  "category": "combinational",
  "difficulty": "easy",
  "specification": "Design a 2-input AND gate in Verilog. Module should have two 1-bit inputs (a, b) and one 1-bit output (y).",
  "reference_hdl": "combinational/new_task/reference.v",
  "reference_tb": "combinational/new_task/testbench.v",
  "inputs": ["a", "b"],
  "outputs": ["y"]
}
```

### Step 3: Validate

Run dataset validation:

```bash
cd Quantitative
python dataset_loader.py
```

### Task Requirements

1. **Synthesizable Verilog-2001**: Must compile with Verilator/Icarus
2. **Self-Checking Testbench**: Must use `$display` for pass/fail
3. **Clear Specification**: Natural language description
4. **Correct I/O**: Match reference module interface

### Task Categories

- **`combinational`**: Combinational logic (gates, adders, mux, decoders)
- **`sequential`**: Sequential logic (flip-flops, registers, counters)
- **`fsm`**: Finite state machines (sequence detectors, controllers)
- **`mixed`**: Mixed/complex designs (ALUs, priority encoders)

### Difficulty Levels

- **`easy`**: Simple designs (basic gates, DFF)
- **`medium`**: Moderate complexity (adders, counters, simple FSMs)
- **`hard`**: Complex designs (ALUs, complex FSMs)

---

## Adding New Models

### Option 1: Ollama Models

If the model is available via Ollama:

```python
# In run_phase2.py or run_phase4.py
try:
    new_model = OllamaInterface("model-name")
    models.append(("Model-Name", new_model))
    print("  ✓ Model-Name ready")
except Exception as e:
    print(f"  ⚠ Model-Name failed: {e}")
```

**Setup**:
```bash
ollama pull model-name
```

### Option 2: HuggingFace Models

For HuggingFace Transformers models:

```python
from model_interface import HuggingFaceInterface

# In run_phase2.py or run_phase4.py
try:
    new_model = HuggingFaceInterface("org/model-name")
    models.append(("Model-Name", new_model))
    print("  ✓ Model-Name ready")
except Exception as e:
    print(f"  ⚠ Model-Name failed: {e}")
```

### Option 3: Custom Model Interface

Implement the model interface:

```python
class CustomModelInterface:
    def generate_hdl(
        self,
        specification: str,
        temperature: float = 0.0,
        max_tokens: int = 512
    ) -> Tuple[str, float]:
        """
        Generate Verilog HDL from specification.
        
        Args:
            specification: Task specification text
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Tuple of (generated_code, generation_time)
        """
        start_time = time.time()
        
        # Your model generation logic here
        code = your_model.generate(specification, temperature, max_tokens)
        
        generation_time = time.time() - start_time
        return code, generation_time
```

Then use it in phase runners:

```python
custom_model = CustomModelInterface()
models.append(("Custom-Model", custom_model))
```

---

## Adding New Post-Processors

### Extending `post_process_verilog()`

Edit `run_phase2.py` and add your post-processing step:

```python
def post_process_verilog(code: str, expected_module_name: str) -> str:
    # Existing post-processing steps...
    
    # Your new post-processing step
    code = your_custom_post_processor(code)
    
    return code
```

### Creating a Standalone Post-Processor

```python
def custom_post_processor(code: str) -> str:
    """
    Your custom post-processing logic.
    
    Args:
        code: Raw Verilog code
        
    Returns:
        Processed Verilog code
    """
    # Your processing logic
    processed_code = code  # Apply transformations
    
    return processed_code
```

Then import and use:

```python
from your_module import custom_post_processor

# In post_process_verilog()
code = custom_post_processor(code)
```

---

## Adding New Semantic Repair Tools

### Step 1: Implement Repair Interface

```python
class YourRepairTool:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
    
    def repair(self, code: str, task: BenchmarkTask, metrics: EvaluationMetrics) -> Tuple[str, List[str]]:
        """
        Repair code based on semantic analysis.
        
        Args:
            code: Generated Verilog code
            task: Task specification
            metrics: Current evaluation metrics
            
        Returns:
            Tuple of (repaired_code, applied_repairs_list)
        """
        if not self.enabled:
            return code, []
        
        # Your repair logic
        repaired_code = code  # Apply repairs
        applied_repairs = []  # List of applied repairs
        
        return repaired_code, applied_repairs
```

### Step 2: Integrate with SemanticRepair

Edit `semantic_repair.py`:

```python
from your_repair_tool import YourRepairTool

class SemanticRepair:
    def __init__(self, enable_your_tool: bool = True, ...):
        # ... existing initialization ...
        self.your_repair_tool = YourRepairTool(enable_your_tool)
    
    def repair(self, code: str, task: BenchmarkTask, metrics: EvaluationMetrics) -> Tuple[str, List[str]]:
        # ... existing repair logic ...
        
        # Apply your repair tool
        code, repairs = self.your_repair_tool.repair(code, task, metrics)
        applied_repairs.extend(repairs)
        
        return code, applied_repairs
```

### Step 3: Update Configuration

Edit `phase4_config.py`:

```python
class Phase4Config:
    # ... existing config ...
    ENABLE_YOUR_REPAIR_TOOL = True
```

---

## Adding New Evaluation Metrics

### Step 1: Extend EvaluationMetrics

Edit `Eval_Pipeline.py`:

```python
@dataclass
class EvaluationMetrics:
    # ... existing fields ...
    
    # Your new metric
    your_metric: Optional[float] = None
    your_metric_details: Optional[Dict] = None
```

### Step 2: Compute Metric in Pipeline

Edit `BenchmarkPipeline.evaluate_task()`:

```python
def evaluate_task(self, task: BenchmarkTask, model: AIModelInterface) -> EvaluationMetrics:
    # ... existing evaluation ...
    
    # Compute your metric
    your_metric_value = compute_your_metric(generated_code, task)
    
    metrics = EvaluationMetrics(
        # ... existing metrics ...
        your_metric=your_metric_value,
        your_metric_details=your_metric_details
    )
    
    return metrics
```

### Step 3: Update Analysis Tools

Edit `statistical_analysis.py`:

```python
class BenchmarkAnalyzer:
    def print_summary_report(self):
        # ... existing report ...
        
        # Add your metric
        print(f"  Your Metric: {mean_your_metric:.2f}")
```

---

## Adding New Analysis Tools

### Creating a Standalone Analysis Script

```python
"""
Your custom analysis tool.
"""

import json
from pathlib import Path
from typing import Dict, List

def analyze_results(results_file: Path) -> Dict:
    """
    Analyze benchmark results.
    
    Args:
        results_file: Path to results JSON file
        
    Returns:
        Analysis results dictionary
    """
    with open(results_file) as f:
        results = json.load(f)
    
    # Your analysis logic
    analysis = {}
    
    return analysis

def main():
    import sys
    results_file = Path(sys.argv[1])
    analysis = analyze_results(results_file)
    
    # Print or save analysis
    print(json.dumps(analysis, indent=2))

if __name__ == "__main__":
    main()
```

### Integration with Existing Tools

You can also extend `statistical_analysis.py`:

```python
class BenchmarkAnalyzer:
    # ... existing methods ...
    
    def your_custom_analysis(self) -> Dict:
        """Your custom analysis method."""
        # Your analysis logic
        return analysis_results
```

---

## Adding New Visualization Types

### Extending visualizations.py

```python
class BenchmarkVisualizer:
    # ... existing methods ...
    
    def plot_your_custom_plot(self, output_path: str):
        """
        Generate your custom visualization.
        
        Args:
            output_path: Path to save the plot
        """
        import matplotlib.pyplot as plt
        
        # Your plotting logic
        fig, ax = plt.subplots()
        # ... create plot ...
        
        plt.savefig(output_path)
        plt.close()
```

---

## Configuration Extensions

### Adding New Configuration Options

Edit `phase4_config.py`:

```python
class Phase4Config:
    # ... existing config ...
    
    # Your new configuration
    ENABLE_YOUR_FEATURE = True
    YOUR_FEATURE_PARAMETER = 0.5
```

### Adding to instruction.json

```json
{
  "your_new_section": {
    "your_setting": "value",
    "your_parameter": 123
  }
}
```

---

## Testing Your Extensions

### Unit Testing

```python
def test_your_extension():
    # Test your new functionality
    result = your_function(input_data)
    assert result == expected_output
```

### Integration Testing

```python
def test_integration():
    # Test integration with existing pipeline
    task = load_task("comb_and_gate_001")
    # Use your extension
    result = pipeline_with_your_extension.evaluate_task(task, model)
    assert result.your_metric is not None
```

### Manual Testing

1. Run dataset validation: `python dataset_loader.py`
2. Run mini benchmark: `python run_mini_benchmark.py`
3. Verify results include your extension
4. Check for any errors or warnings

---

## Best Practices

### Code Style
- Follow PEP 8
- Add docstrings to all functions
- Use type hints
- Keep functions focused

### Documentation
- Document your extension
- Add examples
- Update relevant docs files
- Include usage instructions

### Testing
- Write unit tests
- Test edge cases
- Verify integration
- Check error handling

### Performance
- Consider efficiency
- Add timeouts if needed
- Handle large inputs
- Optimize if necessary

---

## Getting Help

- Check existing code for examples
- Review documentation in `docs/`
- Open an issue for questions
- See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines

---

## Examples

See the codebase for examples of:
- Task definitions in `dataset/tasks.json`
- Model interfaces in `model_interface.py`
- Post-processors in `run_phase2.py`
- Semantic repair tools in `semantic_repair.py`
- Analysis tools in `statistical_analysis.py`
- Visualizations in `visualizations.py`

