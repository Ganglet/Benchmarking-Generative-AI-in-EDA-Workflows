#!/usr/bin/env python3
"""
Mini Benchmark: Quick test with first 5 tasks
A simplified benchmark runner for quick validation and testing
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# Import necessary components from run_phase2
from run_phase2 import (
    extract_module_name,
    get_port_spec,
    get_constrained_prompt,
    post_process_verilog,
    compute_statistics,
    REPETITIONS_PER_PROMPT,
    TEMPERATURE
)
from dataset_loader import load_tasks_from_json, print_dataset_stats, validate_dataset
from model_interface import OllamaInterface, HuggingFaceInterface
from Eval_Pipeline import BenchmarkPipeline, EvaluationMetrics, HDLCompiler, HDLSimulator
import time
import json
import statistics
from collections import defaultdict

def main():
    print("="*70)
    print("MINI BENCHMARK: Quick Test (First 5 Tasks)")
    print("="*70)
    print(f"\n📊 Configuration:")
    print(f"  • Repetitions per prompt: {REPETITIONS_PER_PROMPT}")
    print(f"  • Temperature: {TEMPERATURE}")
    print(f"  • Tasks: First 5 tasks from dataset")
    
    # Load dataset
    dataset_path = Path(__file__).parent / "dataset" / "tasks.json"
    print(f"\n📁 Loading tasks from: {dataset_path}")
    
    tasks = load_tasks_from_json(str(dataset_path))
    print_dataset_stats(tasks)
    validate_dataset(tasks)
    
    # Use only first 5 tasks for mini benchmark
    test_tasks = tasks[:5]
    print(f"\n📋 Running mini benchmark on {len(test_tasks)} tasks:")
    for i, task in enumerate(test_tasks, 1):
        print(f"  {i}. {task.task_id}")
    
    # Initialize models
    print("\n🤖 Initializing models...")
    models = []
    
    # Large model: Llama-3-8B
    try:
        llama3 = OllamaInterface("llama3")
        models.append(("Llama-3-8B-Large", llama3))
        print("  ✓ Llama-3 8B (Large tier) ready")
    except Exception as e:
        print(f"  ⚠ Llama-3 8B failed: {e}")
    
    # Medium model: StarCoder2-7B (try Ollama first, then HuggingFace)
    try:
        starcoder2 = OllamaInterface("starcoder2:7b")
        models.append(("StarCoder2-7B-Medium", starcoder2))
        print("  ✓ StarCoder2 7B (Medium tier) ready via Ollama")
    except Exception as e:
        try:
            print(f"  ⚠ StarCoder2 via Ollama failed: {e}")
            print(f"  Trying HuggingFace...")
            starcoder2 = HuggingFaceInterface("bigcode/starcoder2-7b")
            models.append(("StarCoder2-7B-Medium", starcoder2))
            print("  ✓ StarCoder2 7B (Medium tier) ready via HuggingFace")
        except Exception as e:
            print(f"  ⚠ StarCoder2 7B not available: {e}")
    
    # Small model: TinyLlama-1.1B
    try:
        tinyllama = OllamaInterface("tinyllama")
        models.append(("TinyLlama-1.1B-Small", tinyllama))
        print("  ✓ TinyLlama 1.1B (Small tier) ready")
    except Exception as e:
        print(f"  ⚠ TinyLlama not available: {e}")
    
    if not models:
        print("❌ No models available!")
        print("\nPlease ensure at least one model is available:")
        print("  - Ollama: ollama pull llama3 (or tinyllama)")
        print("  - Or configure HuggingFace model")
        return
    
    print(f"\n✓ {len(models)} model(s) ready")
    
    # Setup output
    output_dir = Path(__file__).parent.parent / "results" / "mini_benchmark"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n📊 Saving to: {output_dir}")
    
    pipeline = BenchmarkPipeline(output_dir)
    compiler = HDLCompiler()
    simulator = HDLSimulator()
    
    total_tasks = len(test_tasks)
    
    print("\n" + "="*70)
    print("RUNNING MINI BENCHMARK")
    print("="*70)
    print(f"\nTesting {total_tasks} tasks × {len(models)} models × {REPETITIONS_PER_PROMPT} repetitions\n")
    
    # Store all results for statistics
    all_results = []
    task_statistics = {}
    
    for model_name, model in models:
        print(f"\n{'='*70}")
        print(f"Evaluating: {model_name}")
        print(f"{'='*70}")
        
        for task in test_tasks:
            print(f"\n  Task: {task.task_id} ({task.category})")
            module_name = extract_module_name(task.task_id)
            prompt = get_constrained_prompt(task.spec, module_name)
            
            task_runs = []
            
            for rep in range(REPETITIONS_PER_PROMPT):
                try:
                    # Generate with constrained prompt
                    code, gen_time = model.generate_hdl(prompt, temperature=TEMPERATURE)
                    
                    # Post-process
                    code = post_process_verilog(code, module_name)
                    
                    # Save code
                    task_dir = output_dir / f"{model_name.replace('-', '_')}_{task.task_id}"
                    task_dir.mkdir(exist_ok=True)
                    hdl_file = task_dir / f"{task.task_id}_rep{rep+1}.v"
                    hdl_file.write_text(code)
                    
                    # Compile
                    compile_start = time.time()
                    syntax_valid, errors = compiler.compile(hdl_file, task_dir)
                    compile_time = time.time() - compile_start
                    
                    # Simulate if syntax valid
                    sim_passed = False
                    tests_passed = 0
                    tests_total = 0
                    sim_time = 0.0
                    
                    if syntax_valid and task.reference_tb:
                        sim_start = time.time()
                        sim_passed, tests_passed, tests_total, _ = simulator.simulate(
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
                    
                    task_runs.append(metrics)
                    all_results.append(metrics)
                    
                    status = "✓" if syntax_valid else "✗"
                    sim_status = "✓" if sim_passed else "✗"
                    print(f"    Rep {rep+1}: Syntax {status} | Sim {sim_status} | Time: {gen_time:.2f}s")
                    
                except Exception as e:
                    print(f"    Rep {rep+1}: Error - {e}")
                    continue
            
            # Compute statistics for this task
            if task_runs:
                syntax_valid_rate = sum(1 for r in task_runs if r.syntax_valid) / len(task_runs)
                sim_pass_rate = sum(1 for r in task_runs if r.simulation_passed) / len(task_runs)
                avg_gen_time = statistics.mean([r.generation_time for r in task_runs])
                
                task_statistics[f"{model_name}_{task.task_id}"] = {
                    "syntax_valid_rate": syntax_valid_rate,
                    "sim_pass_rate": sim_pass_rate,
                    "avg_gen_time": avg_gen_time,
                    "repetitions": len(task_runs)
                }
    
    # Save results
    results_file = output_dir / "benchmark_results.json"
    with open(results_file, 'w') as f:
        json.dump([r.to_dict() for r in all_results], f, indent=2)
    
    stats_file = output_dir / "statistics.json"
    with open(stats_file, 'w') as f:
        json.dump(task_statistics, f, indent=2)
    
    # Print summary
    print("\n" + "="*70)
    print("MINI BENCHMARK SUMMARY")
    print("="*70)
    
    for model_name, _ in models:
        model_results = [r for r in all_results if r.model_name == model_name]
        if not model_results:
            continue
        
        total = len(model_results)
        syntax_valid = sum(1 for r in model_results if r.syntax_valid)
        sim_passed = sum(1 for r in model_results if r.simulation_passed)
        avg_gen_time = statistics.mean([r.generation_time for r in model_results])
        
        print(f"\n{model_name}:")
        print(f"  Syntax Valid: {syntax_valid}/{total} ({100*syntax_valid/total:.1f}%)")
        print(f"  Simulation Passed: {sim_passed}/{total} ({100*sim_passed/total:.1f}%)")
        print(f"  Avg Generation Time: {avg_gen_time:.2f}s")
    
    print(f"\n✓ Results saved to: {results_file}")
    print(f"✓ Statistics saved to: {stats_file}")

if __name__ == "__main__":
    main()

