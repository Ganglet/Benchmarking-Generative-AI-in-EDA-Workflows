#!/usr/bin/env python3
"""
Phase 4: Semantic-Aware Iterative Refinement
Integrates intelligent post-processing with adaptive iterative evaluation loop
"""

import sys
import os
import json
import statistics
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from dataset_loader import load_tasks_from_json, print_dataset_stats, validate_dataset
from model_interface import OllamaInterface, HuggingFaceInterface
from Eval_Pipeline import BenchmarkPipeline, EvaluationMetrics, HDLCompiler, HDLSimulator
from run_phase2 import extract_module_name, get_port_spec, get_constrained_prompt, post_process_verilog
from phase4_config import Phase4Config
from waveform_analyzer import WaveformAnalyzer
from formal_verifier import FormalVerifier
from ast_repair import ASTRepair
from semantic_repair import SemanticRepair
from confidence_tracker import ConfidenceTracker
from feedback_generator import FeedbackGenerator
from iterative_evaluator import IterativeEvaluator
import time

# Configuration
REPETITIONS_PER_PROMPT = 3
TEMPERATURE = 0.0


def get_task_tier(task) -> int:
    """
    Lightweight heuristic to bucket tasks into tiers for fast-path behavior.
    
    Tier 0 (trivial): basic gates and mux.
    Tier 1 (simple): adders, simple counters, basic sequential.
    Tier 2 (complex): FSM, mixed, Johnson counter, richer sequential.
    """
    tid = task.task_id
    cat = getattr(task, "category", "")
    
    if cat == "combinational":
        if any(
            name in tid
            for name in (
                "and_gate",
                "or_gate",
                "not_gate",
                "xor_gate",
                "mux_2to1",
            )
        ):
            return 0
        return 1
    
    if cat == "sequential":
        if "dff" in tid or "counter_4bit" in tid:
            return 1
        # Johnson counter, shift register, PIPO, T flip-flop are harder
        return 2
    
    if cat in ("fsm", "mixed"):
        return 2
    
    # Fallback
    return 1


def get_eval_settings_for_task(task, config: Phase4Config):
    """
    Compute evaluation settings (tier, max iterations, waveform/formal flags)
    for a given task based on the global Phase 4 configuration.
    """
    mode = getattr(config, "MODE", "fast")
    tier = get_task_tier(task) if config.ENABLE_TASK_TIERS else 2
    
    # Strict mode → use full configuration without shortcuts
    if mode == "strict":
        return {
            "tier": tier,
            "max_iterations": config.MAX_ITERATIONS,
            "enable_waveform": config.ENABLE_WAVEFORM_ANALYSIS,
            "enable_formal": config.ENABLE_FORMAL_VERIFICATION,
        }
    
    # Fast mode: tier-specific behavior
    if tier == 0:  # trivial
        max_iters = 1
        enable_waveform = False
        enable_formal = False
    elif tier == 1:  # simple
        max_iters = min(config.MAX_ITERS_SEQUENTIAL, config.MAX_ITERATIONS)
        enable_waveform = False
        enable_formal = False
    else:  # tier 2, complex
        # Use category-aware caps when available
        if task.category == "combinational":
            max_iters = min(config.MAX_ITERS_COMBINATIONAL, config.MAX_ITERATIONS)
        elif task.category == "sequential":
            max_iters = min(config.MAX_ITERS_SEQUENTIAL, config.MAX_ITERATIONS)
        elif task.category == "mixed":
            max_iters = min(config.MAX_ITERS_MIXED, config.MAX_ITERATIONS)
        else:  # fsm or unknown
            max_iters = min(config.MAX_ITERS_FSM, config.MAX_ITERATIONS)
        enable_waveform = config.ENABLE_WAVEFORM_ANALYSIS
        enable_formal = config.ENABLE_FORMAL_VERIFICATION
    
    return {
        "tier": tier,
        "max_iterations": max_iters,
        "enable_waveform": enable_waveform,
        "enable_formal": enable_formal,
    }


def compute_statistics(all_runs):
    """Compute statistics across multiple runs"""
    if not all_runs:
        return {}
    
    syntax_vals = [1 if r.get('syntax_valid', False) else 0 for r in all_runs]
    sim_vals = [1 if r.get('simulation_passed', False) else 0 for r in all_runs]
    gen_times = [r.get('generation_time', 0) for r in all_runs if 'generation_time' in r]
    compile_times = [r.get('compile_time', 0) for r in all_runs if 'compile_time' in r]
    sim_times = [r.get('simulation_time', 0) for r in all_runs if 'simulation_time' in r]
    iterations = [r.get('iteration_count', 1) for r in all_runs]
    entropies = [r.get('confidence_entropy', 0) for r in all_runs if r.get('confidence_entropy') is not None]
    
    stats = {
        'n_runs': len(all_runs),
        'syntax_valid_rate': statistics.mean(syntax_vals) if syntax_vals else 0,
        'simulation_pass_rate': statistics.mean(sim_vals) if sim_vals else 0,
        'avg_generation_time': statistics.mean(gen_times) if gen_times else 0,
        'avg_compile_time': statistics.mean(compile_times) if compile_times else 0,
        'avg_simulation_time': statistics.mean(sim_times) if sim_times else 0,
        'avg_iterations': statistics.mean(iterations) if iterations else 1,
        'avg_entropy': statistics.mean(entropies) if entropies else None,
    }
    
    # Add standard deviations
    if len(all_runs) > 1:
        try:
            if len(set(syntax_vals)) > 1:
                stats['syntax_valid_std'] = statistics.stdev(syntax_vals)
        except:
            pass
        try:
            if len(set(sim_vals)) > 1:
                stats['simulation_pass_std'] = statistics.stdev(sim_vals)
        except:
            pass
        try:
            if len(set(gen_times)) > 1 and gen_times:
                stats['generation_time_std'] = statistics.stdev(gen_times)
        except:
            pass
        try:
            if len(set(iterations)) > 1:
                stats['iteration_std'] = statistics.stdev(iterations)
        except:
            pass
    
    # Test case statistics
    test_passed = [r.get('test_cases_passed', 0) for r in all_runs]
    test_total = [r.get('test_cases_total', 0) for r in all_runs]
    if any(test_total):
        stats['avg_tests_passed'] = statistics.mean(test_passed)
        stats['avg_tests_total'] = statistics.mean(test_total)
    
    return stats


def main():
    print("=" * 70)
    print("PHASE 4: SEMANTIC-AWARE ITERATIVE REFINEMENT")
    print("=" * 70)
    
    # Load configuration
    config = Phase4Config()
    print(f"\n📊 Configuration:")
    print(f"  • Repetitions per prompt: {REPETITIONS_PER_PROMPT}")
    print(f"  • Temperature: {TEMPERATURE}")
    print(f"  • Max iterations: {config.MAX_ITERATIONS}")
    print(f"  • Adaptive stopping: {config.ADAPTIVE_STOPPING}")
    print(f"  • Waveform analysis: {config.ENABLE_WAVEFORM_ANALYSIS}")
    print(f"  • Formal verification: {config.ENABLE_FORMAL_VERIFICATION}")
    print(f"  • AST repair: {config.ENABLE_AST_REPAIR}")
    print(f"  • Confidence tracking: {config.CONFIDENCE_TRACKING}")
    print(f"  • Mode: {config.MODE}")
    print(f"  • Task tiers enabled: {config.ENABLE_TASK_TIERS}")
    print(f"  • Entropy gating: {config.ENABLE_ENTROPY_GATING} (threshold={config.ENTROPY_THRESHOLD})")
    print(f"  • Generation cache: {config.ENABLE_GENERATION_CACHE}")
    print(f"  • Task max runtime: {config.TASK_MAX_RUNTIME_SECONDS}s")
    
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
        starcoder2 = OllamaInterface("starcoder2:7b")
        models.append(("StarCoder2-7B-Medium", starcoder2))
        print("  ✓ StarCoder2 7B (Medium tier) ready")
    except Exception as e:
        print(f"  ⚠ StarCoder2 7B not available: {e}")
    
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
    
    # Initialize Phase 4 components
    print("\n🔧 Initializing Phase 4 components...")
    compiler = HDLCompiler()
    simulator = HDLSimulator()
    
    waveform_analyzer = WaveformAnalyzer(config.ENABLE_WAVEFORM_ANALYSIS) if config.ENABLE_WAVEFORM_ANALYSIS else None
    formal_verifier = FormalVerifier(config.ENABLE_FORMAL_VERIFICATION) if config.ENABLE_FORMAL_VERIFICATION else None
    ast_repair = ASTRepair(config.ENABLE_AST_REPAIR) if config.ENABLE_AST_REPAIR else None
    
    semantic_repair = SemanticRepair(
        enable_waveform=config.ENABLE_WAVEFORM_ANALYSIS,
        enable_formal=config.ENABLE_FORMAL_VERIFICATION,
        enable_ast=config.ENABLE_AST_REPAIR
    ) if config.ENABLE_SEMANTIC_REPAIR else None
    
    confidence_tracker = ConfidenceTracker(config.CONFIDENCE_SAMPLES) if config.CONFIDENCE_TRACKING else None
    feedback_generator = FeedbackGenerator(config.MAX_FEEDBACK_LENGTH)
    
    print("  ✓ All components initialized")
    
    # Setup output (configurable via environment variable)
    output_dir_name = os.getenv("BENCHMARK_OUTPUT_DIR", "Benchmark_9_Results")
    output_dir = Path(__file__).parent.parent / "results" / output_dir_name
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n📊 Saving to: {output_dir}")
    
    pipeline = BenchmarkPipeline(output_dir)
    
    # Use full task list
    test_tasks = tasks
    total_tasks = len(test_tasks)
    
    print("\n" + "=" * 70)
    print("RUNNING PHASE 4 BENCHMARK")
    print("=" * 70)
    print("\nFeatures:")
    print("  ✓ Semantic-aware post-processing (waveform diff, formal verification, AST repair)")
    print("  ✓ Adaptive iterative refinement loop")
    print("  ✓ Confidence modeling (entropy tracking)")
    print("  ✓ Feedback-driven generation")
    print(f"  ✓ Multiple repetitions ({REPETITIONS_PER_PROMPT} per task) for statistical significance")
    print(f"\nTesting {total_tasks} tasks × {len(models)} models × {REPETITIONS_PER_PROMPT} repetitions\n")
    
    # Store all results
    all_results = []
    task_statistics = {}
    
    for model_name, model in models:
        print(f"\n{'='*70}")
        print(f"MODEL: {model_name}")
        print(f"{'='*70}")
        
        for i, task in enumerate(test_tasks, 1):
            print(f"\n[{i}/{total_tasks}] {task.task_id}")
            print(f"  Category: {task.category}")
            
            # Determine evaluation settings for this task
            eval_settings = get_eval_settings_for_task(task, config)
            tier = eval_settings["tier"]
            max_iterations = eval_settings["max_iterations"]
            enable_waveform = eval_settings["enable_waveform"]
            enable_formal = eval_settings["enable_formal"]
            
            print(
                f"  Running {REPETITIONS_PER_PROMPT} repetitions "
                f"(tier={tier}, max_iters={max_iterations}, "
                f"waveform={'on' if enable_waveform else 'off'}, "
                f"formal={'on' if enable_formal else 'off'})"
            )
            
            # Get module name for post-processing
            module_name = extract_module_name(task.task_id)
            
            # Store all runs for this task
            task_runs = []
            
            for rep in range(REPETITIONS_PER_PROMPT):
                try:
                    # Create iterative evaluator for this run
                    evaluator = IterativeEvaluator(
                        config=config,
                        compiler=compiler,
                        simulator=simulator,
                        semantic_repair=semantic_repair,
                        confidence_tracker=confidence_tracker,
                        feedback_generator=feedback_generator,
                        waveform_analyzer=waveform_analyzer,
                        formal_verifier=formal_verifier,
                    )
                    
                    # Run iterative evaluation
                    task_dir = output_dir / f"{model_name.replace('-', '_')}_{task.task_id}"
                    task_dir.mkdir(exist_ok=True)
                    rep_dir = task_dir / f"rep{rep+1}"
                    rep_dir.mkdir(exist_ok=True)
                    
                    # Create post-processing function with module name
                    def post_process(code):
                        return post_process_verilog(code, module_name)
                    
                    best_metrics, iteration_history = evaluator.evaluate_with_refinement(
                        task=task,
                        model=model,
                        output_dir=rep_dir,
                        post_process_func=post_process,
                        max_iterations=max_iterations,
                        enable_waveform=enable_waveform,
                        enable_formal=enable_formal,
                        tier=tier,
                    )
                    
                    # Save iteration history
                    history_file = rep_dir / "iteration_history.json"
                    with open(history_file, 'w') as f:
                        json.dump([
                            {
                                "attempt": h["attempt"],
                                "score": h["score"],
                                "syntax_valid": h["metrics"].syntax_valid,
                                "simulation_passed": h["metrics"].simulation_passed,
                                "feedback": h["feedback"][:200]  # Truncate for storage
                            }
                            for h in iteration_history
                        ], f, indent=2)
                    
                    # Store result
                    run_result = {
                        'task_id': task.task_id,
                        'model_name': model_name,
                        'repetition': rep + 1,
                        'syntax_valid': best_metrics.syntax_valid,
                        'compile_errors': best_metrics.compile_errors,
                        'simulation_passed': best_metrics.simulation_passed,
                        'test_cases_passed': best_metrics.test_cases_passed,
                        'test_cases_total': best_metrics.test_cases_total,
                        'generation_time': best_metrics.generation_time,
                        'compile_time': best_metrics.compile_time,
                        'simulation_time': best_metrics.simulation_time,
                        'iteration_count': best_metrics.iteration_count,
                        'confidence_entropy': best_metrics.confidence_entropy,
                        'confidence_log_prob': best_metrics.confidence_log_prob,
                        'waveform_diff_summary': best_metrics.waveform_diff_summary,
                        'formal_equiv_status': best_metrics.formal_equiv_status,
                        'semantic_repair_applied': best_metrics.semantic_repair_applied,
                        'fast_skip_reason': best_metrics.fast_skip_reason,
                    }
                    task_runs.append(run_result)
                    all_results.append(run_result)
                    
                    # Print status
                    status = "✓" if best_metrics.syntax_valid else "✗"
                    sim_status = "✓" if best_metrics.simulation_passed else "✗"
                    print(f"    Rep {rep+1}: {status} Syntax, {sim_status} Sim ({best_metrics.test_cases_passed}/{best_metrics.test_cases_total})")
                    print(f"      Iterations: {best_metrics.iteration_count}, Entropy: {best_metrics.confidence_entropy:.3f}" if best_metrics.confidence_entropy else f"      Iterations: {best_metrics.iteration_count}")
                    
                except Exception as e:
                    print(f"    Rep {rep+1}: ✗ Error: {e}")
                    import traceback
                    traceback.print_exc()
                    run_result = {
                        'task_id': task.task_id,
                        'model_name': model_name,
                        'repetition': rep + 1,
                        'syntax_valid': False,
                        'simulation_passed': False,
                        'error': str(e),
                        'iteration_count': 1
                    }
                    task_runs.append(run_result)
                    all_results.append(run_result)
            
            # Compute statistics for this task
            task_key = f"{model_name}_{task.task_id}"
            task_statistics[task_key] = compute_statistics(task_runs)
            
            # Print summary
            stats = task_statistics[task_key]
            print(f"\n  📊 Task Statistics ({REPETITIONS_PER_PROMPT} runs):")
            print(f"    Syntax valid: {stats['syntax_valid_rate']:.1%}", end="")
            if 'syntax_valid_std' in stats:
                print(f" (σ={stats['syntax_valid_std']:.3f})")
            else:
                print()
            print(f"    Simulation pass: {stats['simulation_pass_rate']:.1%}", end="")
            if 'simulation_pass_std' in stats:
                print(f" (σ={stats['simulation_pass_std']:.3f})")
            else:
                print()
            print(f"    Avg iterations: {stats['avg_iterations']:.2f}")
            if stats.get('avg_entropy'):
                print(f"    Avg entropy: {stats['avg_entropy']:.3f}")
    
    # Save results
    print("\n" + "="*70)
    print("SAVING RESULTS")
    print("="*70)
    
    # Save individual run results
    individual_results_file = output_dir / "individual_runs.json"
    with open(individual_results_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"✓ Individual run results: {individual_results_file}")
    print(f"  Total runs: {len(all_results)} ({total_tasks} tasks × {len(models)} models × {REPETITIONS_PER_PROMPT} reps)")
    
    # Save task statistics
    statistics_file = output_dir / "task_statistics.json"
    with open(statistics_file, 'w') as f:
        json.dump(task_statistics, f, indent=2)
    print(f"✓ Task statistics: {statistics_file}")
    
    # Compute model-level statistics
    model_stats = {}
    for model_name, _ in models:
        model_runs = [r for r in all_results if r['model_name'] == model_name]
        model_stats[model_name] = compute_statistics(model_runs)
    
    model_stats_file = output_dir / "model_statistics.json"
    with open(model_stats_file, 'w') as f:
        json.dump(model_stats, f, indent=2)
    print(f"✓ Model statistics: {model_stats_file}")
    
    # Print summary
    print("\n" + "="*70)
    print("AGGREGATED BENCHMARK SUMMARY")
    print("="*70)
    
    for model_name, _ in models:
        stats = model_stats[model_name]
        print(f"\nModel: {model_name}")
        print("-" * 70)
        print(f"  Total runs: {stats['n_runs']}")
        print(f"  Syntax valid rate: {stats['syntax_valid_rate']:.1%}", end="")
        if 'syntax_valid_std' in stats:
            print(f" (σ={stats['syntax_valid_std']:.3f})")
        else:
            print()
        print(f"  Simulation pass rate: {stats['simulation_pass_rate']:.1%}", end="")
        if 'simulation_pass_std' in stats:
            print(f" (σ={stats['simulation_pass_std']:.3f})")
        else:
            print()
        print(f"  Avg iterations: {stats['avg_iterations']:.2f}", end="")
        if 'iteration_std' in stats:
            print(f" (σ={stats['iteration_std']:.3f})")
        else:
            print()
        if stats.get('avg_entropy'):
            print(f"  Avg entropy: {stats['avg_entropy']:.3f}")
        print(f"  Avg generation time: {stats['avg_generation_time']:.3f}s", end="")
        if 'generation_time_std' in stats:
            print(f" (σ={stats['generation_time_std']:.3f}s)")
        else:
            print()
    
    # Confidence correlation analysis
    if confidence_tracker:
        correlation_stats = confidence_tracker.get_correlation_stats()
        if correlation_stats:
            print(f"\n📈 Confidence Correlation:")
            for key, value in correlation_stats.items():
                print(f"  {key}: {value:.3f}")
    
    print(f"\n✓ Phase 4 complete!")
    print(f"\nResults saved:")
    print(f"  • Individual runs: {individual_results_file}")
    print(f"  • Task statistics: {statistics_file}")
    print(f"  • Model statistics: {model_stats_file}")


if __name__ == "__main__":
    main()

