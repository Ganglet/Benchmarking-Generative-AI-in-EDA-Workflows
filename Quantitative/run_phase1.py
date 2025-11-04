#!/usr/bin/env python3
"""
Phase 1 Only: Few-shot prompting with Llama-3 and Llama-4
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dataset_loader import load_tasks_from_json, print_dataset_stats, validate_dataset
from model_interface import OllamaInterface
from Eval_Pipeline import BenchmarkPipeline, EvaluationMetrics, HDLCompiler, HDLSimulator
import time


def get_few_shot_prompt(task_spec: str, module_name: str = None) -> str:
    """Few-shot learning with examples"""
    module_hint = f"\nCRITICAL: Module name must be exactly: {module_name}" if module_name else ""
    
    return f"""You are a Verilog HDL expert. Generate synthesizable Verilog-2001 code.

Here are examples of CORRECT Verilog modules:

Example 1 - Simple Logic:
module or_gate(input wire a, input wire b, output wire y);
    assign y = a | b;
endmodule

Example 2 - Multi-bit:
module adder_4bit(input wire [3:0] a, input wire [3:0] b, output wire [3:0] sum, output wire carry);
    wire [4:0] temp;
    assign temp = a + b;
    assign sum = temp[3:0];
    assign carry = temp[4];
endmodule

Example 3 - Sequential:
module dff(input wire clk, input wire rst, input wire d, output reg q);
    always @(posedge clk) begin
        if (rst) q <= 1'b0;
        else q <= d;
    end
endmodule

Now generate Verilog for: {task_spec}
{module_hint}

RULES:
- Start with 'module', end with 'endmodule'
- Use 'assign' for combinational logic
- Use 'always @(posedge clk)' for sequential
- ONLY standard Verilog-2001 syntax
- Match port names from specification

Generate ONLY the module code:
"""


def extract_module_name(task_id: str) -> str:
    """Extract expected module name from task ID (with special cases)."""
    name = task_id.replace("comb_", "").replace("seq_", "")
    base = name.rsplit("_", 1)[0]
    special_map = {
        "dff": "d_flipflop",
    }
    return special_map.get(base, base)


def main():
    print("="*70)
    print("PHASE 1: FEW-SHOT PROMPTING + LLAMA-4 TEST")
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
    output_dir = Path(__file__).parent.parent / "results" / "phase1_benchmark"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n📊 Saving to: {output_dir}")
    
    pipeline = BenchmarkPipeline(output_dir)
    compiler = HDLCompiler()
    simulator = HDLSimulator()
    
    # Test first 5 tasks
    test_tasks = tasks[:5]
    
    print("\n" + "="*70)
    print("RUNNING PHASE 1 BENCHMARK")
    print("="*70)
    print(f"\nTesting {len(test_tasks)} tasks × {len(models)} models = {len(test_tasks) * len(models)} evaluations\n")
    
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
                
                # Generate with few-shot prompt
                prompt = get_few_shot_prompt(task.spec, module_name)
                code, gen_time = model.generate_hdl(prompt, temperature=0.0)
                
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
    
    print(f"\n✓ Phase 1 complete!")
    print(f"Results: {output_dir}/benchmark_results.json")


if __name__ == "__main__":
    main()

