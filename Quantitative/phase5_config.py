"""
Phase 5 Configuration
Enhanced configuration for FSM and Mixed task improvement
"""


class Phase5Config:
    """Configuration for Phase 5 enhanced pipeline"""
    
    # Iterative Refinement
    MAX_ITERATIONS = 6
    ADAPTIVE_STOPPING = True
    MIN_IMPROVEMENT_THRESHOLD = 0.05  # Lower threshold to allow more refinement passes
    
    # Post-Processing Intelligence
    ENABLE_WAVEFORM_ANALYSIS = True
    ENABLE_FORMAL_VERIFICATION = True  # Enable for FSM and complex categories
    ENABLE_AST_REPAIR = True
    
    # Confidence Tracking
    CONFIDENCE_TRACKING = True
    CONFIDENCE_SAMPLES = 3  # Number of samples for entropy calculation
    
    # Semantic Repair
    ENABLE_SEMANTIC_REPAIR = True
    SEMANTIC_REPAIR_THRESHOLD = 0.5  # Minimum confidence to apply repair
    
    # Feedback Generation
    ENABLE_FEEDBACK_GENERATION = True
    MAX_FEEDBACK_LENGTH = 500  # Maximum characters in feedback
    
    # Timeouts
    WAVEFORM_ANALYSIS_TIMEOUT = 30
    FORMAL_VERIFICATION_TIMEOUT = 60
    AST_PARSING_TIMEOUT = 10
    
    # === Phase 5 scaling optimizations ===
    #
    # Global preset for how aggressively to apply fast-path optimizations.
    #  - "fast": enable all optimizations (tiers, entropy gating, caching, etc.)
    #  - "strict": run full pipeline with minimal shortcuts
    MODE = "strict"
    
    # Task tiering and per-tier iteration caps (effective only in fast mode)
    ENABLE_TASK_TIERS = True
    # Max iterations per logical category when tiering is enabled
    MAX_ITERS_COMBINATIONAL = 1
    MAX_ITERS_SEQUENTIAL = 3
    MAX_ITERS_MIXED = 6  # Increased to allow deeper ALU refinement
    MAX_ITERS_FSM = 7  # Give FSM designs another chance to converge
    
    # Entropy-based simulation gating
    ENABLE_ENTROPY_GATING = False
    ENTROPY_THRESHOLD = 0.3  # Default threshold (unused in strict mode)
    ENTROPY_THRESHOLD_MIXED = 0.20  # Lower threshold for mixed tasks
    ENTROPY_THRESHOLD_FSM = 0.05  # Very low threshold for FSM - skip messy generations but allow refinement
    # FSM/Mixed gating disabled in strict mode; thresholds kept for optional fast-mode use
    ENABLE_ENTROPY_GATING_FSM = False
    ENABLE_ENTROPY_GATING_MIXED = False
    
    # Generation caching
    ENABLE_GENERATION_CACHE = True
    
    # Per-task wall-clock timeout (seconds) for a single (task, model, repetition)
    TASK_MAX_RUNTIME_SECONDS = 90
    
    # Parallel evaluation (kept configurable for future use)
    ENABLE_PARALLEL_EVAL = False
    MAX_WORKERS = None  # If None, may default to num_cores // 2 when used

