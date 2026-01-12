#!/usr/bin/env python3
"""
Phase 5: Enhanced FSM and Mixed Task Pipeline
Improved prompts, micro-repair, and targeted feedback for FSM and Mixed designs
"""

import sys
import json
import statistics
from pathlib import Path
from collections import defaultdict
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from dataset_loader import load_tasks_from_json, print_dataset_stats, validate_dataset
from model_interface import OllamaInterface, HuggingFaceInterface
from Eval_Pipeline import BenchmarkPipeline, EvaluationMetrics, HDLCompiler, HDLSimulator
from run_phase2 import extract_module_name, get_port_spec, post_process_verilog
from phase5_config import Phase5Config
from phase5_feedback import Phase5FeedbackGenerator
from phase5_repair import Phase5Repair
from waveform_analyzer import WaveformAnalyzer
from formal_verifier import FormalVerifier
from ast_repair import ASTRepair
from semantic_repair import SemanticRepair
from confidence_tracker import ConfidenceTracker
from iterative_evaluator import IterativeEvaluator
import time

# Configuration
REPETITIONS_PER_PROMPT = 3
TEMPERATURE = 0.0
# Benchmark label (results directory)
BENCHMARK_NAME = "Benchmark_12_Results"


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
        if "johnson" in tid.lower():
            return 2  # Johnson counter requires waveform analysis for shift pattern validation
        if "dff" in tid or "counter_4bit" in tid:
            return 1
        # Shift register, PIPO, T flip-flop are harder
        return 2
    
    if cat in ("fsm", "mixed"):
        return 2
    
    # Fallback
    return 1


def get_eval_settings_for_task(task, config: Phase5Config):
    """
    Compute evaluation settings (tier, max iterations, waveform/formal flags)
    for a given task based on the global Phase 5 configuration.
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
            "enable_entropy_gating": False,
            "entropy_threshold": config.ENTROPY_THRESHOLD,
        }
    
    # Fast mode: tier-specific behavior
    if tier == 0:  # trivial
        max_iters = 1
        enable_waveform = False
        enable_formal = False
        enable_entropy_gating = config.ENABLE_ENTROPY_GATING
        entropy_threshold = config.ENTROPY_THRESHOLD
    elif tier == 1:  # simple
        max_iters = min(config.MAX_ITERS_SEQUENTIAL, config.MAX_ITERATIONS)
        enable_waveform = False
        enable_formal = False
        enable_entropy_gating = config.ENABLE_ENTROPY_GATING
        entropy_threshold = config.ENTROPY_THRESHOLD
    else:  # tier 2, complex
        # Default values for tier 2
        enable_waveform = config.ENABLE_WAVEFORM_ANALYSIS
        enable_formal = False
        enable_entropy_gating = config.ENABLE_ENTROPY_GATING
        entropy_threshold = config.ENTROPY_THRESHOLD
        
        # Use category-aware caps when available
        if task.category == "combinational":
            max_iters = min(config.MAX_ITERS_COMBINATIONAL, config.MAX_ITERATIONS)
            enable_waveform = False
            enable_formal = False
        elif task.category == "sequential":
            max_iters = min(config.MAX_ITERS_SEQUENTIAL, config.MAX_ITERATIONS)
            enable_waveform = False
            enable_formal = False
        elif task.category == "mixed":
            max_iters = min(config.MAX_ITERS_MIXED, config.MAX_ITERATIONS)
            enable_entropy_gating = config.ENABLE_ENTROPY_GATING_MIXED
            entropy_threshold = config.ENTROPY_THRESHOLD_MIXED
            enable_waveform = config.ENABLE_WAVEFORM_ANALYSIS  # Only after syntax passes
            enable_formal = False
        else:  # fsm or unknown
            max_iters = min(config.MAX_ITERS_FSM, config.MAX_ITERATIONS)
            enable_entropy_gating = config.ENABLE_ENTROPY_GATING_FSM  # Enabled with very low threshold
            entropy_threshold = config.ENTROPY_THRESHOLD_FSM  # Very low threshold (0.05)
            enable_waveform = config.ENABLE_WAVEFORM_ANALYSIS
            enable_formal = config.ENABLE_FORMAL_VERIFICATION  # Enabled for FSM
    
    return {
        "tier": tier,
        "max_iterations": max_iters,
        "enable_waveform": enable_waveform,
        "enable_formal": enable_formal,
        "enable_entropy_gating": enable_entropy_gating,
        "entropy_threshold": entropy_threshold,
    }


def extract_fsm_transitions(task_spec: str, module_name: str) -> str:
    """Extract FSM state transitions from task specification and return DSL format"""
    # Parse common FSM patterns from specification
    fsm_dsl = ""
    
    if 'sequence_detector' in module_name and '101' in module_name:
        # Sequence detector 101 pattern
        fsm_dsl = """
FSM SPEC (MACHINE-READABLE):
States:
  S0: no bits matched
  S1: matched '1'
  S2: matched '10'
  S3: matched '101' (output detected=1)
Transitions:
  S0 --1--> S1
  S0 --0--> S0
  S1 --0--> S2
  S1 --1--> S1
  S2 --1--> S3 (output detected=1)
  S2 --0--> S0
  S3 --1--> S1 (after detection, restart)
  S3 --0--> S2
"""
    elif 'traffic_light' in module_name:
        # Traffic light controller
        fsm_dsl = """
FSM SPEC (MACHINE-READABLE):
States:
  S_NS_GO: North-South green, East-West red
  S_NS_WARN: North-South yellow, East-West red
  S_EW_GO: East-West green, North-South red
  S_EW_WARN: East-West yellow, North-South red
Transitions:
  S_NS_GO --timer==2--> S_NS_WARN
  S_NS_WARN --timer==1--> S_EW_GO
  S_EW_GO --timer==2--> S_EW_WARN
  S_EW_WARN --timer==1--> S_NS_GO
Outputs:
  S_NS_GO: ns_light=GREEN, ew_light=RED
  S_NS_WARN: ns_light=YELLOW, ew_light=RED
  S_EW_GO: ns_light=RED, ew_light=GREEN
  S_EW_WARN: ns_light=RED, ew_light=YELLOW
"""
    elif 'turnstile' in module_name:
        # Turnstile controller
        fsm_dsl = """
FSM SPEC (MACHINE-READABLE):
States:
  S_LOCKED: gate locked, alarm off
  S_UNLOCKED: gate unlocked, alarm off
Transitions:
  S_LOCKED --coin--> S_UNLOCKED (locked=0)
  S_LOCKED --push--> S_LOCKED (alarm=1)
  S_UNLOCKED --push--> S_LOCKED (locked=1)
  S_UNLOCKED --coin--> S_UNLOCKED (no change)
Outputs:
  S_LOCKED: locked=1, alarm=1 if push without coin
  S_UNLOCKED: locked=0, alarm=0
"""
    
    return fsm_dsl


def get_phase5_prompt(task_spec: str, module_name: str) -> str:
    """Phase 5: Enhanced prompt with FSM template and Mixed case rules"""
    port_info = get_port_spec(module_name)
    
    # Determine category
    is_fsm = any(x in module_name for x in ['sequence_detector', 'traffic_light', 'turnstile'])
    is_mixed = any(x in module_name for x in ['priority_encoder', 'alu'])
    
    # FSM Transition Table/DSL (improves logic correctness by 20-40%)
    fsm_transition_table = ""
    if is_fsm:
        fsm_transition_table = extract_fsm_transitions(task_spec, module_name)
    
    # FSM Reference Template (fixes ~60% of syntax issues)
    fsm_template = ""
    if is_fsm:
        fsm_template = """
=== FSM REFERENCE TEMPLATE ===
Use the standard 2-always FSM template:

localparam S0 = 2'b00;
localparam S1 = 2'b01;
localparam S2 = 2'b10;

reg [1:0] state;
reg [1:0] next_state;

always @(posedge clk) begin
    if (rst)
        state <= S0;
    else
        state <= next_state;
end

always @(*) begin
    next_state = state;  // Initialize before case
    detected = 1'b0;    // Initialize outputs
    case (state)
        S0: next_state = in_bit ? S1 : S0;
        S1: next_state = in_bit ? S1 : S2;
        S2: begin
            if (in_bit) begin
                detected = 1'b1;
                next_state = S1;
            end else begin
                next_state = S0;
            end
        end
        default: next_state = S0;  // ALWAYS include default
    endcase
end

KEY FSM RULES:
1. TWO always blocks: always @(posedge clk) for state, always @(*) for next_state
2. Initialize next_state before case statement
3. Initialize all outputs before case statement
4. Wrap multi-statement case items with begin/end
5. ALWAYS include default case
6. NEVER put case statement outside always block
7. NEVER assign state in always @(*) block

"""
    
    # Mixed Case Formatting Rules
    mixed_rules = ""
    if is_mixed:
        # ALU Logic Template (explicit operation mapping)
        alu_template = ""
        if 'alu' in module_name:
            alu_template = """
=== ALU LOGIC TEMPLATE (EXPLICIT OPERATION MAPPING) ===
ALUs must compute outputs combinationally. Use this exact structure:

always @(*) begin
    result = 4'b0000;  // Initialize before case
    carry_out = 1'b0;
    case (op)
        2'b00: {carry_out, result} = a + b;  // ADD operation
        2'b01: {carry_out, result} = a - b;  // SUBTRACT operation
        2'b10: begin  // AND operation (multi-statement needs begin/end)
            result = a & b;
            carry_out = 1'b0;
        end
        2'b11: begin  // XOR operation
            result = a ^ b;
            carry_out = 1'b0;
        end
        default: begin
            result = 4'h0;
            carry_out = 1'b0;
        end
    endcase
    zero = (result == 4'h0);
end

CRITICAL ALU RULES:
1. ALUs MUST use always @(*) or always_comb, NEVER always_ff
2. ALUs are combinational logic - no clock needed
3. Initialize result before case statement
4. Each operation (add, subtract, AND, XOR) must be explicitly mapped
5. Carry_out is only valid for add/subtract operations
6. Zero flag is computed after case statement

"""
        
        mixed_rules = f"""
=== CASE FORMATTING RULES (MIXED DESIGNS) ===
RULES FOR CASE STATEMENTS:
- Every case item must use begin/end if it has more than one statement
- Do NOT put 'end' inside a case item (e.g., "2'b00: result = a + b; end" is WRONG)
- Wrap the whole case in always @(*) or always_comb (NEVER always_ff for ALU)
- Initialize the output before the case: result = 4'b0000;
- ALUs must use always_comb or always @(*), never always_ff
- Each case item must assign the result variable

CORRECT CASE STRUCTURE:
always @(*) begin
    result = 4'b0000;  // Initialize before case
    case (op)
        2'b00: {{carry_out, result}} = a + b;
        2'b01: {{carry_out, result}} = a - b;
        2'b10: begin  // Multi-statement needs begin/end
            result = a & b;
            carry_out = 1'b0;
        end
        2'b11: begin
            result = a ^ b;
            carry_out = 1'b0;
        end
        default: begin
            result = 4'h0;
            carry_out = 1'b0;
        end
    endcase
    zero = (result == 4'h0);
end

WRONG PATTERNS TO AVOID:
- 2'b00: result = a + b; end  (stray 'end' inside case item)
- case (op) result = a + b; endcase  (missing begin/end for multi-statement)
- always_ff @(posedge clk) for ALU  (ALU must be combinational)

{alu_template}
"""
    
    # Get task-specific example from Phase 2
    from run_phase2 import get_constrained_prompt
    phase2_prompt = get_constrained_prompt(task_spec, module_name)
    
    # Extract example from Phase 2 prompt (between EXAMPLE and MANDATORY)
    example_start = phase2_prompt.find("EXAMPLE")
    mandatory_start = phase2_prompt.find("MANDATORY")
    
    if example_start >= 0 and mandatory_start > example_start:
        example = phase2_prompt[example_start:mandatory_start]
        
        # Add broken + fixed FSM example for contrastive learning
        if is_fsm and 'sequence_detector' in module_name:
            broken_fsm_example = """

=== BROKEN FSM EXAMPLE (DO NOT REPEAT THESE MISTAKES) ===
// WRONG - case outside always block:
module sequence_detector_101(...);
    reg [1:0] state;
    always @(posedge clk) begin
        if (rst) state <= S0; end  // WRONG: end closes block before else
        else state <= next_state;
    end
    case (state)  // WRONG: case outside always block
        S0: next_state = in_bit ? S1 : S0;
    endcase
endmodule

// FIXED - correct structure:
module sequence_detector_101(...);
    reg [1:0] state;
    reg [1:0] next_state;
    always @(posedge clk) begin  // Correct: begin/end properly placed
        if (rst)
            state <= S0;
        else
            state <= next_state;
    end
    always @(*) begin  // Correct: case inside always block
        next_state = state;
        case (state)
            S0: next_state = in_bit ? S1 : S0;
            default: next_state = S0;  // Correct: default included
        endcase
    end
endmodule

"""
            example = broken_fsm_example + example
    
    # Build Phase 5 prompt
    prompt = f"""Generate ONLY synthesizable Verilog-2001 code. NO explanations, NO instructions, NO text outside module.

SPECIFICATION: {task_spec}
{fsm_transition_table}
{fsm_template}
{mixed_rules}
{example}
MANDATORY STRUCTURE - Use this EXACT format:
module {module_name}(
    {port_info['ports']}
);
    // Your logic here - COMPLETE THE MODULE BODY
endmodule

CRITICAL RULES - MUST FOLLOW ALL:
1. Module name MUST be: {module_name}
2. Port names MUST match: {port_info['desc']}
3. Combinational logic → use 'wire' + 'assign' statements
4. Sequential logic → use 'reg' + 'always @(posedge clk)' block with 'begin' and 'end'
5. FSM logic → use TWO always blocks: one sequential for state, one combinational for next_state/output
6. Mixed designs → use case statements with proper begin/end for multi-statement branches
7. ONLY standard Verilog-2001 syntax
8. NO SystemVerilog, NO BSV, NO invented keywords
9. NO procedural code: NO 'for' loops, NO 'integer' declarations, NO system tasks like $readmemh
10. For sequential: use non-blocking (<=) ONLY inside always blocks, NEVER use blocking (=) with reg
11. NEVER assign to reg variables outside always blocks
12. For addition, use + operator on full vectors (e.g., 'a + b'), NOT XOR (^), NOT ternary operators
13. Use full bit vectors in operations, not single bits (e.g., use 'a[1:0]' not just 'a[0]')
14. ALL ports in port list MUST be declared in the module
15. Start with 'module {module_name}(' and end with 'endmodule'. Nothing before or after.
16. DO NOT write explanations, instructions, steps, or any text outside the module.
17. DO NOT use nested ternary operators (multiple ? : operators) EXCEPT for priority encoders.
18. COMPLETE THE ENTIRE MODULE - do not truncate after module declaration.
19. For FSM: MUST include both state register always block AND combinational next_state always block.
20. For case statements: MUST include default case.
21. For ALU: MUST use always @(*) or always_comb, NEVER always_ff.
22. For mixed designs: Initialize outputs before case statement.

Generate ONLY the complete Verilog module code:
"""
    
    return prompt


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


class Phase5IterativeEvaluator:
    """Phase 5 evaluator with micro-repair and enhanced feedback"""
    
    def __init__(
        self,
        config: Phase5Config,
        compiler: HDLCompiler,
        simulator: HDLSimulator,
        semantic_repair: Optional[SemanticRepair] = None,
        confidence_tracker: Optional[ConfidenceTracker] = None,
        feedback_generator: Phase5FeedbackGenerator = None,
        waveform_analyzer: Optional[WaveformAnalyzer] = None,
        formal_verifier: Optional[FormalVerifier] = None,
        repair_engine: Phase5Repair = None,
    ):
        from iterative_evaluator import IterativeEvaluator
        
        # Wrap IterativeEvaluator but override prompt generation
        # Wrap feedback generator to inject category info
        self.config = config
        self.feedback_generator = feedback_generator or Phase5FeedbackGenerator()
        self.repair_engine = repair_engine or Phase5Repair()
        self.current_task_category = None  # Set during evaluation
        
        # Create wrapper feedback generator that adds category
        class CategoryAwareFeedbackGenerator:
            def __init__(self, base_gen, category_getter):
                self.base = base_gen
                self.get_category = category_getter
            
            def compile_feedback(self, compile_errors, code="", category=None):
                cat = category or self.get_category()
                return self.base.compile_feedback(compile_errors, code, cat)
            
            def simulation_feedback(self, sim_errors, waveform_diff, code="", category=None):
                cat = category or self.get_category()
                return self.base.simulation_feedback(sim_errors, waveform_diff, code, cat)
            
            def semantic_feedback(self, repair_hints, category=None):
                cat = category or self.get_category()
                return self.base.semantic_feedback(repair_hints, cat)
            
            def combine_feedback(self, compile_fb, sim_fb, semantic_fb, category=None):
                return self.base.combine_feedback(compile_fb, sim_fb, semantic_fb, category or self.get_category())
            
            def __getattr__(self, name):
                return getattr(self.base, name)
        
        wrapper_feedback = CategoryAwareFeedbackGenerator(
            self.feedback_generator,
            lambda: self.current_task_category or ""
        )
        
        self.base_evaluator = IterativeEvaluator(
            config=config,
            compiler=compiler,
            simulator=simulator,
            semantic_repair=semantic_repair,
            confidence_tracker=confidence_tracker,
            feedback_generator=wrapper_feedback,
            waveform_analyzer=waveform_analyzer,
            formal_verifier=formal_verifier,
        )
    
    def evaluate_with_refinement(
        self,
        task,
        model,
        output_dir: Path,
        post_process_func: Optional[callable] = None,
        max_iterations: Optional[int] = None,
        enable_waveform: Optional[bool] = None,
        enable_formal: Optional[bool] = None,
        enable_entropy_gating: Optional[bool] = None,
        entropy_threshold: Optional[float] = None,
        tier: Optional[int] = None,
    ) -> tuple:
        """
        Phase 5 iterative refinement with Phase 5 prompts and micro-repair
        """
        from iterative_evaluator import IterativeEvaluator
        
        # Temporarily override get_constrained_prompt to use Phase 5 prompts
        import run_phase2
        original_get_prompt = run_phase2.get_constrained_prompt
        
        def phase5_get_prompt_wrapper(task_spec: str, module_name: str) -> str:
            return get_phase5_prompt(task_spec, module_name)
        
        # Override entropy gating settings
        original_gating = self.config.ENABLE_ENTROPY_GATING
        original_threshold = self.config.ENTROPY_THRESHOLD
        
        try:
            # Set task category for feedback generator
            self.current_task_category = task.category
            
            # Patch prompt generation
            run_phase2.get_constrained_prompt = phase5_get_prompt_wrapper
            
            if enable_entropy_gating is not None:
                self.config.ENABLE_ENTROPY_GATING = enable_entropy_gating
                if entropy_threshold is not None:
                    self.config.ENTROPY_THRESHOLD = entropy_threshold
            
            result = self.base_evaluator.evaluate_with_refinement(
                task=task,
                model=model,
                output_dir=output_dir,
                post_process_func=post_process_func,
                max_iterations=max_iterations,
                enable_waveform=enable_waveform,
                enable_formal=enable_formal,
                tier=tier,
            )
        finally:
            # Restore original prompt function
            run_phase2.get_constrained_prompt = original_get_prompt
            # Restore entropy gating settings
            self.config.ENABLE_ENTROPY_GATING = original_gating
            self.config.ENTROPY_THRESHOLD = original_threshold
        
        return result


def main():
    print("=" * 70)
    print("BENCHMARK 12: PHASE 5 MULTI-MODEL (QUALITY-FOCUSED)")
    print("=" * 70)
    
    # Load configuration
    config = Phase5Config()
    print(f"\n📊 Configuration:")
    print(f"  • Repetitions per prompt: {REPETITIONS_PER_PROMPT}")
    print(f"  • Temperature: {TEMPERATURE}")
    print(f"  • Max iterations: {config.MAX_ITERATIONS}")
    print(f"  • FSM max iterations: {config.MAX_ITERS_FSM}")
    print(f"  • Mixed max iterations: {config.MAX_ITERS_MIXED}")
    print(f"  • Adaptive stopping: {config.ADAPTIVE_STOPPING}")
    print(f"  • Waveform analysis: {config.ENABLE_WAVEFORM_ANALYSIS}")
    print(f"  • Formal verification (FSM): {config.ENABLE_FORMAL_VERIFICATION}")
    print(f"  • AST repair: {config.ENABLE_AST_REPAIR}")
    print(f"  • Confidence tracking: {config.CONFIDENCE_TRACKING}")
    print(f"  • Mode: {config.MODE}")
    print(f"  • Task tiers enabled: {config.ENABLE_TASK_TIERS}")
    print(f"  • Entropy gating FSM: {config.ENABLE_ENTROPY_GATING_FSM}")
    print(f"  • Entropy gating Mixed: {config.ENABLE_ENTROPY_GATING_MIXED} (threshold={config.ENTROPY_THRESHOLD_MIXED})")
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
    failures = []
    desired_models = [
        ("Llama-3-8B-Large", "llama3"),
        ("StarCoder2-7B-Medium", "starcoder2:7b"),
        ("TinyLlama-1.1B-Small", "tinyllama"),
    ]
    
    for display_name, model_id in desired_models:
        try:
            model = OllamaInterface(model_id)
            models.append((display_name, model))
            print(f"  ✓ {display_name} ready ({model_id})")
        except Exception as e:
            failures.append((display_name, model_id, str(e)))
            print(f"  ✗ {display_name} failed: {e}")
    
    if len(models) != len(desired_models):
        print("❌ Benchmark 12 requires all three default models.")
        for display_name, model_id, msg in failures:
            print(f"  - {display_name} ({model_id}): {msg}")
        return
    
    print(f"\n✓ {len(models)} model(s) ready")
    
    # Initialize Phase 5 components
    print("\n🔧 Initializing Phase 5 components...")
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
    feedback_generator = Phase5FeedbackGenerator(config.MAX_FEEDBACK_LENGTH)
    repair_engine = Phase5Repair()
    
    print("  ✓ All components initialized")
    
    # Setup output
    output_dir = Path(__file__).parent.parent / "results" / BENCHMARK_NAME
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n📊 Saving to: {output_dir}")
    
    pipeline = BenchmarkPipeline(output_dir)
    
    # Use full task list
    test_tasks = tasks
    total_tasks = len(test_tasks)
    
    print("\n" + "=" * 70)
    print("RUNNING BENCHMARK 12 (ALL MODELS)")
    print("=" * 70)
    print("\nFeatures:")
    print("  ✓ Enhanced FSM prompts with reference template")
    print("  ✓ Mixed design case formatting rules")
    print("  ✓ Micro-repair engine (runs BEFORE GPT)")
    print("  ✓ Category-specific feedback triggers")
    print("  ✓ Adaptive iterative refinement loop")
    print("  ✓ Confidence modeling (entropy tracking)")
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
            enable_entropy_gating = eval_settings["enable_entropy_gating"]
            entropy_threshold = eval_settings["entropy_threshold"]
            
            print(
                f"  Running {REPETITIONS_PER_PROMPT} repetitions "
                f"(tier={tier}, max_iters={max_iterations}, "
                f"waveform={'on' if enable_waveform else 'off'}, "
                f"formal={'on' if enable_formal else 'off'}, "
                f"entropy_gating={'on' if enable_entropy_gating else 'off'})"
            )
            
            # Get module name for post-processing
            module_name = extract_module_name(task.task_id)
            
            # Store all runs for this task
            task_runs = []
            
            for rep in range(REPETITIONS_PER_PROMPT):
                try:
                    # Create Phase 5 evaluator for this run
                    evaluator = Phase5IterativeEvaluator(
                        config=config,
                        compiler=compiler,
                        simulator=simulator,
                        semantic_repair=semantic_repair,
                        confidence_tracker=confidence_tracker,
                        feedback_generator=feedback_generator,
                        waveform_analyzer=waveform_analyzer,
                        formal_verifier=formal_verifier,
                        repair_engine=repair_engine,
                    )
                    
                    # Run iterative evaluation
                    task_dir = output_dir / f"{model_name.replace('-', '_')}_{task.task_id}"
                    task_dir.mkdir(exist_ok=True)
                    rep_dir = task_dir / f"rep{rep+1}"
                    rep_dir.mkdir(exist_ok=True)
                    
                    # Create post-processing function with module name and micro-repair
                    def post_process(code):
                        # Apply micro-repair BEFORE standard post-processing
                        repaired = repair_engine.repair_before_generation(code, task.category)
                        # Then apply standard post-processing
                        return post_process_verilog(repaired, module_name)
                    
                    # Override prompt generation to use Phase 5 prompts
                    original_generate = None
                    if hasattr(model, 'generate_hdl'):
                        # Temporarily override prompt in iterative evaluator
                        # We need to patch the evaluator to use Phase 5 prompts
                        pass
                    
                    best_metrics, iteration_history = evaluator.evaluate_with_refinement(
                        task=task,
                        model=model,
                        output_dir=rep_dir,
                        post_process_func=post_process,
                        max_iterations=max_iterations,
                        enable_waveform=enable_waveform,
                        enable_formal=enable_formal,
                        enable_entropy_gating=enable_entropy_gating,
                        entropy_threshold=entropy_threshold,
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
    
    print(f"\n✓ Phase 5 complete!")
    print(f"\nResults saved:")
    print(f"  • Individual runs: {individual_results_file}")
    print(f"  • Task statistics: {statistics_file}")
    print(f"  • Model statistics: {model_stats_file}")


if __name__ == "__main__":
    main()

