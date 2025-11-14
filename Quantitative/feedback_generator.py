"""
Feedback Generation
Converts errors and repair hints into natural language feedback for model prompts
"""

from typing import List, Dict, Optional


class FeedbackGenerator:
    """Generates feedback from errors and analysis for iterative refinement"""
    
    def __init__(self, max_length: int = 500):
        self.max_length = max_length
    
    def compile_feedback(self, compile_errors: List[str]) -> str:
        """
        Convert compiler errors to prompt feedback
        
        Args:
            compile_errors: List of compilation error messages
            
        Returns:
            Formatted feedback string
        """
        if not compile_errors:
            return ""
        
        feedback = "Compilation errors found:\n"
        for i, error in enumerate(compile_errors[:5], 1):
            # Clean up error message
            clean_error = error.strip()
            if len(clean_error) > 100:
                clean_error = clean_error[:100] + "..."
            feedback += f"{i}. {clean_error}\n"
        
        feedback += "\nPlease fix these errors in your Verilog code."
        return feedback[:self.max_length]
    
    def simulation_feedback(
        self,
        sim_errors: Optional[List[str]],
        waveform_diff: Optional[Dict]
    ) -> str:
        """
        Generate feedback from simulation mismatches
        
        Args:
            sim_errors: Simulation error messages
            waveform_diff: Waveform comparison results
            
        Returns:
            Formatted feedback string
        """
        feedback_parts = []
        
        if sim_errors:
            feedback_parts.append("Simulation errors:\n")
            for error in sim_errors[:3]:
                feedback_parts.append(f"- {error}\n")
        
        if waveform_diff:
            feedback_parts.append("\nWaveform mismatches detected:\n")
            for signal, mismatches in list(waveform_diff.items())[:3]:
                feedback_parts.append(f"- Signal '{signal}' has {len(mismatches)} mismatch(es)\n")
            feedback_parts.append("\nPlease review the logic implementation.")
        
        feedback = "".join(feedback_parts)
        return feedback[:self.max_length] if feedback else ""
    
    def semantic_feedback(self, repair_hints: List[str]) -> str:
        """
        Convert semantic repair hints to natural language
        
        Args:
            repair_hints: List of repair suggestions
            
        Returns:
            Formatted feedback string
        """
        if not repair_hints:
            return ""
        
        feedback = "Semantic analysis suggests:\n"
        for i, hint in enumerate(repair_hints[:5], 1):
            feedback += f"{i}. {hint}\n"
        
        feedback += "\nPlease address these issues in your design."
        return feedback[:self.max_length]
    
    def combine_feedback(
        self,
        compile_fb: str = "",
        sim_fb: str = "",
        semantic_fb: str = ""
    ) -> str:
        """
        Merge all feedback into coherent prompt enhancement
        
        Args:
            compile_fb: Compilation feedback
            sim_fb: Simulation feedback
            semantic_fb: Semantic feedback
            
        Returns:
            Combined feedback string
        """
        feedback_parts = []
        
        if compile_fb:
            feedback_parts.append(compile_fb)
        
        if sim_fb:
            if feedback_parts:
                feedback_parts.append("\n---\n")
            feedback_parts.append(sim_fb)
        
        if semantic_fb:
            if feedback_parts:
                feedback_parts.append("\n---\n")
            feedback_parts.append(semantic_fb)
        
        combined = "\n".join(feedback_parts)
        
        # Truncate if too long
        if len(combined) > self.max_length:
            combined = combined[:self.max_length-3] + "..."
        
        return combined
    
    def generate_iteration_prompt(
        self,
        original_spec: str,
        feedback: str,
        attempt_number: int
    ) -> str:
        """
        Generate enhanced prompt with feedback for next iteration
        
        Args:
            original_spec: Original specification
            feedback: Combined feedback from previous attempt
            attempt_number: Current attempt number
            
        Returns:
            Enhanced prompt string
        """
        prompt = f"""Previous attempt ({attempt_number}) had issues. Please fix and regenerate.

Original Specification:
{original_spec}

Feedback from previous attempt:
{feedback}

Please generate corrected Verilog code that addresses all the issues mentioned above."""
        
        return prompt

