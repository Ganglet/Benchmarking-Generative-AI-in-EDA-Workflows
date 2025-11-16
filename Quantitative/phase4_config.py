"""
Phase 4 Configuration
Configuration options for Semantic-Aware Iterative Refinement
"""


class Phase4Config:
    """Configuration for Phase 4 features"""
    
    # Iterative Refinement
    MAX_ITERATIONS = 5
    ADAPTIVE_STOPPING = True
    MIN_IMPROVEMENT_THRESHOLD = 0.1  # Minimum improvement to continue
    
    # Post-Processing Intelligence
    ENABLE_WAVEFORM_ANALYSIS = True
    ENABLE_FORMAL_VERIFICATION = False  # Optional, slower
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
    
    # === Phase 4 scaling optimizations ===
    #
    # Global preset for how aggressively to apply fast-path optimizations.
    #  - "fast": enable all optimizations (tiers, entropy gating, caching, etc.)
    #  - "strict": run full pipeline with minimal shortcuts
    MODE = "fast"
    
    # Task tiering and per-tier iteration caps (effective only in fast mode)
    ENABLE_TASK_TIERS = True
    # Max iterations per logical category when tiering is enabled
    MAX_ITERS_COMBINATIONAL = 1
    MAX_ITERS_SEQUENTIAL = 2
    MAX_ITERS_MIXED = 2
    MAX_ITERS_FSM = 4
    
    # Entropy-based simulation gating
    ENABLE_ENTROPY_GATING = True
    ENTROPY_THRESHOLD = 0.3  # If entropy > threshold, skip simulation for that attempt
    
    # Generation caching
    ENABLE_GENERATION_CACHE = True
    
    # Per-task wall-clock timeout (seconds) for a single (task, model, repetition)
    TASK_MAX_RUNTIME_SECONDS = 60
    
    # Parallel evaluation (kept configurable for future use)
    ENABLE_PARALLEL_EVAL = False
    MAX_WORKERS = None  # If None, may default to num_cores // 2 when used
    
