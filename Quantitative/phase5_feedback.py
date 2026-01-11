"""
Phase 5 Enhanced Feedback Generator
Specialized feedback for FSM and Mixed designs with specific error pattern detection
"""

from typing import List, Dict, Optional
from phase5_repair import Phase5Repair


class Phase5FeedbackGenerator:
    """Enhanced feedback generator with FSM/mixed-specific triggers"""
    
    def __init__(self, max_length: int = 500):
        self.max_length = max_length
        self.repair_engine = Phase5Repair()
    
    def compile_feedback(self, compile_errors: List[str], code: str = "", category: str = "") -> str:
        """
        Convert compiler errors to prompt feedback with category-specific analysis
        
        Args:
            compile_errors: List of compilation error messages
            code: Generated code for pattern detection
            category: Task category ('fsm', 'mixed', etc.)
            
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
        
        # Add category-specific feedback based on detected issues - TOP 3 TRIGGERS ONLY
        # Try to detect issues from compile errors if code not available
        if category == 'fsm':
            if code:
                fsm_issues = self.repair_engine.detect_fsm_issues(code)
                # Filter to top 3 high-impact issues
                top_issues = [issue for issue in fsm_issues if issue in [
                    "case_outside_always", "next_state_in_always_ff", "missing_begin_end_case"
                ]][:3]
                if top_issues:
                    feedback += "\n--- FSM-Specific Issues Detected:\n"
                    for issue in top_issues:
                        feedback += f"- {self._get_fsm_feedback_message(issue)}\n"
            else:
                # Detect from compile errors - top 3 triggers only
                error_text = ' '.join(compile_errors).lower()
                if 'case' in error_text and 'always' not in error_text:
                    feedback += "\n--- FSM Issue Detected:\n- Case statement appears outside always block. Move it into always_comb block.\n"
                if 'next_state' in error_text and 'always_ff' in error_text:
                    feedback += "\n--- FSM Issue Detected:\n- next_state should only be assigned in always_comb, not in always_ff. Move next_state logic to always_comb.\n"
                if 'unexpected' in error_text and 'case' in error_text:
                    feedback += "\n--- FSM Issue Detected:\n- Multi-statement case branches missing begin/end. Wrap each multi-statement branch with begin/end.\n"
        
        elif category == 'mixed':
            if code:
                mixed_issues = self.repair_engine.detect_mixed_issues(code)
                # Filter to top 3 high-impact issues
                top_issues = [issue for issue in mixed_issues if issue in [
                    "stray_end_in_case_item", "missing_begin_end_case", "missing_default_assignment"
                ]][:3]
                if top_issues:
                    feedback += "\n--- Mixed Design Issues Detected:\n"
                    for issue in top_issues:
                        feedback += f"- {self._get_mixed_feedback_message(issue)}\n"
            else:
                # Detect from compile errors - top 3 triggers only
                error_text = ' '.join(compile_errors).lower()
                if "unexpected 'end'" in error_text or "unexpected end" in error_text:
                    feedback += "\n--- Mixed Design Issue Detected:\n- Stray 'end' in case item. Remove 'end' from case item, use begin/end for multi-statement branches.\n"
                if 'case' in error_text and ('unexpected' in error_text or 'missing' in error_text):
                    feedback += "\n--- Mixed Design Issue Detected:\n- Multi-statement case branches without begin/end. Wrap each multi-statement branch with begin/end.\n"
                if 'alu' in error_text.lower() and ('result' in error_text or 'output' in error_text):
                    feedback += "\n--- Mixed Design Issue Detected:\n- Initialize output before case statement: 'result = 4'b0000;' and include default case.\n"
        
        feedback += "\nPlease fix these errors in your Verilog code."
        return feedback[:self.max_length]
    
    def _get_fsm_feedback_message(self, issue: str) -> str:
        """Get specific feedback message for FSM issues - TOP 3 HIGH-IMPACT TRIGGERS"""
        messages = {
            # Top 3 high-impact triggers
            "case_outside_always": "Your FSM's case statement is outside an always block. Move it into always_comb block.",
            "next_state_in_always_ff": "next_state should only be assigned in always_comb, not in always_ff. Move next_state logic to always_comb block.",
            "missing_begin_end_case": "Your case statement has multi-statement branches missing begin/end. Wrap each multi-statement case branch with begin/end.",
        }
        return messages.get(issue, f"FSM issue detected: {issue}")
    
    def _get_mixed_feedback_message(self, issue: str) -> str:
        """Get specific feedback message for Mixed design issues - TOP 3 HIGH-IMPACT TRIGGERS"""
        messages = {
            # Top 3 high-impact triggers
            "stray_end_in_case_item": "You have a stray 'end' inside a case item. Remove the 'end' from the case item. Use begin/end for multi-statement branches.",
            "missing_begin_end_case": "Your case statement has multi-statement branches without begin/end. Wrap each multi-statement branch with begin/end.",
            "missing_default_assignment": "Initialize your output before the case statement: 'result = 4'b0000;' and include a default case that assigns a default value.",
        }
        return messages.get(issue, f"Mixed design issue detected: {issue}")
    
    def simulation_feedback(
        self,
        sim_errors: Optional[List[str]],
        waveform_diff: Optional[Dict],
        code: str = "",
        category: str = ""
    ) -> str:
        """
        Generate feedback from simulation mismatches with category-specific analysis
        
        Args:
            sim_errors: Simulation error messages
            waveform_diff: Waveform comparison results
            code: Generated code for pattern detection
            category: Task category
            
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
        
        # Add category-specific feedback
        if category == 'fsm' and code:
            feedback_parts.append("\n--- FSM Logic Check:\n")
            feedback_parts.append("Verify state transitions are correct in always_comb block.\n")
            feedback_parts.append("Ensure next_state logic matches the state machine specification.\n")
            feedback_parts.append("Check that detected/output signals are set at the correct states.\n")
        
        elif category == 'mixed' and code:
            feedback_parts.append("\n--- Mixed Design Logic Check:\n")
            if 'alu' in code.lower():
                feedback_parts.append("For ALU: Verify each operation (add, subtract, AND, XOR) is correctly implemented.\n")
                feedback_parts.append("Check that carry_out and zero flags are computed correctly.\n")
            
        feedback = "".join(feedback_parts)
        return feedback[:self.max_length] if feedback else ""
    
    def semantic_feedback(self, repair_hints: List[str], category: str = "") -> str:
        """
        Convert semantic repair hints to natural language with category context
        
        Args:
            repair_hints: List of repair suggestions
            category: Task category
            
        Returns:
            Formatted feedback string
        """
        if not repair_hints:
            return ""
        
        feedback = "Semantic analysis suggests:\n"
        for i, hint in enumerate(repair_hints[:5], 1):
            feedback += f"{i}. {hint}\n"
        
        # Add category-specific suggestions
        if category == 'fsm':
            feedback += "\n--- FSM Structure Reminder:\n"
            feedback += "Use TWO always blocks:\n"
            feedback += "1. always_ff @(posedge clk) for state <= next_state;\n"
            feedback += "2. always_comb for next_state logic with case statement.\n"
            feedback += "Include default case in every case statement.\n"
        
        elif category == 'mixed':
            feedback += "\n--- Mixed Design Reminder:\n"
            feedback += "Use always_comb (never always_ff) for ALU operations.\n"
            feedback += "Initialize outputs before case statement.\n"
            feedback += "Wrap multi-statement case items with begin/end.\n"
        
        feedback += "\nPlease address these issues in your design."
        return feedback[:self.max_length]
    
    def combine_feedback(
        self,
        compile_fb: str = "",
        sim_fb: str = "",
        semantic_fb: str = "",
        category: str = ""
    ) -> str:
        """
        Merge all feedback into coherent prompt enhancement
        
        Args:
            compile_fb: Compilation feedback
            sim_fb: Simulation feedback
            semantic_fb: Semantic feedback
            category: Task category
            
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

