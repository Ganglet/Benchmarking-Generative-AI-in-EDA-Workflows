"""
Adaptive Iterative Refinement Loop
Implements iterative evaluation with adaptive stopping logic
"""

from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
import time

from Eval_Pipeline import BenchmarkTask, EvaluationMetrics, HDLCompiler, HDLSimulator
from semantic_repair import SemanticRepair
from confidence_tracker import ConfidenceTracker
from feedback_generator import FeedbackGenerator
from waveform_analyzer import WaveformAnalyzer
from formal_verifier import FormalVerifier
from phase4_config import Phase4Config
from run_phase2 import extract_module_name, get_constrained_prompt


class IterativeEvaluator:
    """Evaluates tasks with iterative refinement and adaptive stopping"""
    
    def __init__(
        self,
        config: Phase4Config,
        compiler: HDLCompiler,
        simulator: HDLSimulator,
        semantic_repair: Optional[SemanticRepair] = None,
        confidence_tracker: Optional[ConfidenceTracker] = None,
        feedback_generator: Optional[FeedbackGenerator] = None,
        waveform_analyzer: Optional[WaveformAnalyzer] = None,
        formal_verifier: Optional[FormalVerifier] = None
    ):
        self.config = config
        self.compiler = compiler
        self.simulator = simulator
        self.semantic_repair = semantic_repair
        self.confidence_tracker = confidence_tracker
        self.feedback_generator = feedback_generator or FeedbackGenerator()
        self.waveform_analyzer = waveform_analyzer
        self.formal_verifier = formal_verifier
    
    def evaluate_with_refinement(
        self,
        task: BenchmarkTask,
        model: Any,
        output_dir: Path,
        post_process_func: Optional[callable] = None
    ) -> Tuple[EvaluationMetrics, List[Dict]]:
        """
        Main iterative refinement loop
        
        Args:
            task: Benchmark task to evaluate
            model: Model interface for generation
            output_dir: Directory for outputs
            post_process_func: Optional post-processing function
            
        Returns:
            Tuple of (best_metrics, iteration_history)
        """
        iteration_history = []
        best_result = None
        best_score = -1
        
        original_spec = task.spec
        feedback = ""
        module_name = extract_module_name(task.task_id)
        
        for attempt in range(1, self.config.MAX_ITERATIONS + 1):
            attempt_dir = output_dir / f"attempt_{attempt}"
            attempt_dir.mkdir(exist_ok=True)
            
            # Generate code with feedback
            if attempt == 1:
                # Use constrained prompt from Phase 2
                prompt = get_constrained_prompt(original_spec, module_name)
            else:
                # Add feedback to constrained prompt for iterative refinement
                base_prompt = get_constrained_prompt(original_spec, module_name)
                prompt = f"{base_prompt}\n\n---\nFEEDBACK FROM PREVIOUS ATTEMPT:\n{feedback}\n\nPlease address the issues above and regenerate the Verilog code."
            
            # Generate HDL
            # For Phase 4, we pass the full prompt directly (Phase 2 style)
            # The model interface will still add its template, but the constrained prompt
            # from Phase 2 is more complete, so we pass it as specification
            gen_start = time.time()
            if hasattr(model, 'generate_hdl'):
                try:
                    # Pass prompt as specification (model will add its own template)
                    generated_code, gen_time = model.generate_hdl(prompt, temperature=0.0)
                except TypeError:
                    generated_code, gen_time = model.generate_hdl(prompt)
            else:
                generated_code, gen_time = "", 0.0
            gen_time = time.time() - gen_start
            
            # Post-process if function provided
            if post_process_func:
                generated_code = post_process_func(generated_code)
            
            # Save generated code
            hdl_file = attempt_dir / f"{task.task_id}.v"
            hdl_file.write_text(generated_code)
            
            # Compile
            compile_start = time.time()
            syntax_valid, compile_errors = self.compiler.compile(hdl_file, attempt_dir)
            compile_time = time.time() - compile_start
            
            # Formal verification (optional)
            equiv_report = None
            if self.formal_verifier and self.config.ENABLE_FORMAL_VERIFICATION and syntax_valid:
                ref_hdl = Path(task.reference_hdl) if task.reference_hdl else None
                if ref_hdl and ref_hdl.exists():
                    equiv_report = self.formal_verifier.equiv_check(
                        ref_hdl, hdl_file, attempt_dir
                    )
            
            # Simulate
            sim_passed = False
            tests_passed = 0
            tests_total = 0
            sim_time = 0.0
            vcd_path = None
            waveform_diff = None
            
            if syntax_valid and task.reference_tb:
                sim_start = time.time()
                
                # Simulate with VCD generation if enabled
                sim_passed, tests_passed, tests_total, vcd_path_result = self.simulator.simulate(
                    hdl_file, Path(task.reference_tb), attempt_dir,
                    generate_vcd=self.config.ENABLE_WAVEFORM_ANALYSIS
                )
                sim_time = time.time() - sim_start
                
                # Compare waveforms if available
                waveform_diff = None
                if vcd_path_result and self.waveform_analyzer and task.reference_hdl:
                    # Generate reference VCD for comparison
                    ref_hdl = Path(task.reference_hdl)
                    ref_tb = Path(task.reference_tb)
                    ref_tb_with_vcd = attempt_dir / "ref_tb_with_vcd.v"
                    
                    if self.waveform_analyzer.inject_vcd_dump(ref_tb, ref_tb_with_vcd):
                        ref_vcd_path = self.waveform_analyzer.generate_vcd(
                            ref_tb_with_vcd, ref_hdl, attempt_dir
                        )
                        
                        if ref_vcd_path and ref_vcd_path.exists():
                            ref_vcd = self.waveform_analyzer.load_vcd(ref_vcd_path)
                            gen_vcd = self.waveform_analyzer.load_vcd(vcd_path_result)
                            if ref_vcd and gen_vcd:
                                waveform_diff = self.waveform_analyzer.compare_waveforms(
                                    ref_vcd, gen_vcd
                                )
            
            # Semantic analysis
            repair_hints = []
            if self.semantic_repair:
                analysis = self.semantic_repair.analyze_failure(
                    compile_errors,
                    [] if sim_passed else ["Simulation failed"],
                    waveform_diff,
                    equiv_report
                )
                repair_hints = self.semantic_repair.generate_repair_hints(analysis)
            
            # Confidence tracking
            confidence_metrics = {}
            if self.confidence_tracker and self.config.CONFIDENCE_TRACKING:
                # Generate multiple samples for entropy (if temperature > 0)
                generations = [generated_code]
                if self.config.CONFIDENCE_SAMPLES > 1:
                    # Use slightly higher temperature for sampling
                    for _ in range(self.config.CONFIDENCE_SAMPLES - 1):
                        try:
                            # Try with temperature parameter
                            try:
                                sample_code, _ = model.generate_hdl(prompt, temperature=0.3)
                            except TypeError:
                                sample_code, _ = model.generate_hdl(prompt)
                            if post_process_func:
                                sample_code = post_process_func(sample_code)
                            generations.append(sample_code)
                        except Exception:
                            # If sampling fails, just use the original
                            pass
                
                entropy = self.confidence_tracker.compute_entropy(generations)
                confidence_metrics = {
                    "entropy": entropy,
                    "log_prob": None  # Would need model API support
                }
                
                self.confidence_tracker.correlate_with_correctness(
                    confidence_metrics,
                    syntax_valid and sim_passed
                )
            
            # Create metrics
            metrics = EvaluationMetrics(
                task_id=task.task_id,
                model_name=getattr(model, 'model_name', 'unknown'),
                syntax_valid=syntax_valid,
                compile_errors=compile_errors,
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
                fault_detection_ratio=None,
                iteration_count=attempt,
                confidence_log_prob=confidence_metrics.get("log_prob"),
                confidence_entropy=confidence_metrics.get("entropy"),
                waveform_diff_summary=str(waveform_diff) if waveform_diff else None,
                formal_equiv_status=equiv_report.get("status") if equiv_report else None,
                semantic_repair_applied=repair_hints
            )
            
            # Score this attempt
            score = self._score_attempt(metrics)
            if score > best_score:
                best_score = score
                best_result = metrics
            
            iteration_history.append({
                "attempt": attempt,
                "metrics": metrics,
                "score": score,
                "feedback": feedback
            })
            
            # Generate feedback for next iteration
            if not (syntax_valid and sim_passed):
                compile_fb = self.feedback_generator.compile_feedback(compile_errors)
                sim_fb = self.feedback_generator.simulation_feedback(
                    [] if sim_passed else ["Tests failed"],
                    waveform_diff
                )
                semantic_fb = self.feedback_generator.semantic_feedback(repair_hints)
                feedback = self.feedback_generator.combine_feedback(
                    compile_fb, sim_fb, semantic_fb
                )
            
            # Check if we should continue
            if not self.should_continue(attempt, iteration_history):
                break
        
        return best_result or metrics, iteration_history
    
    def _score_attempt(self, metrics: EvaluationMetrics) -> float:
        """Score an attempt based on syntax, simulation, and confidence"""
        score = 0.0
        
        if metrics.syntax_valid:
            score += 1.0
        
        if metrics.simulation_passed:
            score += 2.0
            if metrics.test_cases_total > 0:
                score += (metrics.test_cases_passed / metrics.test_cases_total)
        
        # Confidence bonus (lower entropy = higher confidence = better)
        if metrics.confidence_entropy is not None:
            score += (1.0 - metrics.confidence_entropy) * 0.5
        
        return score
    
    def should_continue(
        self,
        attempt: int,
        results_history: List[Dict]
    ) -> bool:
        """
        Adaptive stopping logic
        
        Args:
            attempt: Current attempt number
            results_history: History of all attempts
            
        Returns:
            True if should continue, False if should stop
        """
        if not self.config.ADAPTIVE_STOPPING:
            return attempt < self.config.MAX_ITERATIONS
        
        # Stop if max attempts reached
        if attempt >= self.config.MAX_ITERATIONS:
            return False
        
        # Stop if current attempt succeeded
        if results_history:
            last_metrics = results_history[-1]["metrics"]
            if last_metrics.syntax_valid and last_metrics.simulation_passed:
                return False
        
        # Stop if no improvement in last 2 attempts
        if len(results_history) >= 2:
            last_two = results_history[-2:]
            scores = [r["score"] for r in last_two]
            
            if len(scores) == 2:
                improvement = scores[1] - scores[0]
                if improvement < self.config.MIN_IMPROVEMENT_THRESHOLD:
                    return False
        
        return True
    
    def select_best_result(
        self,
        results_history: List[Dict]
    ) -> Optional[EvaluationMetrics]:
        """
        Choose best result based on syntax, simulation, and confidence
        
        Args:
            results_history: History of all attempts
            
        Returns:
            Best EvaluationMetrics, or None if empty
        """
        if not results_history:
            return None
        
        # Sort by score (highest first)
        sorted_results = sorted(
            results_history,
            key=lambda x: x["score"],
            reverse=True
        )
        
        return sorted_results[0]["metrics"]

