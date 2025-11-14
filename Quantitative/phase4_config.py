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

