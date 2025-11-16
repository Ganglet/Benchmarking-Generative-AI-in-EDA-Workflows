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
        formal_verifier: Optional[FormalVerifier] = None,
    ):
        self.config = config
        self.compiler = compiler
        self.simulator = simulator
        self.semantic_repair = semantic_repair
        self.confidence_tracker = confidence_tracker
        self.feedback_generator = feedback_generator or FeedbackGenerator()
        self.waveform_analyzer = waveform_analyzer
        self.formal_verifier = formal_verifier
        # Simple in-memory cache for model generations (prompt-level)
        # Key: (model_name, task_id, tier, attempt, prompt_hash)
        # Value: (generated_code, gen_time)
        self.generation_cache: Dict[Tuple[str, str, int, int, str], Tuple[str, float]] = {}
    
    def evaluate_with_refinement(
        self,
        task: BenchmarkTask,
        model: Any,
        output_dir: Path,
        post_process_func: Optional[callable] = None,
        max_iterations: Optional[int] = None,
        enable_waveform: Optional[bool] = None,
        enable_formal: Optional[bool] = None,
        tier: Optional[int] = None,
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
        iteration_history: List[Dict] = []
        best_result = None
        best_score = -1
        start_time = time.time()
        
        # Resolve per-run configuration
        max_iters = max_iterations or self.config.MAX_ITERATIONS
        waveform_enabled = (
            self.config.ENABLE_WAVEFORM_ANALYSIS
            if enable_waveform is None
            else enable_waveform
        )
        formal_enabled = (
            self.config.ENABLE_FORMAL_VERIFICATION
            if enable_formal is None
            else enable_formal
        )
        task_tier = tier if tier is not None else 0
        
        original_spec = task.spec
        feedback = ""
        module_name = extract_module_name(task.task_id)
        
        for attempt in range(1, max_iters + 1):
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
            
            # Generate HDL (with optional caching)
            # For Phase 4, we pass the full prompt directly (Phase 2 style)
            # The model interface will still add its template, but the constrained prompt
            # from Phase 2 is more complete, so we pass it as specification
            model_name = getattr(model, "model_name", "unknown")
            prompt_key = prompt.encode("utf-8", errors="ignore")
            prompt_hash = str(hash(prompt_key))
            cache_key = (model_name, task.task_id, task_tier, attempt, prompt_hash)
            
            if self.config.ENABLE_GENERATION_CACHE and cache_key in self.generation_cache:
                generated_code, gen_time = self.generation_cache[cache_key]
            else:
                gen_start = time.time()
                if hasattr(model, "generate_hdl"):
                    try:
                        # Pass prompt as specification (model will add its own template)
                        generated_code, gen_time = model.generate_hdl(
                            prompt, temperature=0.0
                        )
                    except TypeError:
                        generated_code, gen_time = model.generate_hdl(prompt)
                else:
                    generated_code, gen_time = "", 0.0
                gen_time = time.time() - gen_start
                if self.config.ENABLE_GENERATION_CACHE:
                    self.generation_cache[cache_key] = (generated_code, gen_time)
            
            # Post-process if function provided
            if post_process_func:
                generated_code = post_process_func(generated_code)
            
            # Save generated code
            hdl_file = attempt_dir / f"{task.task_id}.v"
            hdl_file.write_text(generated_code)
            
            # Confidence tracking (computed before simulation to allow entropy gating)
            confidence_metrics: Dict[str, Any] = {}
            entropy = None
            if self.confidence_tracker and self.config.CONFIDENCE_TRACKING:
                generations = [generated_code]
                if self.config.CONFIDENCE_SAMPLES > 1:
                    # Use slightly higher temperature for sampling
                    for _ in range(self.config.CONFIDENCE_SAMPLES - 1):
                        try:
                            try:
                                sample_code, _ = model.generate_hdl(
                                    prompt, temperature=0.3
                                )
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
                    "log_prob": None,  # Would need model API support
                }
            
            # Compile
            compile_start = time.time()
            syntax_valid, compile_errors = self.compiler.compile(hdl_file, attempt_dir)
            compile_time = time.time() - compile_start
            
            # Decide whether to run simulation based on entropy gating
            fast_skip_reason: Optional[str] = None
            high_entropy = (
                entropy is not None
                and self.config.ENABLE_ENTROPY_GATING
                and entropy > self.config.ENTROPY_THRESHOLD
            )
            
            # Formal verification (optional – only when enabled and syntax is valid)
            equiv_report = None
            if (
                self.formal_verifier
                and formal_enabled
                and syntax_valid
            ):
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
            waveform_diff = None
            
            run_simulation = (
                syntax_valid
                and task.reference_tb
                and not high_entropy
            )
            if high_entropy:
                fast_skip_reason = "entropy_high"
            
            if run_simulation:
                sim_start = time.time()
                sim_passed, tests_passed, tests_total, vcd_path_result = (
                    self.simulator.simulate(
                        hdl_file,
                        Path(task.reference_tb),
                        attempt_dir,
                        generate_vcd=waveform_enabled,
                    )
                )
                sim_time = time.time() - sim_start
                
                # Compare waveforms if available
                if (
                    vcd_path_result
                    and self.waveform_analyzer
                    and task.reference_hdl
                    and waveform_enabled
                ):
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
                                waveform_diff = (
                                    self.waveform_analyzer.compare_waveforms(
                                        ref_vcd, gen_vcd
                                    )
                                )
            
            # Semantic analysis
            repair_hints: List[str] = []
            if self.semantic_repair:
                analysis = self.semantic_repair.analyze_failure(
                    compile_errors,
                    [] if sim_passed else ["Simulation failed"],
                    waveform_diff,
                    equiv_report,
                )
                repair_hints = self.semantic_repair.generate_repair_hints(analysis)
            
            # Correlate confidence with correctness if we have metrics
            if (
                self.confidence_tracker
                and self.config.CONFIDENCE_TRACKING
                and confidence_metrics
            ):
                self.confidence_tracker.correlate_with_correctness(
                    confidence_metrics,
                    syntax_valid and sim_passed,
                )
            # Create metrics
            metrics = EvaluationMetrics(
                task_id=task.task_id,
                model_name=model_name,
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
                confidence_log_prob=confidence_metrics.get("log_prob")
                if confidence_metrics
                else None,
                confidence_entropy=confidence_metrics.get("entropy")
                if confidence_metrics
                else None,
                waveform_diff_summary=str(waveform_diff) if waveform_diff else None,
                formal_equiv_status=equiv_report.get("status") if equiv_report else None,
                semantic_repair_applied=repair_hints,
                fast_skip_reason=fast_skip_reason,
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
            
            # Per-task wall-clock timeout
            if (
                self.config.TASK_MAX_RUNTIME_SECONDS
                and (time.time() - start_time) > self.config.TASK_MAX_RUNTIME_SECONDS
            ):
                if not fast_skip_reason:
                    metrics.fast_skip_reason = "timeout"
                break
            
            # Check if we should continue (respect adaptive stopping)
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

