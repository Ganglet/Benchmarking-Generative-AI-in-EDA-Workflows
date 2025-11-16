"""
EDA AI Benchmarking Framework
Automated evaluation pipeline for generative AI models in HDL design
"""

import json
import subprocess
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
import re

@dataclass
class BenchmarkTask:
    """Represents a single HDL design task"""
    task_id: str
    spec: str
    reference_hdl: str
    reference_tb: str
    category: str
    inputs: List[str]
    outputs: List[str]
    
@dataclass
class EvaluationMetrics:
    """Stores all evaluation metrics for a task"""
    task_id: str
    model_name: str
    
    # Syntax Validity
    syntax_valid: bool
    compile_errors: List[str]
    
    # Functional Correctness
    simulation_passed: bool
    test_cases_passed: int
    test_cases_total: int
    
    # Synthesis Quality
    gate_count: Optional[int]
    cell_count: Optional[int]
    estimated_area: Optional[float]
    
    # Generation Efficiency
    generation_time: float
    compile_time: float
    simulation_time: float
    
    # Testbench Coverage (if testbench generated)
    tb_generated: bool
    fault_detection_ratio: Optional[float]
    
    # Phase 4: Iterative Refinement and Confidence
    iteration_count: int = 1
    confidence_log_prob: Optional[float] = None
    confidence_entropy: Optional[float] = None
    waveform_diff_summary: Optional[str] = None
    formal_equiv_status: Optional[str] = None
    semantic_repair_applied: List[str] = None
    # Fast-path diagnostics (Phase 4 scaling)
    fast_skip_reason: Optional[str] = None
    
    def __post_init__(self):
        """Initialize default values for optional fields"""
        if self.semantic_repair_applied is None:
            self.semantic_repair_applied = []
    
    def to_dict(self):
        return asdict(self)

class HDLCompiler:
    """Handles HDL compilation using Verilator or Icarus Verilog"""
    
    def __init__(self, tool="verilator"):
        self.tool = tool
        
    def compile(self, hdl_file: Path, output_dir: Path) -> tuple[bool, List[str]]:
        """
        Compile HDL file and return success status and errors
        """
        errors = []
        try:
            if self.tool == "verilator":
                result = subprocess.run(
                    ["verilator", "--lint-only", str(hdl_file)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:  # iverilog
                result = subprocess.run(
                    ["iverilog", "-t", "null", str(hdl_file)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            
            if result.returncode != 0:
                errors = self._parse_errors(result.stderr)
                return False, errors
            return True, []
            
        except subprocess.TimeoutExpired:
            return False, ["Compilation timeout"]
        except FileNotFoundError:
            return False, [f"{self.tool} not found in PATH"]
        except Exception as e:
            return False, [str(e)]
    
    def _parse_errors(self, stderr: str) -> List[str]:
        """Extract meaningful error messages"""
        lines = stderr.split('\n')
        errors = [line.strip() for line in lines if 'Error' in line or 'error' in line]
        return errors[:5]  # Limit to first 5 errors

class HDLSimulator:
    """Runs simulation and compares outputs"""
    
    def simulate(
        self, 
        hdl_file: Path, 
        testbench: Path, 
        output_dir: Path,
        generate_vcd: bool = False
    ) -> tuple[bool, int, int, Optional[Path]]:
        """
        Simulate HDL with testbench
        
        Args:
            hdl_file: Path to HDL file
            testbench: Path to testbench file
            output_dir: Directory for output files
            generate_vcd: Whether to generate VCD file
            
        Returns:
            Tuple of (passed, tests_passed, tests_total, vcd_path)
        """
        vcd_path = None
        try:
            # Use testbench with VCD if requested
            tb_to_use = testbench
            if generate_vcd:
                # Check if testbench already has $dumpvars
                tb_content = testbench.read_text()
                if "$dumpvars" not in tb_content and "$dumpfile" not in tb_content:
                    # Inject VCD dump
                    tb_with_vcd = output_dir / "testbench_with_vcd.v"
                    modified_content = self._inject_vcd_dump(tb_content)
                    tb_with_vcd.write_text(modified_content)
                    tb_to_use = tb_with_vcd
            
            # Compile with testbench
            compile_result = subprocess.run(
                ["iverilog", "-o", str(output_dir / "sim.vvp"), 
                 str(hdl_file), str(tb_to_use)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if compile_result.returncode != 0:
                return False, 0, 0, None
            
            # Run simulation
            sim_result = subprocess.run(
                ["vvp", str(output_dir / "sim.vvp")],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(output_dir)
            )
            
            # Check for VCD file
            if generate_vcd:
                vcd_path = output_dir / "waveform.vcd"
                if not vcd_path.exists():
                    # Try to find VCD file
                    vcd_files = list(output_dir.glob("*.vcd"))
                    if vcd_files:
                        vcd_path = vcd_files[0]
                    else:
                        vcd_path = None
            
            # Parse results
            passed, total = self._parse_simulation_output(sim_result.stdout)
            return passed == total, passed, total, vcd_path
            
        except Exception as e:
            print(f"Simulation error: {e}")
            return False, 0, 0, None
    
    def _inject_vcd_dump(self, tb_content: str) -> str:
        """Inject $dumpvars into testbench content"""
        # Try to find module instantiation (usually "dut")
        if "dut" in tb_content.lower():
            dut_name = "dut"
        else:
            # Try to find first module instantiation
            import re
            match = re.search(r'\s+(\w+)\s+(\w+)\s*\(', tb_content)
            if match:
                dut_name = match.group(2)
            else:
                dut_name = "dut"
        
        # Add VCD dump in initial block
        vcd_code = f"""
    $dumpfile("waveform.vcd");
    $dumpvars(0, {dut_name});
"""
        
        if "initial begin" in tb_content:
            # Add after initial begin
            tb_content = tb_content.replace(
                "initial begin",
                f"initial begin{vcd_code}"
            )
        else:
            # Add initial block at start
            tb_content = f"initial begin{vcd_code}end\n\n" + tb_content
        
        return tb_content
    
    def _parse_simulation_output(self, output: str) -> tuple[int, int]:
        """Parse test results from simulation output"""
        # Look for common test result patterns
        patterns = [
            r'(\d+)/(\d+) tests passed',
            r'PASSED: (\d+), FAILED: (\d+)',
            r'Tests passed: (\d+) out of (\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                if 'FAILED' in pattern:
                    passed = int(match.group(1))
                    failed = int(match.group(2))
                    return passed, passed + failed
                else:
                    return int(match.group(1)), int(match.group(2))
        
        # Default: check for error keywords
        if 'PASS' in output and 'FAIL' not in output:
            return 1, 1
        return 0, 1

class SynthesisTool:
    """Handles synthesis using Yosys"""
    
    def synthesize(self, hdl_file: Path, output_dir: Path) -> Dict:
        """
        Synthesize HDL and extract metrics
        Returns: dict with gate_count, cell_count, estimated_area
        """
        try:
            # Create Yosys script
            script = f"""
read_verilog {hdl_file}
hierarchy -auto-top
proc; opt; fsm; opt; memory; opt
techmap; opt
stat
"""
            script_file = output_dir / "synth.ys"
            script_file.write_text(script)
            
            # Run Yosys
            result = subprocess.run(
                ["yosys", "-s", str(script_file)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return self._parse_synthesis_stats(result.stdout)
            
        except Exception as e:
            print(f"Synthesis error: {e}")
            return {"gate_count": None, "cell_count": None, "estimated_area": None}
    
    def _parse_synthesis_stats(self, output: str) -> Dict:
        """Extract synthesis statistics"""
        stats = {
            "gate_count": None,
            "cell_count": None,
            "estimated_area": None
        }
        
        # Parse Yosys stat output
        cell_match = re.search(r'Number of cells:\s+(\d+)', output)
        if cell_match:
            stats["cell_count"] = int(cell_match.group(1))
            stats["gate_count"] = stats["cell_count"]  # Approximate
            stats["estimated_area"] = stats["cell_count"] * 1.0  # Normalized units
        
        return stats

class AIModelInterface:
    """Interface for querying AI models"""
    
    def __init__(self, model_name: str, api_endpoint: Optional[str] = None):
        self.model_name = model_name
        self.api_endpoint = api_endpoint
    
    def generate_hdl(self, spec: str, context: Dict = None) -> tuple[str, float]:
        """
        Generate HDL code from specification
        Returns: (generated_code, generation_time)
        """
        start_time = time.time()
        
        # Construct prompt
        prompt = self._construct_prompt(spec, context)
        
        # TODO: Implement actual model inference
        # This is a placeholder for the actual API call
        generated_code = self._mock_generation(spec)
        
        generation_time = time.time() - start_time
        return generated_code, generation_time
    
    def _construct_prompt(self, spec: str, context: Dict = None) -> str:
        """Build prompt for the model"""
        prompt = f"""Generate Verilog code for the following specification:

{spec}

Requirements:
- Use proper Verilog syntax
- Include module declaration with ports
- Add comments for clarity
- Ensure synthesizable code

Verilog code:
"""
        return prompt
    
    def _mock_generation(self, spec: str) -> str:
        """Mock generation for testing pipeline"""
        return """module example(
    input wire clk,
    input wire rst,
    output reg [7:0] out
);
    always @(posedge clk or posedge rst) begin
        if (rst)
            out <= 8'b0;
        else
            out <= out + 1;
    end
endmodule"""

class BenchmarkPipeline:
    """Main benchmarking pipeline orchestrator"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        
        self.compiler = HDLCompiler()
        self.simulator = HDLSimulator()
        self.synthesizer = SynthesisTool()
        
        self.results = []
    
    def evaluate_task(self, task: BenchmarkTask, model: AIModelInterface) -> EvaluationMetrics:
        """
        Run complete evaluation pipeline for a single task
        """
        print(f"Evaluating task: {task.task_id}")
        
        # Create task-specific directory
        task_dir = self.output_dir / task.task_id
        task_dir.mkdir(exist_ok=True)
        
        # Generate HDL
        generated_code, gen_time = model.generate_hdl(task.spec)
        
        # Save generated code
        hdl_file = task_dir / f"{task.task_id}.v"
        hdl_file.write_text(generated_code)
        
        # Syntax validation
        compile_start = time.time()
        syntax_valid, errors = self.compiler.compile(hdl_file, task_dir)
        compile_time = time.time() - compile_start
        
        # Functional verification (if syntax valid)
        sim_passed = False
        tests_passed = 0
        tests_total = 0
        sim_time = 0.0
        
        if syntax_valid and task.reference_tb:
            sim_start = time.time()
            sim_passed, tests_passed, tests_total = self.simulator.simulate(
                hdl_file, Path(task.reference_tb), task_dir
            )
            sim_time = time.time() - sim_start
        
        # Synthesis (if functionally correct)
        synth_stats = {"gate_count": None, "cell_count": None, "estimated_area": None}
        if syntax_valid:
            synth_stats = self.synthesizer.synthesize(hdl_file, task_dir)
        
        # Create metrics object
        metrics = EvaluationMetrics(
            task_id=task.task_id,
            model_name=model.model_name,
            syntax_valid=syntax_valid,
            compile_errors=errors,
            simulation_passed=sim_passed,
            test_cases_passed=tests_passed,
            test_cases_total=tests_total,
            gate_count=synth_stats["gate_count"],
            cell_count=synth_stats["cell_count"],
            estimated_area=synth_stats["estimated_area"],
            generation_time=gen_time,
            compile_time=compile_time,
            simulation_time=sim_time,
            tb_generated=False,
            fault_detection_ratio=None
        )
        
        self.results.append(metrics)
        return metrics
    
    def run_benchmark(self, tasks: List[BenchmarkTask], models: List[AIModelInterface]):
        """
        Run complete benchmark suite
        """
        print(f"Starting benchmark with {len(tasks)} tasks and {len(models)} models")
        
        for model in models:
            print(f"\nEvaluating model: {model.model_name}")
            for task in tasks:
                metrics = self.evaluate_task(task, model)
                print(f"  {task.task_id}: Valid={metrics.syntax_valid}, "
                      f"Passed={metrics.simulation_passed}")
        
        # Save results
        self.save_results()
    
    def save_results(self):
        """Save benchmark results to JSON"""
        results_file = self.output_dir / "benchmark_results.json"
        with open(results_file, 'w') as f:
            json.dump([r.to_dict() for r in self.results], f, indent=2)
        print(f"\nResults saved to {results_file}")
    
    def generate_report(self):
        """Generate summary report"""
        if not self.results:
            print("No results to report")
            return
        
        # Group by model
        by_model = {}
        for result in self.results:
            model = result.model_name
            if model not in by_model:
                by_model[model] = []
            by_model[model].append(result)
        
        # Print summary
        print("\n" + "="*70)
        print("BENCHMARK SUMMARY")
        print("="*70)
        
        for model, results in by_model.items():
            print(f"\nModel: {model}")
            print("-" * 50)
            
            total = len(results)
            syntax_valid = sum(1 for r in results if r.syntax_valid)
            sim_passed = sum(1 for r in results if r.simulation_passed)
            
            avg_gen_time = sum(r.generation_time for r in results) / total
            avg_compile_time = sum(r.compile_time for r in results) / total
            
            print(f"  Total tasks: {total}")
            print(f"  Syntax valid: {syntax_valid}/{total} ({100*syntax_valid/total:.1f}%)")
            print(f"  Simulation passed: {sim_passed}/{total} ({100*sim_passed/total:.1f}%)")
            print(f"  Avg generation time: {avg_gen_time:.3f}s")
            print(f"  Avg compile time: {avg_compile_time:.3f}s")

# Example usage
if __name__ == "__main__":
    # Setup
    output_dir = Path("./benchmark_output")
    pipeline = BenchmarkPipeline(output_dir)
    
    # Create sample tasks
    tasks = [
        BenchmarkTask(
            task_id="mux_4to1_001",
            spec="Design a 4-to-1 multiplexer in Verilog with 4 data inputs, 1 select input, and 1 output",
            reference_hdl="ref/mux4.v",
            reference_tb="ref/mux4_tb.v",
            category="combinational",
            inputs=["d0", "d1", "d2", "d3", "sel"],
            outputs=["out"]
        ),
        BenchmarkTask(
            task_id="counter_8bit_001",
            spec="Design an 8-bit synchronous counter with reset",
            reference_hdl="ref/counter8.v",
            reference_tb="ref/counter8_tb.v",
            category="sequential",
            inputs=["clk", "rst"],
            outputs=["count[7:0]"]
        )
    ]
    
    # Create model instances
    models = [
        AIModelInterface("Llama-3-8B-Instruct"),
        AIModelInterface("StarCoder2-7B"),
        AIModelInterface("TinyLlama-1.1B")
    ]
    
    # Run benchmark
    pipeline.run_benchmark(tasks, models)
    pipeline.generate_report()