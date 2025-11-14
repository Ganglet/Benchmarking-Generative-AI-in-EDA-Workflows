"""
Semantic Repair Engine
Orchestrates waveform diff, formal verification, and AST analysis to generate repair hints
"""

from typing import Dict, List, Optional, Any
from pathlib import Path

from waveform_analyzer import WaveformAnalyzer
from formal_verifier import FormalVerifier
from ast_repair import ASTRepair


class SemanticRepair:
    """Orchestrates semantic analysis and repair"""
    
    def __init__(
        self,
        enable_waveform: bool = True,
        enable_formal: bool = False,
        enable_ast: bool = True
    ):
        self.waveform_analyzer = WaveformAnalyzer(enable_waveform) if enable_waveform else None
        self.formal_verifier = FormalVerifier(enable_formal) if enable_formal else None
        self.ast_repair = ASTRepair(enable_ast) if enable_ast else None
    
    def analyze_failure(
        self,
        compile_errors: List[str],
        sim_errors: Optional[List[str]],
        waveform_diff: Optional[Dict],
        equiv_report: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Aggregate all failure signals into unified analysis
        
        Args:
            compile_errors: Compilation error messages
            sim_errors: Simulation error messages
            waveform_diff: Waveform comparison results
            equiv_report: Formal verification report
            
        Returns:
            Dictionary with aggregated analysis
        """
        analysis = {
            "compile_errors": compile_errors,
            "sim_errors": sim_errors or [],
            "waveform_mismatches": waveform_diff or {},
            "formal_status": equiv_report or {},
            "severity": "unknown",
            "primary_issue": None
        }
        
        # Determine severity and primary issue
        if compile_errors:
            analysis["severity"] = "syntax"
            analysis["primary_issue"] = "Compilation failed"
        elif sim_errors or waveform_diff:
            analysis["severity"] = "semantic"
            if waveform_diff:
                analysis["primary_issue"] = "Waveform mismatch detected"
            else:
                analysis["primary_issue"] = "Simulation failed"
        elif equiv_report and not equiv_report.get("equivalent", True):
            analysis["severity"] = "semantic"
            analysis["primary_issue"] = "Formal equivalence failed"
        else:
            analysis["severity"] = "unknown"
            analysis["primary_issue"] = "Unknown failure"
        
        return analysis
    
    def generate_repair_hints(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Convert analysis to specific repair suggestions
        
        Args:
            analysis: Output from analyze_failure()
            
        Returns:
            List of repair hints
        """
        hints = []
        
        # Compile error hints
        if analysis["compile_errors"]:
            for error in analysis["compile_errors"][:3]:
                if "port" in error.lower():
                    hints.append("Check port declarations match module interface")
                elif "syntax" in error.lower():
                    hints.append("Fix syntax error in code structure")
                elif "undefined" in error.lower():
                    hints.append("Declare missing signal or variable")
        
        # Waveform mismatch hints
        if analysis["waveform_mismatches"]:
            if self.waveform_analyzer:
                waveform_hints = self.waveform_analyzer.identify_logic_mismatches(
                    analysis["waveform_mismatches"]
                )
                hints.extend(waveform_hints)
        
        # Formal verification hints
        if analysis["formal_status"].get("status") == "counterexample":
            if self.formal_verifier:
                formal_hints = self.formal_verifier.suggest_fixes(analysis["formal_status"])
                hints.extend(formal_hints)
        
        # General semantic hints based on severity
        if analysis["severity"] == "semantic":
            hints.append("Review logic implementation for correctness")
            if not hints:
                hints.append("Check signal assignments and state transitions")
        
        return hints
    
    def apply_semantic_fix(
        self,
        code: str,
        hints: List[str],
        expected_module_name: str
    ) -> Optional[str]:
        """
        Execute repairs based on hints
        
        Args:
            code: Original code
            hints: Repair hints from generate_repair_hints()
            expected_module_name: Expected module name
            
        Returns:
            Repaired code, or None if repair cannot be applied
        """
        repaired_code = code
        
        # Apply fixes based on hint patterns
        for hint in hints:
            hint_lower = hint.lower()
            
            # Inverted signal
            if "inverted" in hint_lower or "invert" in hint_lower:
                # Try to find and invert enable/reset signals
                if "enable" in hint_lower or "en" in hint_lower:
                    repaired_code = self._invert_signal(repaired_code, ["en", "enable"])
                elif "reset" in hint_lower or "rst" in hint_lower:
                    repaired_code = self._invert_signal(repaired_code, ["rst", "reset"])
            
            # Missing state transition
            if "missing" in hint_lower and "transition" in hint_lower:
                # This would require more sophisticated analysis
                pass
            
            # Wrong initial value
            if "initial value" in hint_lower:
                # Try to fix reset values
                repaired_code = self._fix_reset_value(repaired_code)
            
            # Missing port
            if "port" in hint_lower:
                # AST repair would handle this better
                if self.ast_repair:
                    repaired_code = self.ast_repair.repair_with_ast(
                        repaired_code,
                        [hint]
                    ) or repaired_code
        
        return repaired_code if repaired_code != code else None
    
    def _invert_signal(self, code: str, signal_names: List[str]) -> str:
        """Invert a signal in the code"""
        for signal in signal_names:
            # Invert in conditions
            code = code.replace(f"if ({signal})", f"if (!{signal})")
            code = code.replace(f"if (!{signal})", f"if ({signal})")
            # Invert in assignments (more complex, would need AST)
        return code
    
    def _fix_reset_value(self, code: str) -> str:
        """Fix reset value assignments"""
        # Common fix: ensure reset sets to 0
        code = code.replace("q <= 1'b1;", "q <= 1'b0;")
        code = code.replace("count <= 4'b1111;", "count <= 4'b0000;")
        return code

