#!/usr/bin/env python3
"""
Phase 2: Constrained Prompts + Post-Processing Fixes
"""

import sys
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dataset_loader import load_tasks_from_json, print_dataset_stats, validate_dataset
from model_interface import OllamaInterface
from Eval_Pipeline import BenchmarkPipeline, EvaluationMetrics, HDLCompiler, HDLSimulator
import time


def extract_module_name(task_id: str) -> str:
    """Extract module name from task ID"""
    name = task_id.replace("comb_", "").replace("seq_", "")
    return name.rsplit("_", 1)[0]


def get_port_spec(module_name: str) -> dict:
    """Get exact port specifications"""
    specs = {
        "and_gate": {
            "ports": "input wire a, input wire b, output wire y",
            "desc": "a, b (inputs), y (output)"
        },
        "mux_2to1": {
            "ports": "input wire d0, input wire d1, input wire sel, output wire y",
            "desc": "d0, d1, sel (inputs), y (output)"
        },
        "adder_2bit": {
            "ports": "input wire [1:0] a, input wire [1:0] b, output wire [1:0] sum, output wire carry_out",
            "desc": "a[1:0], b[1:0] (inputs), sum[1:0], carry_out (outputs)"
        },
        "d_flipflop": {
            "ports": "input wire clk, input wire rst, input wire d, output reg q",
            "desc": "clk, rst, d (inputs), q (output reg)"
        },
        "counter_4bit": {
            "ports": "input wire clk, input wire rst, output reg [3:0] count",
            "desc": "clk, rst (inputs), count[3:0] (output reg)"
        }
    }
    return specs.get(module_name, {"ports": "/*from spec*/", "desc": "as specified"})


def get_constrained_prompt(task_spec: str, module_name: str) -> str:
    """Phase 2: Constrained prompt with exact module/port names"""
    port_info = get_port_spec(module_name)
    
    return f"""Generate ONLY synthesizable Verilog-2001 code.

SPECIFICATION: {task_spec}

MANDATORY STRUCTURE - Use this EXACT format:
module {module_name}(
    {port_info['ports']}
);
    // Your logic here
endmodule

CRITICAL RULES:
1. Module name MUST be: {module_name}
2. Port names MUST match: {port_info['desc']}
3. Combinational logic → use 'wire' + 'assign'
4. Sequential logic → use 'reg' + 'always @(posedge clk)'
5. ONLY standard Verilog-2001 syntax
6. NO SystemVerilog, NO BSV, NO invented keywords
7. For sequential: use non-blocking (<=) ONLY
8. NO explanations, ONLY code

Examples:
- Combinational: assign y = a & b;
- Sequential: always @(posedge clk) begin if (rst) q <= 0; else q <= d; end

Generate the module now:
"""


def post_process_verilog(code: str, expected_module_name: str) -> str:
    """Phase 2: Fix common errors automatically"""
    # Remove text before 'module'
    if 'module' in code:
        code = code[code.find('module'):]
    
    # Remove text after 'endmodule'
    if 'endmodule' in code:
        end_pos = code.find('endmodule') + len('endmodule')
        code = code[:end_pos]
    
    # Fix module name
    code = re.sub(r'module\s+\w+\s*\(', f'module {expected_module_name}(', code, count=1)
    
    # Fix SystemVerilog → Verilog
    code = re.sub(r'\blogic\b', 'wire', code)
    code = re.sub(r'\blet\s+', 'wire ', code)
    
    # Remove BSV constructs
    code = re.sub(r'rule\s+\w+.*?endrule', '', code, flags=re.DOTALL)
    
    # Remove invalid operators
    code = code.replace('=>', '')
    code = code.replace('sub-operation', '')
    
    # Remove SystemVerilog constructs
    code = re.sub(r'input_port#.*?\n', '', code)
    code = re.sub(r'new_\w+\(.*?\)', '', code)
    
    # Ensure endmodule exists
    if 'endmodule' not in code:
        code += '\nendmodule'
    
    return code


def main():
    print("="*70)
    print("PHASE 2: CONSTRAINED PROMPTS + POST-PROCESSING")
    print("="*70)
    
    # Load dataset
    dataset_path = Path(__file__).parent / "dataset" / "tasks.json"
    print(f"\n📁 Loading tasks from: {dataset_path}")
    
    tasks = load_tasks_from_json(str(dataset_path))
    print_dataset_stats(tasks)
    validate_dataset(tasks)
    
    # Initialize models
    print("\n🤖 Initializing models...")
    models = []
    
    try:
        llama3 = OllamaInterface("llama3")
        models.append(("Llama-3-8B-Large", llama3))
        print("  ✓ Llama-3 8B (Large tier) ready")
    except Exception as e:
        print(f"  ⚠ Llama-3 8B failed: {e}")
    
    try:
        tinyllama = OllamaInterface("tinyllama")
        models.append(("TinyLlama-1.1B-Small", tinyllama))
        print("  ✓ TinyLlama 1.1B (Small tier) ready")
    except Exception as e:
        print(f"  ⚠ TinyLlama not available: {e}")
    
    if not models:
        print("❌ No models available!")
        return
    
    print(f"\n✓ {len(models)} model(s) ready")
    
    # Setup output
    output_dir = Path(__file__).parent.parent / "results" / "phase2_benchmark"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n📊 Saving to: {output_dir}")
    
    pipeline = BenchmarkPipeline(output_dir)
    compiler = HDLCompiler()
    simulator = HDLSimulator()
    
    # Test first 5 tasks
    test_tasks = tasks[:5]
    
    print("\n" + "="*70)
    print("RUNNING PHASE 2 BENCHMARK")
    print("="*70)
    print("\nFeatures:")
    print("  ✓ Task-specific module/port name constraints")
    print("  ✓ Automatic post-processing fixes")
    print(f"\nTesting {len(test_tasks)} tasks × {len(models)} models\n")
    
    for model_name, model in models:
        print(f"\n{'='*70}")
        print(f"MODEL: {model_name}")
        print(f"{'='*70}")
        
        for i, task in enumerate(test_tasks, 1):
            print(f"\n[{i}/{len(test_tasks)}] {task.task_id}")
            print(f"  Category: {task.category}")
            
            try:
                # Get module name
                module_name = extract_module_name(task.task_id)
                
                # Generate with constrained prompt
                prompt = get_constrained_prompt(task.spec, module_name)
                code, gen_time = model.generate_hdl(prompt, temperature=0.0)
                
                # Post-process
                code = post_process_verilog(code, module_name)
                
                # Save code
                task_dir = output_dir / f"{model_name.replace('-', '_')}_{task.task_id}"
                task_dir.mkdir(exist_ok=True)
                hdl_file = task_dir / f"{task.task_id}.v"
                hdl_file.write_text(code)
                
                # Compile
                compile_start = time.time()
                syntax_valid, errors = compiler.compile(hdl_file, task_dir)
                compile_time = time.time() - compile_start
                
                # Simulate
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
                
                # Save metrics
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
                status = "✓" if syntax_valid else "✗"
                print(f"  {status} Syntax: {syntax_valid}")
                
                if syntax_valid:
                    sim_status = "✓" if sim_passed else "✗"
                    print(f"  {sim_status} Simulation: {tests_passed}/{tests_total} tests")
                    
                    if sim_passed:
                        print(f"      🎉 FUNCTIONAL SUCCESS!")
                
                print(f"  ⏱  Time: {gen_time:.2f}s")
                
                if errors:
                    print(f"  ⚠  {len(errors)} error(s)")
                    for err in errors[:2]:
                        print(f"      {err[:80]}")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                import traceback
                traceback.print_exc()
    
    # Save results
    print("\n" + "="*70)
    print("SAVING RESULTS")
    print("="*70)
    
    pipeline.save_results()
    pipeline.generate_report()
    
    print(f"\n✓ Phase 2 complete!")
    print(f"Results: {output_dir}/benchmark_results.json")


if __name__ == "__main__":
    main()

