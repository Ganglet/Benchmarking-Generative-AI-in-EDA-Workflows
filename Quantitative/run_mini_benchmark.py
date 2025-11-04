#!/usr/bin/env python3
"""
Mini Benchmark Runner - Quick test of the pipeline with real models
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dataset_loader import load_tasks_from_json, print_dataset_stats, validate_dataset
from model_interface import OllamaInterface, create_model_interface
from Eval_Pipeline import BenchmarkPipeline, EvaluationMetrics

def run_mini_benchmark():
    """
    Run a quick benchmark with available models and tasks
    """
    print("="*70)
    print("MINI BENCHMARK - Testing Pipeline with Real Models")
    print("="*70)
    
    # 1. Load dataset
    dataset_path = Path(__file__).parent / "dataset" / "tasks.json"
    print(f"\n📁 Loading tasks from: {dataset_path}")
    
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
        models.append(("Llama-3-8B", llama_model))
        print("  ✓ Llama3 ready")
    except Exception as e:
        print(f"  ⚠ Could not load Llama3: {e}")
    
    try:
        tiny_model = OllamaInterface("tinyllama")
        models.append(("TinyLlama-1.1B", tiny_model))
        print("  ✓ TinyLlama ready")
    except Exception as e:
        print(f"  ⚠ Could not load TinyLlama: {e}")
    
    if not models:
        print("\n✗ No models available!")
        print("\nTo use Ollama models:")
        print("  1. Install: curl -fsSL https://ollama.com/install.sh | sh")
        print("  2. Pull models:")
        print("     ollama pull llama3")
        print("     ollama pull tinyllama")
        print("  3. Run this script again")
        return
    
    print(f"\n✓ {len(models)} model(s) ready for benchmarking")
    
    # 3. Setup pipeline
    output_dir = Path(__file__).parent.parent / "results" / "mini_benchmark"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📊 Results will be saved to: {output_dir}")
    
    pipeline = BenchmarkPipeline(output_dir)
    
    # 4. Run benchmark
    print("\n" + "="*70)
    print("RUNNING BENCHMARK")
    print("="*70)
    
    # Limit to first few tasks for quick test
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
                # Wrapper to match expected interface
                class ModelWrapper:
                    def __init__(self, model, name):
                        self.model = model
                        self.model_name = name
                    
                    def generate_hdl(self, spec, context=None):
                        code, time_taken = self.model.generate_hdl(
                            spec, 
                            prompt_template="B",  # Use detailed template
                            temperature=0.0
                        )
                        return code, time_taken
                
                wrapper = ModelWrapper(model_interface, model_name)
                metrics = pipeline.evaluate_task(task, wrapper)
                
                # Print immediate results
                status_icon = "✓" if metrics.syntax_valid else "✗"
                print(f"  {status_icon} Syntax Valid: {metrics.syntax_valid}")
                
                if metrics.syntax_valid:
                    sim_icon = "✓" if metrics.simulation_passed else "✗"
                    print(f"  {sim_icon} Simulation: {metrics.test_cases_passed}/{metrics.test_cases_total} tests passed")
                
                print(f"  ⏱  Generation time: {metrics.generation_time:.2f}s")
                
                if metrics.compile_errors:
                    print(f"  ⚠  Errors: {len(metrics.compile_errors)}")
                
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
    
    print("\n✓ Mini benchmark complete!")
    print(f"\nResults saved to: {output_dir}")
    print(f"  - benchmark_results.json (detailed metrics)")
    print(f"  - Individual task outputs in subdirectories")


def main():
    """Main entry point"""
    print("\n🚀 Starting Mini Benchmark Runner\n")
    
    try:
        run_mini_benchmark()
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

