"""
Confidence Modeling
Tracks model confidence via log-probabilities and token entropy
"""

import time
from typing import List, Tuple, Optional, Dict
from difflib import SequenceMatcher


class ConfidenceTracker:
    """Tracks and computes confidence metrics for model generations"""
    
    def __init__(self, num_samples: int = 3):
        self.num_samples = num_samples
        self.confidence_history = []
    
    def compute_entropy(self, generations: List[str]) -> float:
        """
        Compute entropy as average edit distance between multiple generations
        
        Args:
            generations: List of generated code strings
            
        Returns:
            Entropy value (higher = more uncertain)
        """
        if len(generations) < 2:
            return 0.0
        
        edit_distances = []
        for i in range(len(generations)):
            for j in range(i + 1, len(generations)):
                # Compute normalized edit distance
                similarity = SequenceMatcher(None, generations[i], generations[j]).ratio()
                distance = 1.0 - similarity
                edit_distances.append(distance)
        
        if not edit_distances:
            return 0.0
        
        avg_distance = sum(edit_distances) / len(edit_distances)
        
        # Normalize by average length
        avg_length = sum(len(g) for g in generations) / len(generations)
        if avg_length > 0:
            normalized_entropy = avg_distance / (avg_length / 100)  # Scale to reasonable range
        else:
            normalized_entropy = avg_distance
        
        return min(normalized_entropy, 1.0)  # Cap at 1.0
    
    def compute_log_prob_summary(self, log_probs: Optional[List[float]]) -> Optional[Dict[str, float]]:
        """
        Aggregate token-level log probabilities
        
        Args:
            log_probs: List of log probabilities per token (if available)
            
        Returns:
            Dictionary with summary statistics, or None if not available
        """
        if log_probs is None or not log_probs:
            return None
        
        import statistics
        
        return {
            "mean": statistics.mean(log_probs),
            "median": statistics.median(log_probs),
            "min": min(log_probs),
            "max": max(log_probs),
            "std": statistics.stdev(log_probs) if len(log_probs) > 1 else 0.0
        }
    
    def correlate_with_correctness(
        self,
        confidence_metrics: Dict,
        success: bool
    ) -> Dict[str, any]:
        """
        Track correlation between confidence and correctness
        
        Args:
            confidence_metrics: Dictionary with confidence values
            success: Whether generation was correct
            
        Returns:
            Correlation data point
        """
        correlation_point = {
            "entropy": confidence_metrics.get("entropy"),
            "log_prob_mean": confidence_metrics.get("log_prob", {}).get("mean") if isinstance(confidence_metrics.get("log_prob"), dict) else None,
            "success": success,
            "timestamp": time.time()
        }
        
        self.confidence_history.append(correlation_point)
        return correlation_point
    
    def get_correlation_stats(self) -> Dict[str, float]:
        """
        Compute correlation statistics from history
        
        Returns:
            Dictionary with correlation coefficients
        """
        if len(self.confidence_history) < 2:
            return {}
        
        # Extract data
        entropies = [h["entropy"] for h in self.confidence_history if h["entropy"] is not None]
        successes = [1 if h["success"] else 0 for h in self.confidence_history]
        
        if not entropies or len(entropies) != len(successes):
            return {}
        
        # Compute correlation
        try:
            from scipy.stats import pearsonr
            correlation, p_value = pearsonr(entropies, successes)
            return {
                "entropy_success_correlation": correlation,
                "entropy_success_p_value": p_value
            }
        except ImportError:
            # Fallback: simple correlation
            if len(entropies) > 1:
                import statistics
                mean_entropy = statistics.mean(entropies)
                mean_success = statistics.mean(successes)
                
                # Simple correlation approximation
                covariance = sum((entropies[i] - mean_entropy) * (successes[i] - mean_success) 
                                for i in range(len(entropies))) / len(entropies)
                
                entropy_std = statistics.stdev(entropies) if len(entropies) > 1 else 1.0
                success_std = statistics.stdev(successes) if len(successes) > 1 else 1.0
                
                if entropy_std > 0 and success_std > 0:
                    correlation = covariance / (entropy_std * success_std)
                    return {"entropy_success_correlation": correlation}
            
            return {}

