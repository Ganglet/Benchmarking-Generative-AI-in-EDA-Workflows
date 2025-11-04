#!/usr/bin/env python3
"""
Improved Benchmark Runner - With Enhanced Prompting Strategies
Phases 1-3 Implementation
"""

import sys
import re
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dataset_loader import load_tasks_from_json, print_dataset_stats, validate_dataset
from model_interface import OllamaInterface, create_model_interface
from Eval_Pipeline import BenchmarkPipeline, EvaluationMetrics


# ============================================================================
# PHASE 1: IMPROVED PROMPTING
# ============================================================================

def get_few_shot_prompt_for_task(task_spec: str, module_name: str = None) -> str:
    """
    Phase 1: Few-shot learning with examples
    """
    module_hint = f"\nCRITICAL: Module name must be exactly: {module_name}" if module_name else ""
    
    return f"""You are a Verilog HDL expert. Generate synthesizable Verilog-2001 code.

Here are examples of CORRECT Verilog modules:

Example 1 - Simple Combinational Logic:
module or_gate(input wire a, input wire b, output wire y);
    assign y = a | b;
endmodule

Example 2 - Multi-bit Combinational:
module adder_4bit(input wire [3:0] a, input wire [3:0] b, output wire [3:0] sum, output wire carry);
    wire [4:0] temp;
    assign temp = a + b;
    assign sum = temp[3:0];
    assign carry = temp[4];
endmodule

Example 3 - Sequential Logic:
module dff(input wire clk, input wire rst, input wire d, output reg q);
    always @(posedge clk) begin
        if (rst)
            q <= 1'b0;
        else
            q <= d;
    end
endmodule

Now generate Verilog for this specification:
{task_spec}
{module_hint}

REQUIREMENTS:
- Start with 'module' keyword
- End with 'endmodule'
- Use 'wire' with 'assign' for combinational logic
- Use 'reg' with 'always @(posedge clk)' for sequential logic
- NO code outside module definition
- Use ONLY standard Verilog-2001 syntax
- NO SystemVerilog, NO BSV, NO invented keywords
- Match port names EXACTLY as specified in description

Generate ONLY the module code (no explanations):
"""


# ============================================================================
# PHASE 2: MODULE/PORT NAME ENFORCEMENT + POST-PROCESSING
# ============================================================================

def extract_module_name_from_task_id(task_id: str) -> str:
    """Extract expected module name from task ID (with special cases)."""
    name = task_id.replace("comb_", "").replace("seq_", "")
    base = name.rsplit("_", 1)[0]
    special_map = {
        "dff": "d_flipflop",
    }
    return special_map.get(base, base)


def get_port_specification(module_name: str) -> dict:
    """
    Phase 2: Get exact port specifications for known modules
    """
    port_specs = {
        "and_gate": {
            "ports": "input wire a, input wire b, output wire y",
            "description": "inputs a and b (single bits), output y"
        },
        "mux_2to1": {
            "ports": "input wire d0, input wire d1, input wire sel, output wire y",
            "description": "inputs d0, d1, sel (single bits), output y"
        },
        "adder_2bit": {
            "ports": "input wire [1:0] a, input wire [1:0] b, output wire [1:0] sum, output wire carry_out",
            "description": "inputs a[1:0] and b[1:0], outputs sum[1:0] and carry_out"
        },
        "d_flipflop": {
            "ports": "input wire clk, input wire rst, input wire d, output reg q",
            "description": "inputs clk, rst, d, output reg q"
        },
        "counter_4bit": {
            "ports": "input wire clk, input wire rst, output reg [3:0] count",
            "description": "inputs clk, rst, output reg [3:0] count"
        }
    }
    
    return port_specs.get(module_name, {
        "ports": "/* refer to specification */",
        "description": "as specified"
    })


def get_constrained_prompt_for_task(task_spec: str, module_name: str) -> str:
    """
    Phase 2: Highly constrained prompt with exact module/port names
    """
    port_info = get_port_specification(module_name)
    
    return f"""Generate ONLY synthesizable Verilog-2001 code. Follow these rules EXACTLY:

SPECIFICATION: {task_spec}

MANDATORY STRUCTURE:
module {module_name}(
    {port_info['ports']}
);
    // Your logic here
endmodule

STRICT RULES:
1. Module name MUST be exactly: {module_name}
2. Port names MUST match: {port_info['description']}
3. For combinational logic: use 'wire' type with 'assign' statements
4. For sequential logic: use 'reg' type with 'always @(posedge clk)' blocks
5. NO explanations, NO comments, NO text outside the module
6. Use ONLY these operators: &, |, ^, ~, +, -, ==, !=, <, >, ? :
7. NO 'logic', NO 'let', NO 'rule', NO invented keywords
8. NO SystemVerilog (use Verilog-2001 only)

Generate the complete module now (code only):
"""


def post_process_verilog(code: str, expected_module_name: str) -> str:
    """
    Phase 2: Fix common generation errors automatically
    """
    # Remove any text before first 'module'
    if 'module' in code:
        code = code[code.find('module'):]
    
    # Remove code after endmodule
    if 'endmodule' in code:
        end_pos = code.find('endmodule') + len('endmodule')
        code = code[:end_pos]
    
    # Fix module name if wrong
    code = re.sub(r'module\s+\w+\s*\(', f'module {expected_module_name}(', code, count=1)
    
    # Fix common hallucinations
    code = code.replace('sub-operation', '')
    code = re.sub(r'\blogic\b', 'wire', code)  # SystemVerilog -> Verilog
    code = re.sub(r'\blet\s+', 'wire ', code)  # Rust-style -> Verilog
    
    # Remove rule/endrule blocks (BSV)
    code = re.sub(r'rule\s+\w+.*?endrule', '', code, flags=re.DOTALL)
    
    # Ensure endmodule exists
    if 'endmodule' not in code:
        code += '\nendmodule'
    
    # Remove common invalid syntax patterns
    code = re.sub(r'=>', '', code)  # Arrow operators
    code = re.sub(r'input_port#.*?\n', '', code)  # SystemVerilog constructs
    code = re.sub(r'new_\w+\(.*?\)', '', code)  # Constructor calls
    
    return code


# ============================================================================
# PHASE 3: ITERATIVE REFINEMENT
# ============================================================================

def generate_with_refinement(model, task, max_attempts: int = 3, phase: int = 3):
    """
    Phase 3: Try generating code, refining on compilation errors
    """
    module_name = extract_module_name_from_task_id(task.task_id)
    previous_errors = []
    
    for attempt in range(max_attempts):
        # Build prompt based on phase and attempt
        if attempt == 0:
            if phase >= 2:
                prompt = get_constrained_prompt_for_task(task.spec, module_name)
            else:
                prompt = get_few_shot_prompt_for_task(task.spec, module_name)
        else:
            # Add error feedback for refinement
            error_text = "\n".join(previous_errors[:5])  # Limit to top 5 errors
            prompt = f"""{prompt}

PREVIOUS ATTEMPT {attempt} FAILED with these errors:
{error_text}

Fix ALL these errors and regenerate the COMPLETE module:
module {module_name}(...)
    // corrected logic
endmodule
"""
        
        # Generate code
        code, gen_time = model.generate_hdl(prompt, temperature=0.0)
        
        # Post-process if Phase 2+
        if phase >= 2:
            code = post_process_verilog(code, module_name)
        
        # Quick syntax check (without full simulation)
        from Eval_Pipeline import HDLCompiler
        import tempfile
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.v', delete=False) as f:
                f.write(code)
                temp_file = Path(f.name)
            
            compiler = HDLCompiler()
            temp_dir = Path(tempfile.mkdtemp())
            syntax_ok, errors = compiler.compile(temp_file, temp_dir)
            
            # Cleanup
            temp_file.unlink()
            
            if syntax_ok:
                print(f"    ✓ Success on attempt {attempt + 1}")
                return code, gen_time, attempt + 1
            
            previous_errors = errors
            print(f"    ⚠ Attempt {attempt + 1} failed, retrying...")
            
        except Exception as e:
            print(f"    ⚠ Quick check error: {e}")
            previous_errors = [str(e)]
    
    print(f"    ✗ All {max_attempts} attempts failed")
    return code, gen_time, max_attempts


# ============================================================================
# MAIN BENCHMARK RUNNER
# ============================================================================

def run_improved_benchmark(phase: int = 3, use_refinement: bool = True):
    """
    Run benchmark with specified improvement phase
    
    Args:
        phase: 1 (few-shot), 2 (constrained+postproc), 3 (refinement)
        use_refinement: Enable iterative refinement (Phase 3)
    """
    print("="*70)
    print(f"IMPROVED BENCHMARK - PHASE {phase}")
    print("="*70)
    print(f"Features enabled:")
    if phase >= 1:
        print("  ✓ Few-shot prompting with examples")
    if phase >= 2:
        print("  ✓ Task-specific module/port name constraints")
        print("  ✓ Automatic post-processing fixes")
    if phase >= 3 and use_refinement:
        print("  ✓ Iterative refinement (up to 3 attempts)")
    print()
    
    # 1. Load dataset
    dataset_path = Path(__file__).parent / "dataset" / "tasks.json"
    print(f"📁 Loading tasks from: {dataset_path}")
    
    try:
        tasks = load_tasks_from_json(str(dataset_path))
        print_dataset_stats(tasks)
        
        if not validate_dataset(tasks):
            print("⚠ Dataset validation failed. Some files are missing.")
            return
        
    except Exception as e:
        print(f"✗ Error loading dataset: {e}")
        return
    
    # 2. Initialize models
    print("\n🤖 Initializing AI models...")
    models = []
    
    # Try Ollama models
    try:
        print("  Attempting to connect to Ollama...")
        llama_model = OllamaInterface("llama3")
        models.append(("Llama-3-8B-Large", llama_model))
        print("  ✓ Llama-3 8B (Large tier) ready")
    except Exception as e:
        print(f"  ⚠ Could not load Llama-3 8B: {e}")
    
    # Add TinyLlama for model size comparison
    try:
        tinyllama_model = OllamaInterface("tinyllama")
        models.append(("TinyLlama-1.1B-Small", tinyllama_model))
        print("  ✓ TinyLlama 1.1B (Small tier) ready")
    except Exception as e:
        print(f"  ⚠ Could not load TinyLlama: {e}")
    
    if not models:
        print("\n✗ No models available!")
        return
    
    print(f"\n✓ {len(models)} model(s) ready for benchmarking")
    
    # 3. Setup pipeline
    output_dir = Path(__file__).parent.parent / "results" / f"phase{phase}_benchmark"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📊 Results will be saved to: {output_dir}")
    
    pipeline = BenchmarkPipeline(output_dir)
    
    # 4. Run benchmark
    print("\n" + "="*70)
    print("RUNNING BENCHMARK")
    print("="*70)
    
    test_tasks = tasks[:min(5, len(tasks))]
    
    print(f"\nTesting {len(test_tasks)} tasks with {len(models)} models")
    print(f"Total evaluations: {len(test_tasks) * len(models)}\n")
    
    for model_name, model_interface in models:
        print(f"\n{'='*70}")
        print(f"MODEL: {model_name}")
        print(f"{'='*70}")
        
        for i, task in enumerate(test_tasks, 1):
            print(f"\n[{i}/{len(test_tasks)}] Evaluating: {task.task_id}")
            print(f"  Category: {task.category}")
            print(f"  Spec: {task.spec[:60]}...")
            
            try:
                module_name = extract_module_name_from_task_id(task.task_id)
                
                # Generate code based on phase
                if phase >= 3 and use_refinement:
                    # Phase 3: With refinement
                    code, gen_time, attempts = generate_with_refinement(
                        model_interface, task, max_attempts=3, phase=phase
                    )
                else:
                    # Phase 1-2: Direct generation
                    if phase >= 2:
                        prompt = get_constrained_prompt_for_task(task.spec, module_name)
                    else:
                        prompt = get_few_shot_prompt_for_task(task.spec, module_name)
                    
                    code, gen_time = model_interface.generate_hdl(prompt, temperature=0.0)
                    attempts = 1
                    
                    if phase >= 2:
                        code = post_process_verilog(code, module_name)
                
                # Create task-specific directory
                task_dir = output_dir / task.task_id
                task_dir.mkdir(exist_ok=True)
                
                # Save generated code
                hdl_file = task_dir / f"{task.task_id}.v"
                hdl_file.write_text(code)
                
                # Evaluate using pipeline
                from Eval_Pipeline import HDLCompiler, HDLSimulator, SynthesisTool
                import time
                
                compiler = HDLCompiler()
                simulator = HDLSimulator()
                
                # Syntax validation
                compile_start = time.time()
                syntax_valid, errors = compiler.compile(hdl_file, task_dir)
                compile_time = time.time() - compile_start
                
                # Simulation
                sim_passed = False
                tests_passed = 0
                tests_total = 0
                sim_time = 0.0
                
                if syntax_valid and task.reference_tb:
                    sim_start = time.time()
                    sim_passed, tests_passed, tests_total = simulator.simulate(
                        hdl_file, Path(task.reference_tb), task_dir
                    )
                    sim_time = time.time() - sim_start
                
                # Create metrics
                metrics = EvaluationMetrics(
                    task_id=task.task_id,
                    model_name=model_name,
                    syntax_valid=syntax_valid,
                    compile_errors=errors,
                    simulation_passed=sim_passed,
                    test_cases_passed=tests_passed,
                    test_cases_total=tests_total,
                    gate_count=None,
                    cell_count=None,
                    estimated_area=None,
                    generation_time=gen_time,
                    compile_time=compile_time,
                    simulation_time=sim_time,
                    tb_generated=False,
                    fault_detection_ratio=None
                )
                
                pipeline.results.append(metrics)
                
                # Print results
                status_icon = "✓" if syntax_valid else "✗"
                print(f"  {status_icon} Syntax Valid: {syntax_valid} (attempts: {attempts})")
                
                if syntax_valid:
                    sim_icon = "✓" if sim_passed else "✗"
                    print(f"  {sim_icon} Simulation: {tests_passed}/{tests_total} tests passed")
                
                print(f"  ⏱  Generation time: {gen_time:.2f}s")
                
                if errors:
                    print(f"  ⚠  Errors: {len(errors)}")
                
            except Exception as e:
                print(f"  ✗ Error during evaluation: {e}")
                import traceback
                traceback.print_exc()
    
    # 5. Save and display results
    print("\n" + "="*70)
    print("SAVING RESULTS")
    print("="*70)
    
    pipeline.save_results()
    pipeline.generate_report()
    
    print(f"\n✓ Phase {phase} benchmark complete!")
    print(f"\nResults saved to: {output_dir}")
    print(f"  - benchmark_results.json (detailed metrics)")
    print(f"  - Individual task outputs in subdirectories")
    
    return output_dir


def main():
    """Main entry point - Run all phases"""
    print("\n🚀 Starting Improved Benchmark Runner\n")
    
    try:
        # Run Phase 1
        print("\n" + "█"*70)
        print("█" + " "*68 + "█")
        print("█" + "  PHASE 1: FEW-SHOT PROMPTING + LLAMA-4".center(68) + "█")
        print("█" + " "*68 + "█")
        print("█"*70 + "\n")
        phase1_dir = run_improved_benchmark(phase=1, use_refinement=False)
        
        # Run Phase 2
        print("\n" + "█"*70)
        print("█" + " "*68 + "█")
        print("█" + "  PHASE 2: CONSTRAINED PROMPTS + POST-PROCESSING".center(68) + "█")
        print("█" + " "*68 + "█")
        print("█"*70 + "\n")
        phase2_dir = run_improved_benchmark(phase=2, use_refinement=False)
        
        # Run Phase 3
        print("\n" + "█"*70)
        print("█" + " "*68 + "█")
        print("█" + "  PHASE 3: ITERATIVE REFINEMENT".center(68) + "█")
        print("█" + " "*68 + "█")
        print("█"*70 + "\n")
        phase3_dir = run_improved_benchmark(phase=3, use_refinement=True)
        
        # Final summary
        print("\n" + "="*70)
        print("ALL PHASES COMPLETE!")
        print("="*70)
        print("\nResults directories:")
        print(f"  Phase 1: {phase1_dir}")
        print(f"  Phase 2: {phase2_dir}")
        print(f"  Phase 3: {phase3_dir}")
        print("\nCompare results in each directory's benchmark_results.json")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Benchmark interrupted by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("Benchmark session ended")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

